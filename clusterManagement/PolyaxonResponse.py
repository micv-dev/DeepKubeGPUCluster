import json

from Constants import *


class PolyaxonResponse:
    def __init__(self,name,webURL,webSockerPort,framework_type,framework_version,namespace_name,quota_info,
            volume_info,user_id,password):
       self.name=name,
       self.webURL=webURL
       self.webSockerPort=webSockerPort
       self.frameworkType=framework_type
       self.frameworkVersion=framework_version
       self.namespaceName=namespace_name
       self.quotaInfo=quota_info
       self.storageVolumeInfo=volume_info
       self.polyaxonUserId=user_id
       self.polyaxonPassword=password
       # self.dataSetVolumemountPointOnHost=DEFAULT_DATASET_MOUNT_PATH





