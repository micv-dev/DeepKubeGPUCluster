import logging
import os
from flask import Flask

app = Flask(__name__)

class sshConfig:
    host = None
    port = 22
    user = None
    password = None
    ssh_pass_file = None
    passwordless = False

    def __init__(self, dummy):
        pass

    def __init__(self, ssh_host, ssh_user, ssh_pass, ssh_port=22, ssh_pass_file=None):

        self.host = ssh_host
        self.port = ssh_port
        self.user = ssh_user
        self.password = ssh_pass
        self.passwordless = False
        if ssh_pass_file is not None :
            ssh_pass_file = ssh_pass_file.strip()
            ssh_pass_file = ssh_pass_file.encode("utf8")
            self.ssh_pass_file = ssh_pass_file
            self.passwordless = True

    def getHost(self):
        return self.host

    def getPort(self):
        return self.port

    def getUser(self):
        return self.user

    def getPass(self):
        return self.password

    def getPassFile(self):
        return self.ssh_pass_file

    def isPasswordless(self):
        return self.passwordless



