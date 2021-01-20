from BaseModel import BaseModel
from peewee import *
import datetime

class DPU(BaseModel):
    name = TextField()
    memory = TextField()
    vcpu = TextField()
    createdOn = DateTimeField(default=datetime.datetime.now)
    modifiedOn = DateTimeField(default=datetime.datetime.now)

