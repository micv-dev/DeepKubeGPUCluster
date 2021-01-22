from configparser import ConfigParser


def getConfig():
    config = ConfigParser()
    config.read('config/app.config')
    return config