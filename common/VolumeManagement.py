import time
import uuid
from pprint import pprint
from Constants import *
import kubernetes
from kubernetes.client import V1ObjectMeta, V1PersistentVolumeClaimSpec, V1ResourceRequirements, V1ResourceQuota, \
    V1ResourceQuotaSpec
from kubernetes.client.rest import ApiException
from common import Logging as log
from dataModels.GlusterFSVolume import GlusterFSVolume


def create_volume(master_machine, size,namespace,volume_name="gfvolume"):
    v1_api=master_machine.kube_api
    body = kubernetes.client.V1PersistentVolumeClaim()
    body.api_version = "v1"
    body.kind = "PersistentVolumeClaim"
    meta = V1ObjectMeta()
    # meta.name = volume_name
    meta.generate_name= volume_name
    spec = V1PersistentVolumeClaimSpec()
    spec.storage_class_name = "glusterfs"
    spec.access_modes = ["ReadWriteMany"]
    body.spec = spec
    resource = V1ResourceRequirements()
    resource.requests = {"storage": str(size)+"Gi"}
    spec.resources = resource
    body.metadata = meta
    api_response = v1_api.create_namespaced_persistent_volume_claim(namespace, body)
    pvc_name=api_response.metadata.name
    gfs=GlusterFSVolume(pvcName=pvc_name,size=size)
    gfs.save()
    return api_response.metadata.name,gfs

def get_vol_name(pvc_name,v1_api):
    vol_name=None
    pvs = v1_api.list_persistent_volume()
    for item in pvs.items:
        log.debug("pvc name is {0},pv item is {1}".format(pvc_name,item))
        if item.metadata.name.strip() == pvc_name.strip():
            log.debug("Matched pvc name is {0},pv item is {1}".format(pvc_name, item))
            vol_name=item.spec.glusterfs.path
            break
    if vol_name is None:
        raise Exception("Matching PV not found for %s" %(pvc_name))
    return vol_name

def check_pvc(master_machine, namespace, pvc, gfs):
    v1_api=master_machine.kube_api
    is_break=False
    vol_name=None
    for i in range(PVC_MAX_ITERATIONS):
        api_response = v1_api.list_namespaced_persistent_volume_claim(namespace)
        for item in api_response.items:
            if item.metadata.name == pvc:
                if item.status.phase == "Bound":
                    log.debug("Bound pvc name is {0},gfs is {1}".format(item, gfs))
                    vol_name=get_vol_name(item.spec.volume_name,v1_api)
                    gfs.name=vol_name
                    gfs.save()
                    is_break=True
                    break
        if is_break is True:
            break
        time.sleep(SLEEP_TIME)
    if is_break is False:
        raise Exception("Volume did not bind.Name is %s,%s" % (pvc, namespace))
    return vol_name

def create_resource_quota_namespaced(cluster_mgmt,namespace,noOfgpu):
    v1_api=cluster_mgmt.kube_api
    quota = V1ResourceQuota()
    quota.api_version = "v1"
    quota.kind = "ResourceQuota"
    meta = V1ObjectMeta()
    meta.generate_name = "quota"
    quota.metadata = meta
    quota_spec = V1ResourceQuotaSpec()
    hard = {"requests.nvidia.com/gpu": str(int(noOfgpu))}
    quota_spec.hard = hard
    quota.spec = quota_spec
    api_response = v1_api.create_namespaced_resource_quota(namespace, quota)
    return api_response.metadata.name


def create_namespace(cluster_mgmt,namespace,generate_name=True):
    namespace=namespace.lower()
    v1_api=cluster_mgmt.kube_api
    body = kubernetes.client.V1Namespace()
    meta = V1ObjectMeta()
    if generate_name is True:
        meta.generate_name=namespace
    else:
        meta.name=namespace
    body.metadata=meta
    api_response = v1_api.create_namespace(body)
    return api_response.metadata.name
