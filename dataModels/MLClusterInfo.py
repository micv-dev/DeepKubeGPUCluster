from BaseModel import BaseModel
from peewee import *
import datetime
from KubeCluster import KubeCluster
from DPU import DPU
from GlusterFSVolume import GlusterFSVolume
from dataModels.User import User


class MLClusterInfo(BaseModel):
    clusterId = ForeignKeyField(KubeCluster)
    userId=ForeignKeyField(User)
    type=TextField()
    namespace=TextField()
    quotaName=TextField()
    status=TextField()
    version=TextField()
    dpuType=TextField()
    dpuCount=IntegerField()
    glusterVolumeId=ForeignKeyField(GlusterFSVolume)
    createdOn = DateTimeField(default=datetime.datetime.now)
    modifiedOn = DateTimeField(default=datetime.datetime.now)