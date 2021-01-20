from uuid import uuid5, uuid4

import kubernetes
from kubernetes.client import V1Volume, V1PersistentVolumeClaimVolumeSource, V1ResourceRequirements, V1VolumeMount, \
    V1Container, V1PodSpec, V1ObjectMeta
from kubernetes.client.rest import ApiException

from clusterManagement.MLClusterBase import MLClusterBase
from common.MachineResource import *
from common.Utils import *
from dataModels.KubeCluster import KubeCluster
from common import Logging as log


class TensorflowCluster(MLClusterBase):
    def __init__(self):
      pass


    def create_cluster(self,spec,cluster_management,namespace_name,volume_claim_name):
        count=int(spec[FRAMEWORK_RESOURCES][FRAMEWORK_DPU_COUNT])
        version=str(spec[FRAMEWORK_VERSION])
        image="tensorflow/tensorflow:"+version+"-gpu"
        ###
        v1_api = cluster_management.kube_api
        api_response_list=[]
        for i in range(count):
            body = kubernetes.client.V1Pod()
            body.api_version = "v1"
            body.kind = "Pod"
            meta = V1ObjectMeta()
            meta.generate_name = "tensorflow-"
            body.metadata = meta
            uuid=str(uuid4())
            container = V1Container(name=uuid, image=image)
            pod_spec = V1PodSpec(containers=[container])
            container_mounts = V1VolumeMount(mount_path=GLUSTER_DEFAULT_MOUNT_PATH, name=CONTAINER_VOLUME_PREFIX)
            container.volume_mounts = [container_mounts]
            compute_resource = V1ResourceRequirements()
            compute_resource.limits = {"nvidia.com/gpu": 1}
            compute_resource.requests = {"nvidia.com/gpu": 1}
            container.resources = compute_resource
            claim = V1PersistentVolumeClaimVolumeSource(claim_name=volume_claim_name)
            volume_claim = V1Volume(name=CONTAINER_VOLUME_PREFIX, persistent_volume_claim=claim)
            volume_claim.persistent_volume_claim = claim
            pod_spec.volumes = [volume_claim]
            body.spec = pod_spec
            try:
                api_response = v1_api.create_namespaced_pod(namespace_name, body)
            except ApiException as e:
                raise Exception("Exception when calling CoreV1Api->create_namespaced_pod: %s\n" % e)
            api_response_list.append(api_response)
        return api_response_list


