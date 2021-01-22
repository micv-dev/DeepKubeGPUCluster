import logging

from flask import Flask, app
from fabric import Connection
from invoke.exceptions import UnexpectedExit, ParseError, Exit
from enum import Enum
from common.Logging import *
# app = Flask(__name__)
#
# logging.basicConfig(level=logging.DEBUG)
from common.remote_execution.SSHConf import sshConfig

app.log=get_log()
class RemoteOperations(Enum):
    CMD=1
    COPY=2

class ErrNo(Exception):
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return repr(self.value)

    def val(self):
        return self.value


class ReturnValue(object):
    def __init__(self, errCode, err, out):
        self.errCode = errCode
        self.errString = err
        self.outString = out

class RemoteExecuter:

    host = None
    hostUrl = None
    connectArgs = None
    conn = None
    sshConf = None

    def __init__(self, host, user, password):
        self.host = host
        self.user = user
        self.password = password
        self.sshConf = sshConfig(host, user, password)

        self.hostUrl = "{0}@{1}".format(self.sshConf.getUser(), self.sshConf.getHost())
        self.connectArgs = {"password": self.sshConf.getPass()}
        self.conn = Connection(host=self.hostUrl, port=self.sshConf.getPort(), connect_kwargs=self.connectArgs)


    def __init__(self, host, sshConf):
        self.host = host
        self.sshConf = sshConf
        app.logger.info("connection info: {0}@{1} identified by {2}. passwordless {3}".format(self.sshConf.getUser(),
                                                                            self.sshConf.getHost(),
                                                                            self.sshConf.getPass(),
                                                                            self.sshConf.isPasswordless()))

        self.hostUrl = "{0}@{1}".format(self.sshConf.getUser(), self.sshConf.getHost())
        if self.sshConf.isPasswordless() == True:
            self.connectArgs = {"key_filename": self.sshConf.getPassFile(),"look_for_keys":False,"allow_agent":False}
        else:
            self.connectArgs = {"password": self.sshConf.getPass()}

        self.conn = Connection(host=self.hostUrl, port=self.sshConf.getPort(), connect_kwargs=self.connectArgs)


    def refreshConn(self):
        self.conn.close()
        self.conn.open()

    def executeRemoteCommand(self, cmd):
        try:
            # cmd="sudo bash -c \"" + cmd + "\""
            app.logger.info("executing remote command: {0}".format(cmd))
            self.refreshConn()
            result = self.conn.run(cmd, hide=True)
            # result=self.conn.sudo(cmd,user="root",hide=True)
            #result = self.conn.sudo(cmd, hide=True, shell=False)

            return ReturnValue(result.exited, result.stderr, result.stdout)
        except (UnexpectedExit, Exit, ParseError) as e:
            if isinstance(e, ParseError):
                app.logger.error("Remote Executor:: Parser failed with error:" + str(e))
                return ReturnValue(1, e.stderr, "")
            if isinstance(e, Exit) and e.message:
                app.logger.error("Remote Executor:: Exited with error: " + str(e))
                return ReturnValue(e.code, e.stderr, "")
            if isinstance(e, UnexpectedExit) and e.result.hide:
                app.logger.error("Remote Executor:: Unexpected exit with error: " + str(e))
                return ReturnValue(1, "", "")
            else:
                app.logger.error("Remote Executor:: Exception : " + str(Exception) + " Err: " + str(e))
                return ReturnValue(e.result.exited, e.result.stderr.strip(), e.result.stdout.strip())

    def copyFileToRemote(self, sourcePath, destinationPath):
        try:
            #conn = Connection(host=self.hostUrl, connect_kwargs=self.connectArgs)
            app.logger.info("copying file to remote: {0}->{1}@{2}".format(sourcePath, self.host, destinationPath))

            self.refreshConn()
            result = self.conn.put(sourcePath, destinationPath, preserve_mode=True)

            #put() method doesnt return a fabric.runners.Result object like run() method.
            #it returns a fabric.transfer.Result which has no return info.
            #on failure it raises exception (oserror), no exception means it succeeded.
            return ReturnValue(0, "", "")
        except (UnexpectedExit, Exit, ParseError) as e:
            if isinstance(e, ParseError):
                app.logger.error("Remote Executor:: Parser failed with error:" + e)
                return ReturnValue(1, e.stderr, "")
            if isinstance(e, Exit) and e.message:
                app.logger.error("Remote Executor:: Exited with error: " + e)
                return ReturnValue(e.code, e.stderr, "")
            if isinstance(e, UnexpectedExit) and e.result.hide:
                return ReturnValue(1, "", "")
            else:
                app.logger.error("Remote Executor:: Exception : " + str(Exception) + " Err: " + str(e))
                return ReturnValue(e.result.exited, e.result.stderr.strip(), e.result.stdout.strip())

    def opsHandler(self, opList):
        # execute operations remotely one by one
        for cmd in opList:
            try:
                if cmd["operId"] == RemoteOperations.CMD:
                    self.executeRemoteCommand(cmd["args"][0])
                elif cmd["operId"] == RemoteOperations.COPY:
                    self.copyFileToRemote(cmd["args"][0], cmd["args"][1])
                else:
                    app.logger.error("remote operation {0} is not supported".format(cmd["operId"]))
                    raise Exception("remote operation {0} is not supported".format(cmd["operId"]))
            except Exception as ex:
                app.logger.error("operation {0} failed with exception {1}".format(str(cmd), str(ex)))

        return True


if __name__ == '__main__':
    rexec = RemoteExecuter("172.17.0.3", "root", "root123")

    print("cmd 1")
    rexec.executeRemoteCommand("sudo apt-get update")
    #print("cmd 2")
    #rexec.executeRemoteCommand("sudo apt-get install nginx")
    print("copy 1")
    rexec.copyFileToRemote(
        "/home/mukul/.bashrc",
        "/etc/mybashrc2")



