from peewee import *
import datetime

from dataModels.BaseModel import BaseModel


class DPU(BaseModel):
    name = TextField()
    memory = TextField()
    vcpu = TextField()
    createdOn = DateTimeField(default=datetime.datetime.now)
    modifiedOn = DateTimeField(default=datetime.datetime.now)

