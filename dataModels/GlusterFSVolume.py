from BaseModel import BaseModel
from peewee import *
import datetime


class GlusterFSVolume(BaseModel):
    pvcName=TextField()
    name = TextField(default="")
    size=IntegerField()
    createdOn = DateTimeField(default=datetime.datetime.now)
    modifiedOn = DateTimeField(default=datetime.datetime.now)

