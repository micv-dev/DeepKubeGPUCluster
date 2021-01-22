from peewee import *
import datetime

from dataModels.BaseModel import BaseModel
from dataModels.User import User


class KubeCluster(BaseModel):
    userId = ForeignKeyField(User)
    name = TextField()
    status = TextField()
    startTime = TextField()
    endTime = TextField(default="")
    createdOn = DateTimeField(default=datetime.datetime.now())
    modifiedOn = DateTimeField(default=datetime.datetime.now())

