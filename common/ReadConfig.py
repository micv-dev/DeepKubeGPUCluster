import ConfigParser

def getConfig():
    config = ConfigParser.RawConfigParser()
    config.read('/root/PycharmProjects/Minerva/config/minereva.config')
    return config