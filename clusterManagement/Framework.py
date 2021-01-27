from kubernetes.client import V1Service, V1ServiceSpec, V1ServicePort, V1Endpoints, V1EndpointAddress, V1EndpointPort, \
    V1EndpointSubset, V1GlusterfsPersistentVolumeSource, V1PersistentVolumeSpec

from Constants import *
from clusterManagement.ClusterManagement import ClusterManagement
from common import GetObject
from common.AppEnums import StackStatus
from common.Utils import mount_gf_volume, get_gfs_endpoint_name
from common.VolumeManagement import *
from common import Logging as log
from dataModels.KubeCluster import KubeCluster
from dataModels.MachinePool import MachinePool
from dataModels.MLClusterInfo import MLClusterInfo


class Framework:
    def __init__(self):
        self.framework_list=[]

    def add_framework(self,framework):
        self.framework_list.append(framework)

    def set_cluster_object(self,cluster_management):
        self.cluster_management=cluster_management

    def create_gluster_service(self,v1_api,namespace_name):
        service = V1Service()
        service.api_version = "v1"
        service.kind = "Service"
        meta = V1ObjectMeta()
        meta.generate_name = "gluster-service"
        service.metadata = meta
        service_spec = V1ServiceSpec()
        service_port = V1ServicePort(port=5)
        service_spec.ports = [service_port]
        service.spec = service_spec
        api_response = v1_api.create_namespaced_service(namespace=namespace_name, body=service)
        return api_response.metadata.name

    def create_gluster_endpoint(self,v1_api,namespace_name):
        endpoints = V1Endpoints()
        endpoints.api_version = "v1"
        endpoints.kind = "Endpoints"
        meta = V1ObjectMeta()
        meta.generate_name = "gluster-endpoint"
        endpoints.metadata = meta
        address = V1EndpointAddress(ip=DEFAULT_GLUSTER_SERVER)
        port = V1EndpointPort(port=5)
        subset = V1EndpointSubset(addresses=[address], ports=[port])
        endpoints.subsets = [subset]
        api_response = v1_api.create_namespaced_endpoints(namespace_name, endpoints)
        return api_response.metadata.name

    def create_pv_gluster_volume(self,v1_api,endpoint):
        body = kubernetes.client.V1PersistentVolume()
        body.api_version = "v1"
        body.kind = "PersistentVolume"
        meta = V1ObjectMeta()
        meta.generate_name = "persist-volume"
        body.metadata = meta
        source = V1GlusterfsPersistentVolumeSource(endpoints=endpoint,
                                                   path=DEFAULT_DATASET_VOLUME_NAME,
                                                   read_only=False)
        spec = V1PersistentVolumeSpec(capacity={"storage": DEFAULT_DATASET_VOLUME_SIZE}, access_modes=["ReadWriteMany"],
                                      persistent_volume_reclaim_policy="Retain", glusterfs=source)
        body.spec = spec
        api_response = v1_api.create_persistent_volume(body)
        return api_response.metadata.name

    def create_pvc_gluster(self,v1_api,namespace_name):
        body = kubernetes.client.V1PersistentVolumeClaim()
        body.api_version = "v1"
        body.kind = "PersistentVolumeClaim"
        meta = V1ObjectMeta()
        meta.generate_name = "pvc"
        spec = V1PersistentVolumeClaimSpec()
        spec.access_modes = ["ReadWriteMany"]
        body.spec = spec
        resource = V1ResourceRequirements()
        resource.requests = {"storage": DEFAULT_DATASET_VOLUME_SIZE}
        spec.resources = resource
        body.metadata = meta
        body.spec = spec
        api_response = v1_api.create_namespaced_persistent_volume_claim(namespace_name, body)
        return api_response.metadata.name

    def create_cluster(self,payload):
        quota_creation=True
        if USER_ID not in payload:
            payload[USER_ID]=DEFAULT_USER_ID
        if FRAMEWORK_TYPE not in payload:
            payload[FRAMEWORK_TYPE]=DEFAULT_FRAMEWORK_TYPE
        if FRAMEWORK_VERSION not in payload:
            payload[FRAMEWORK_VERSION]=DEFAULT_FRAMEWORK_VERSION

        if FRAMEWORK_RESOURCES not in payload:
            quota_creation=False
        cluster_management,payload=ClusterManagement.get_cluster_object(payload)
        self.set_cluster_object(cluster_management)
        user_id=int(payload[USER_ID])
        cluster_id=payload[CLUSTER_ID]
        name=payload[CLUSTER_NAME]
        log.debug("The payload is %s" %(payload))

        dpu=payload[FRAMEWORK_RESOURCES][FRAMEWORK_ASSIGN_DPU_TYPE]
        count=payload[FRAMEWORK_RESOURCES][FRAMEWORK_DPU_COUNT]
        # if payload[FRAMEWORK_TYPE] =="POLYAXON":
        #     namespace_name=create_namespace(self.cluster_management,POLYAXON_DEFAULT_NAMESPACE,generate_name=False)
        # else:
        #     namespace_name=create_namespace(self.cluster_management,name,generate_name=False)
        namespace_name=create_namespace(self.cluster_management,name,generate_name=False)
        if quota_creation is True:
            quota_name=create_resource_quota_namespaced(self.cluster_management,namespace_name,count)
        else:
            quota_name=DEFAULT_QUOTA

        # service_name=self.create_gluster_service(self.cluster_management.kube_api,namespace_name)
        # endpoint_name=self.create_gluster_endpoint(self.cluster_management.kube_api,namespace_name)

        volume_claim_name,gfs=create_volume(self.cluster_management,payload[FRAMEWORK_VOLUME_SIZE],namespace_name)
        volume_name=check_pvc(self.cluster_management,namespace_name,volume_claim_name,gfs)
        endpoint_name=get_gfs_endpoint_name(self.cluster_management,namespace_name)
        pv_name=self.create_pv_gluster_volume(self.cluster_management.kube_api,endpoint_name)
        dataset_pvc_name=self.create_pvc_gluster(self.cluster_management.kube_api,namespace_name)

        namespace=MLClusterInfo(clusterId=cluster_id,
                                userId=user_id,
                                namespace=namespace_name,
                                type=payload[FRAMEWORK_TYPE],
                                version=payload[FRAMEWORK_VERSION],
                                dpuType=dpu,
                                dpuCount=count,
                                quotaName=quota_name,
                                status=StackStatus.getString(StackStatus.INPROGRESS.value),
                                glusterVolumeId=gfs)
        namespace.save()
        framework=GetObject.get_ml_object(payload[FRAMEWORK_TYPE])
        framework.create_cluster(payload,self.cluster_management,namespace_name,volume_claim_name)
        namespace.status=StackStatus.getString(StackStatus.DONE.value)
        # mount_gf_volume(cluster_management, volume_name, DEFAULT_CLUSTER_VOLUME_MOUNT_PATH)
        namespace.save()
        return name



    def get_cluster_info(self,ml_cluster_name,user_id):
        record=MLClusterInfo.select().where((MLClusterInfo.namespace == ml_cluster_name) & (MLClusterInfo.userId == user_id)).get()
        cluster_management=ClusterManagement.get_cluster_management_object(ml_cluster_name)
        kube_cluster_name=KubeCluster.select().where(KubeCluster.id==record.clusterId).get().name
        kube_cluster_info=cluster_management.get_kube_cluster_info(kube_cluster_name)
        framework = GetObject.get_ml_object(record.type)
        mlClusterInfo=framework.get_cluster_info(ml_cluster_name,cluster_management,user_id)
        # mlClusterInfo.update({DATASET_VOLUME_MOUNT_POINT:DEFAULT_DATASET_MOUNT_PATH})
        # DATASET_VOLUME_MOUNT_POINT:DEFAULT_DATASET_MOUNT_PATH,
        # DATASET_VOLUME_MOUNT_PATH_IN_POD_REST:DATASET_VOLUME_MOUNT_PATH_IN_POD
        return {KUBE_CLUSTER_INFO:kube_cluster_info,ML_CLUSTER_INFO:mlClusterInfo}

