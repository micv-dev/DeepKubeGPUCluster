from BaseModel import BaseModel
from peewee import *
import datetime
from MachinePool import MachinePool
from dataModels.DPU import DPU


class MachineGPUResourceInfo(BaseModel):
    machinePool = ForeignKeyField(MachinePool)
    driverVersion=TextField()
    memory=TextField()
    dpuId = ForeignKeyField(DPU)
    dpuCount = IntegerField()
    allocatedDPUCount=IntegerField(default=0)
    createdOn = DateTimeField(default=datetime.datetime.now)
    modifiedOn = DateTimeField(default=datetime.datetime.now)

