from clusterManagement.MLClusterBase import MLClusterBase
from clusterManagement.PolyaxonResponse import PolyaxonResponse
from dataModels.GlusterFSVolume import GlusterFSVolume
from dataModels.KubeCluster import KubeCluster
from common.MachineResource import *
from common import Logging as log
from dataModels.MLClusterInfo import MLClusterInfo


class PolyaxonCluster(MLClusterBase):
    def __init__(self):
        pass

    def create_cluster(self,spec,cluster_management,namespace_name,volume_claim_name,dataset_pvc_name):
        try:
            executor=cluster_management.master_machine[EXECUTOR]
            config = read_config_file(POLYAXON_TEMPLATE)
            executor.executeRemoteCommand("helm repo add polyaxon https://charts.polyaxon.com")
            config=config.replace("<existingClaim>",volume_claim_name)
            config=config.replace("<dataSetClaim>",dataset_pvc_name)
            config=config.replace("<namespaceName>",namespace_name)
            # port_list=get_available_port(cluster_management.master_machine["ipAddress"],3)
            # config=config.replace("<nodePort>",str(port_list[0]))
            # config=config.replace("<apiExternalPort>",str(port_list[1]))
            # config=config.replace("<streamExternalPort>",str(port_list[2]))
            executor.executeRemoteCommand("> "+ POLYAXON_CONFIG_FILE)
            executor.executeRemoteCommand("echo -e '"+config+"' > "+POLYAXON_CONFIG_FILE)
            install_polyaxon = "helm install polyaxon/polyaxon \
                               --name="+namespace_name+" \
                                --namespace=" + namespace_name+ " -f " + POLYAXON_CONFIG_FILE
            log.debug("Polyaxon install command is %s" %(install_polyaxon))
            output=executor.executeRemoteCommand(install_polyaxon)
            validate_error(output, "Polyaxon installation")
            internalIp = cluster_management.master_machine["internalIpAddress"]
            patch_command = "kubectl patch svc "+namespace_name+"-polyaxon-api -n "+namespace_name+" -p '{\"spec\": {\"type\": \"LoadBalancer\", \"externalIPs\":[\"" + internalIp + "\"]}}'"
            output = executor.executeRemoteCommand(patch_command)
            validate_error(output, "Validate patch ip address to polyaxon load balancer")
        except Exception as exp:
            log.exception(exp)
            raise Exception("Error occured while creating the polyaxon cluster.%s" %(exp.message))




    def delete_cluster(self,payload):
        try:
            user_id=payload[USER_ID]
            cluster_name=payload[CLUSTER_NAME]
            records=MachinePool.select().where(MachinePool.userId==user_id and MachinePool.clusterId==cluster_name)
            for record in records:
                record.clusterName=""
                record.status=Resources.getString(Resources.FREE.value)
                record.minervaUserId = -1
                record.save()
            record=KubeCluster.delete().where(KubeCluster.userId==user_id and KubeCluster.name==cluster_name)
            record.execute()
        except Exception as exp:
            log.exception(exp)
            raise Exception("Error occured while deleting the polyaxon cluster.%s" % (exp.message))

    def get_http_port(self,cluster_name,cluster_management):
        return str(POLYAXON_DEFAULT_HTTP_PORT)

    def get_ws_port(self,cluster_name,cluster_management):
        return  POLYAXON_DEFAULT_WS_PORT


    def get_cluster_info(self, ml_cluster_name, cluster_management, user_id):
        name=ml_cluster_name
        v1_api = cluster_management.kube_api
        webURL="http://"+cluster_management.master_machine[IP_ADDRESS]+":"+self.get_http_port(ml_cluster_name, cluster_management)
        webSockerPort=self.get_ws_port(ml_cluster_name, cluster_management)
        namespace=MLClusterInfo.select().where((MLClusterInfo.namespace == ml_cluster_name) & (MLClusterInfo.userId == user_id)).get()
        framework_type=namespace.type
        framework_version=namespace.version
        namespace_name=namespace.namespace
        quota_name=namespace.quotaName
        quota_info = {QUOTA_NAME: quota_name,QUOTA_USED:"",QUOTA_LIMIT:""}
        if quota_name != DEFAULT_QUOTA:
            quota=v1_api.read_namespaced_resource_quota(quota_name,namespace_name)
            quota_info[QUOTA_USED]=quota.status.used[NVIDIA_GPU_RESOURCE_NAME]
            quota_info[QUOTA_LIMIT]=quota.status.hard[NVIDIA_GPU_RESOURCE_NAME]

        gfs_record=GlusterFSVolume.select().where(GlusterFSVolume.id==namespace.glusterVolumeId).get()
        volume_name=gfs_record.name
        volume_size=gfs_record.size

        free_volume=get_volume_usage(volume_name,cluster_management)
        volume_info={VOLUME_NAME:volume_name,MOUNT_PATH_IN_POD:DEFAULT_VOLUME_MOUNT_PATH,
                     VOLUME_TOTAL_SIZE:str(volume_size)+"gb",VOLUME_FREE:free_volume+"gb",
                     CLUSTER_VOLUME_MOUNT_PATH:DEFAULT_CLUSTER_VOLUME_MOUNT_PATH,
                     DATASET_VOLUME_MOUNT_PATH_IN_POD_REST : DATASET_VOLUME_MOUNT_PATH_IN_POD
        }
        response=PolyaxonResponse(name, webURL, webSockerPort, framework_type, framework_version, namespace_name, quota_info, volume_info,
                                  POLYAXON_DEFAULT_USER_ID, POLYAXON_DEFAULT_PASSWORD
                                  )
        return response
