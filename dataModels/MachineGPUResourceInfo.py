from peewee import *
import datetime
from dataModels.BaseModel import BaseModel
from dataModels.DPU import DPU
from dataModels.MachinePool import MachinePool


class MachineGPUResourceInfo(BaseModel):
    machinePool = ForeignKeyField(MachinePool)
    driverVersion=TextField()
    memory=TextField()
    dpuId = ForeignKeyField(DPU)
    dpuCount = IntegerField()
    allocatedDPUCount=IntegerField(default=0)
    createdOn = DateTimeField(default=datetime.datetime.now)
    modifiedOn = DateTimeField(default=datetime.datetime.now)

