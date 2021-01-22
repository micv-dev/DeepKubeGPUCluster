from peewee import *
import datetime

from dataModels.BaseModel import BaseModel
from dataModels.GlusterFSVolume import GlusterFSVolume
from dataModels.KubeCluster import KubeCluster
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