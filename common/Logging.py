import logging as log
# import DbCon
from common import ReadConfig as config

config = config.getConfig()
log.basicConfig(filename=config.get("logging","fileName"), level=log.DEBUG,
                    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
log.debug("This is ")
def get_log():
    return log

def info(message):
    log.info(msg=message)

def debug(message):
    log.debug(msg=message)

def exception(exp,msg=None):
    if msg is not None:
        exp="Message is: "+ msg+"\n Stacktrace is : "+str(exp)
    log.error(exp, exc_info=True)



