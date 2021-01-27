from peewee import *
import datetime

from dataModels.BaseModel import BaseModel


class GlusterFSVolume(BaseModel):
    pvcName=TextField()
    name = TextField(default="")
    size=IntegerField()
    createdOn = DateTimeField(default=datetime.datetime.now)
    modifiedOn = DateTimeField(default=datetime.datetime.now)

