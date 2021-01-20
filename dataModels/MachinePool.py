from MySQLdb.constants.FIELD_TYPE import NULL

from BaseModel import BaseModel
from peewee import *
import datetime


class MachinePool(BaseModel):
    name = TextField()
    ipAddress = TextField()
    internalIpAddress=TextField()
    userId = TextField()
    password = TextField()
    sshFilePath=TextField(default=None)
    kubeVersion = TextField()
    role = TextField()
    clusterId=IntegerField(default=None)
    createdOn = DateTimeField(default=datetime.datetime.now)
    modifiedOn = DateTimeField(default=datetime.datetime.now)

