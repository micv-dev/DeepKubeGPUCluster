import time

from kubernetes.client import V1StorageClass, V1ObjectMeta
from kubernetes.client.rest import ApiException

from common import GetObject
from common.AppEnums import StackStatus, ClusterRole
from dataModels.GlusterFSVolume import GlusterFSVolume
from dataModels.KubeCluster import KubeCluster
from common.MachineResource import *
from kubernetes import client
from common import Logging as log
from dataModels.MachineGPUResourceInfo import MachineGPUResourceInfo
from dataModels.MLClusterInfo import MLClusterInfo

"""
 This class is used to create the kubernetes cluster based upon the DPUs requirements.
 Since we are using readymade kube cluster, this is obsolete.
"""

class ClusterManagement:
    def __init__(self):
        pass

    def set_worker_machines(self,worker_machines):
        self.worker_machines=worker_machines

    def set_master_machines(self,master_machine):
        self.master_machine=master_machine

    def set_kube_auth_token(self,kube_auth_token):
        self.kube_auth_token=kube_auth_token

    def set_joining_token(self,joining_token):
        self.joining_token=joining_token

    def set_kube_object(self,kube_api):
        self.kube_api=kube_api

    def set_storage_api(self,storage_api):
        self.storage_api=storage_api

    def install_helm(self):
        executor = self.master_machine[EXECUTOR]
        output=executor.executeRemoteCommand("kubectl -n kube-system create serviceaccount tiller")
        output=executor.executeRemoteCommand("kubectl create clusterrolebinding tiller --clusterrole cluster-admin --serviceaccount=kube-system:tiller")
        output=executor.executeRemoteCommand("helm init --service-account tiller")
        validate_output(output, "Happy Helming")

    def deploy_nvidia_daemon(self):
        executor = self.master_machine[EXECUTOR]
        output=executor.executeRemoteCommand("kubectl create -f https://raw.githubusercontent.com/NVIDIA/k8s-device-plugin/1.0.0-beta/nvidia-device-plugin.yml")
        validate_output(output, "daemonset.extensions/nvidia-device-plugin-daemonset created")

    def init_kube_cluster(self):
        internalIp = self.master_machine[INTERNAL_IP_ADDRESS]
        executor = self.master_machine[EXECUTOR]
        command=\
            "kubeadm init  --pod-network-cidr={0} --apiserver-advertise-address={1}".format(DEFAULT_CIDR,internalIp)
        output=executor.executeRemoteCommand(command)
        validate_output(output, "you can join any number of worker nodes by running the following")
        executor.executeRemoteCommand("mkdir -p $HOME/.kube")
        executor.executeRemoteCommand("rm -rf $HOME/.kube/config;cp -i /etc/kubernetes/admin.conf $HOME/.kube/config")

        for i in range(CLUSTER_NODE_READY_SLEEP):
            output=executor.executeRemoteCommand("kubectl get nodes")
            try:
                validate_output(output,"NotReady")
                break
            except Exception as exp:
                log.exception(exp,msg=str(i))
            time.sleep(SLEEP_TIME)
        output=executor.executeRemoteCommand(
            "kubectl -n kube-system apply -f https://raw.githubusercontent.com/coreos/flannel/bc79dd1505b0c8681ece4de4c0d86c5cd2643275/Documentation/kube-flannel.yml")
        validate_output(output,"created")
        # for i in range(CLUSTER_NODE_READY_SLEEP):
        #     output = executor.executeRemoteCommand("kubectl get nodes")
        #     try:
        #         validate_output(output,"NotReady")
        #     except Exception as exp:
        #         log.exception(exp,msg=str(i))
        #         break
        #     time.sleep(SLEEP_TIME)
        output=executor.executeRemoteCommand("kubectl create clusterrolebinding default-admin --clusterrole cluster-admin --serviceaccount=default:default")
        validate_output(output,"clusterrolebinding.rbac.authorization.k8s.io/default-admin created")

    def create_storage_class(self):
        storage_class = V1StorageClass(provisioner="kubernetes.io/glusterfs")
        storage_class.api_version = "storage.k8s.io/v1"
        storage_class.kind = "StorageClass"
        meta = V1ObjectMeta()
        meta.name = GFS_STORAGE_CLASS
        storage_class.metadata = meta
        parameters = {"resturl": HEKETI_REST_URL, "restauthenabled": "false", "volumetype": GFS_STORAGE_REPLICATION}
        storage_class.parameters = parameters
        try:
            api_response = self.storage_api.create_storage_class(storage_class)
        except ApiException as e:
            raise Exception(e)

    def start_heketi(self):
        executor = self.master_machine[EXECUTOR]
        output=executor.executeRemoteCommand("nohup /home/user/heketi/heketi --config /home/user/heketi/heketi.json &")
        validate_error(output,"Heket start")

    @staticmethod
    def create_cluster(payload):
        if USER_ID not in payload:
            payload[USER_ID]=DEFAULT_USER_ID
        cluster_management=ClusterManagement()
        cluster_name = payload[CLUSTER_NAME]
        master_ip=payload[CLUSTER_MASTER_IP]

        cluster = KubeCluster(name=cluster_name,userId=payload[USER_ID],
                              status=StackStatus.getString(StackStatus.INPROGRESS.value),
                              startTime=datetime.datetime.now())
        cluster.save()

        master_machine = get_machine(master_ip, cluster.id)
        worker_ip_list = payload[CLUSTER_WORKER_IP_LIST]
        worker_machines = []


        for worker_ip in worker_ip_list:
            machine=get_worker_machine(worker_ip,cluster.id)
            worker_machines.append(machine)

        log.debug("Worker machines {0},Master machines {1}".format(worker_machines, master_machine))
        cluster_management.set_master_machines(master_machine)
        cluster_management.set_worker_machines(worker_machines)
        cluster_management.init_kube_cluster()
        cluster_management.get_kube_auth_token()
        log.debug("The auth token is {0}".format(cluster_management.kube_auth_token))
        cluster_management.get_joining_token()
        log.debug("The joining token is {0}".format(cluster_management.joining_token))
        cluster_management.get_kube_object()
        # self.start_heketi()
        cluster_management.create_storage_class()
        cluster_management.add_worker_nodes()
        cluster.status=StackStatus.getString(StackStatus.DONE.value)
        cluster.save()
        mount_gf_volume(cluster_management, DEFAULT_DATASET_VOLUME_NAME, DEFAULT_DATASET_MOUNT_PATH)
        push_cluster_management_object(cluster_name,cluster_management)

    def add_worker_nodes(self):
        executor = self.master_machine[EXECUTOR]
        executor.executeRemoteCommand("systemctl start docker")
        output = executor.executeRemoteCommand("systemctl status docker")
        if output.errCode != 0:
            raise Exception("Error occured while starting the docker daemon on %s."
                            "Msg is %s" % (self.master_machine["ipAddress"], output.errString))
        if "Active: active (running)" not in output.outString:
            raise Exception("Error occured while starting the docker daemon on %s.")

        for machine in self.worker_machines:
            executor = machine[EXECUTOR]
            executor.executeRemoteCommand("systemctl start docker")
            output = executor.executeRemoteCommand("systemctl status docker")
            if output.errCode != 0:
                raise Exception("Error occured while starting the docker daemon on %s."
                                "Msg is %s" % (machine[IP_ADDRESS], output.errString))
            if "Active: active (running)" not in output.outString:
                raise Exception("Error occured while starting the docker daemon on %s.")
            output=executor.executeRemoteCommand(self.joining_token)
            if output.errCode != 0:
                raise Exception("Error occured while adding worker to the cluster.%s."
                                "Msg is %s" % (machine[IP_ADDRESS], output.errString))
        self.check_if_cluster_is_ready()
        self.deploy_nvidia_daemon()
        self.install_helm()
        self.check_gpu_availability()

    @staticmethod
    def add_node(payload):
        if ROLE not in payload:
            payload[USER_ID]=DEFAULT_USER_ID
            payload[ROLE]=ClusterRole.getString(ClusterRole.WORKER.value)
        ip_addr=payload[IP_ADDRESS]
        internal_ip_addr=payload[INTERNAL_IP_ADDRESS]
        user_id=payload[ADD_NODE_USER_ID]
        password=payload[ADD_NODE_PASSWORD]
        cluster_role=payload[ROLE]
        # cluster_management_object=get_cluster_management_object(cluster_id)
        machine=MachinePool(name=ip_addr,ipAddress=ip_addr,internalIpAddress=internal_ip_addr,
                            kubeVersion=DEFAULT_KUBE_VERSION,
                            role=cluster_role,
                            password=password,
                            userId=user_id,
                            clusterId=0
                            )
        machine.save()
        machine_info=machine_executor(machine)
        executor=machine_info[EXECUTOR]
        output=executor.executeRemoteCommand("nvidia-smi --query-gpu=name,driver_version,memory.total --format=csv ")
        output=output.outString.encode(encoding='UTF-8',errors='strict')
        gpu_details=output.split("\n")
        for i in range(1,len(gpu_details)):
            gpu_detail=gpu_details[i]
            if len(gpu_detail)==0:
                continue
            info=gpu_detail.split(",")
            name="dpu-"+info[0].replace(" ","-")
            driver_version=info[1]
            memory=info[2]
            dpu=DPU.select().where(DPU.name==name).get()
            records=MachineGPUResourceInfo.select().where((MachineGPUResourceInfo.machinePool==machine) &
                                                  (MachineGPUResourceInfo.driverVersion==driver_version)&
                                                  (MachineGPUResourceInfo.dpuId==dpu))
            if len(records)==0:
                machine_resource=MachineGPUResourceInfo(machinePool=machine,driverVersion=driver_version,memory=memory,
                                       dpuId=dpu,dpuCount=1,allocatedDPUCount=0)
                machine_resource.save()
            else:
                if len(records)==1:
                    record=records[0]
                    record.dpuCount=record.dpuCount+1
                    record.save()


    def add_new_worker(self,cluster_name,worker_ip_list):
        for worker_ip in worker_ip_list:
            self.worker_machines.append(get_worker_machine(cluster_name,worker_ip))
        cluster_management_object=get_cluster_management_object(cluster_name)
        for worker_ip in worker_ip_list:
            machine=MachinePool().select().where(MachinePool.ipAddress==worker_ip)
            machine = machine_executor(machine)
            executor=machine[EXECUTOR]
            executor.executeRemoteCommand("systemctl start docker")
            output = executor.executeRemoteCommand("systemctl status docker")
            if output.errCode != 0:
                raise Exception("Error occured while starting the docker daemon on %s."
                                "Msg is %s" % (worker_ip, output.errString))
            if "Active: active (running)" not in output.outString:
                raise Exception("Error occured while starting the docker daemon on %s.")
            output = executor.executeRemoteCommand(self.joining_token)
            if output.errCode != 0:
                raise Exception("Error occured while adding worker to the cluster.%s."
                                "Msg is %s" % (worker_ip, output.errString))
        cluster_management_object.worker_machines.append(machine)


    def get_read_index(self,conditions):
        id = 0
        for idx, condition in enumerate(conditions):
            if condition.type == "Ready":
                id = idx
                break
        return id

    def check_gpu_availability(self):
        all_ready=True
        for i in range(CLUSTER_NODE_READY_COUNT):
            all_ready = True
            nodes = self.kube_api.list_node()
            for node in nodes.items:
                if node.metadata.name.startswith(CLUSTER_NODE_NAME_PREFIX):
                    if "nvidia.com/gpu" in node.status.allocatable and int(node.status.allocatable["nvidia.com/gpu"]) > 0:
                        log.debug("GPU exist .node {0},count {1}".format(node,node.status.allocatable["nvidia.com/gpu"]))
                    else:
                        log.debug("Gpu does not exist {0}".format(node))
                        time.sleep(CLUSTER_NODE_READY_SLEEP)
                        all_ready=False
            if all_ready is True:
                break
        if all_ready is False:
            raise Exception("GPU is not getting detected")

    def check_if_cluster_is_ready(self):
        all_ready = True
        for i in range(CLUSTER_NODE_READY_COUNT):
            nodes = self.kube_api.list_node()
            all_ready = True
            for node in nodes.items:
                conditions = node.status.conditions
                id = self.get_read_index(conditions)
                if conditions[id].status == "True" and conditions[id].reason == "KubeletReady":
                    pass
                else:
                    log.debug("Not ready node is {0}".format(node))
                    all_ready=False
                    time.sleep(CLUSTER_NODE_READY_SLEEP)
            if all_ready is True:
                break
        if all_ready is False:
            raise Exception("Some nodes/node of the cluster are/is not ready")



    def get_kube_auth_token(self):
        output=self.master_machine[EXECUTOR].executeRemoteCommand(
            "(kubectl get secrets -o jsonpath=\"{.items[?(@.metadata.annotations['kubernetes\.io/service-account\.name']=='default')].data.token}\"|base64 -d)")
        self.set_kube_auth_token(output.outString)

    def delete_cluster(self,cluster_name,user_id=1):
        machines=MachinePool.select().where(MachinePool.name==cluster_name)
        cluster_management_object=ClusterManagement.get_cluster_management_object(cluster_name)
        executor= cluster_management_object.master_machine[EXECUTOR]
        executor.executeRemoteCommand("kubeadm reset --force")
        for worker in cluster_management_object.worker_machines:
            executor = worker[EXECUTOR]
            executor.executeRemoteCommand("kubeadm reset --force")

        cluster=KubeCluster.select().where(KubeCluster.name==cluster_name).get()
        records=MLClusterInfo.select().where(MLClusterInfo.clusterId == cluster.id)
        for record in records:
            GlusterFSVolume.delete().where(GlusterFSVolume.id==record.id).execute()
            record.delete()

        KubeCluster.delete().where(KubeCluster.name==cluster_name).execute()
        cluster_obj = GetObject.get_ml_object(cluster.frameworkType)
        # cluster_obj.delete_cluster(payload)


    def get_cluster_info(self,cluster_name,user_id=1):
        cluster = KubeCluster.select().where(KubeCluster.name==cluster_name and KubeCluster.userId==user_id)[0]
        cluster_obj = GetObject.get_ml_object(cluster.frameworkType)
        return cluster_obj.get_cluster_info(cluster_name)


    def get_kube_object(self,host=None,port=6443,token=None):
        if host is None and token is None:
            host=self.master_machine[IP_ADDRESS]
            token=self.kube_auth_token

        configuration = client.Configuration()
        configuration.host ="https://"+ host+":"+str(port)
        configuration.verify_ssl = False
        configuration.debug = True
        configuration.api_key = {"authorization": "Bearer " + token}
        client.Configuration.set_default(configuration)
        v1_api = client.CoreV1Api()
        self.set_kube_object(v1_api)
        storage_api = client.StorageV1Api(client.ApiClient(configuration))
        self.set_storage_api(storage_api)

    def get_joining_token(self):
        output = self.master_machine[EXECUTOR].executeRemoteCommand(
            "kubeadm token create --print-join-command")
        self.set_joining_token(output.outString)

    def get_kube_cluster_info(self, cluster_name):
        cluster = KubeCluster.select().where(KubeCluster.name==cluster_name)[0]
        records = MachinePool.select().where(MachinePool.clusterId == cluster.id)
        master_ip = None
        worker_ip_list = []
        no_of_gpus = 0
        for record in records:
            if record.role == ClusterRole.getString(ClusterRole.MASTER.value):
                master_ip = record.ipAddress
            else:
                if record.role == ClusterRole.getString(ClusterRole.WORKER.value):
                    worker_ip_list.append(record.ipAddress)
                    machine_pool_gpu=MachineGPUResourceInfo.select().where(MachineGPUResourceInfo.machinePool==record).get()
                    no_of_gpus = no_of_gpus + int(machine_pool_gpu.dpuCount)
        return {NAME: cluster_name, MASTER_IP: master_ip, CLUSTER_WORKER_IP_LIST: worker_ip_list, GPU_COUNT: no_of_gpus,
                DATASET_VOLUME_MOUNT_POINT:DEFAULT_DATASET_MOUNT_PATH
                }


    @staticmethod
    def get_cluster_object(payload):
        cluster_id = None
        if FRAMEWORK_RESOURCES  in payload:
            dpu_type = payload[FRAMEWORK_RESOURCES][FRAMEWORK_ASSIGN_DPU_TYPE]
            dpuCount = payload[FRAMEWORK_RESOURCES][FRAMEWORK_DPU_COUNT]
            dpuCount=int(dpuCount)
            dpu = DPU.select().where(DPU.name == dpu_type).get()
            records = MachinePool.select().where((MachinePool.role == ClusterRole.getString(ClusterRole.WORKER.value)))
            for record in records:
                machine_gpu_records=MachineGPUResourceInfo.select().where(MachineGPUResourceInfo.machinePool==record).get()
                dpu = int(machine_gpu_records.dpuCount) - int(machine_gpu_records.allocatedDPUCount)
                if dpu >= dpuCount:
                    machine_gpu_records.allocatedDPUCount = machine_gpu_records.allocatedDPUCount + dpuCount
                    cluster_id = record.clusterId
                    machine_gpu_records.save()
                    break
        else:
            record= MachinePool.select().where(MachinePool.role == ClusterRole.getString(ClusterRole.WORKER.value)).get()
            machine_gpu_record = MachineGPUResourceInfo.select().where(
                MachineGPUResourceInfo.machinePool == record).get()
            dpu = DPU.select().where(DPU.id == machine_gpu_record.dpuId).get()
            payload[FRAMEWORK_RESOURCES]={FRAMEWORK_ASSIGN_DPU_TYPE:dpu.name,
                                          FRAMEWORK_DPU_COUNT:machine_gpu_record.dpuCount}
            cluster_id = record.clusterId
            machine_gpu_record.allocatedDPUCount = machine_gpu_record.dpuCount
            machine_gpu_record.save()
        if cluster_id is not None:
            if CLUSTER_NAME not in payload:
                record=KubeCluster.select().where(KubeCluster.id==cluster_id).get()
                payload[CLUSTER_NAME]=record.name
            payload[CLUSTER_ID]=cluster_id
            cluster_master = MachinePool.select().where((MachinePool.clusterId == cluster_id) &
                                                        (MachinePool.role== ClusterRole.getString(ClusterRole.MASTER.value))).get()
            cluster_management=get_cluster_management_object(cluster_id)
            if cluster_management is  None:
                machine = machine_executor(cluster_master)
                cluster_management=ClusterManagement.get_cluster(cluster_id,machine)
        return cluster_management,payload

    @staticmethod
    def get_cluster(cluster_id,master_machine):
        cluster_management = ClusterManagement()
        cluster_management.set_master_machines(master_machine)
        cluster_management.get_kube_auth_token()
        cluster_management.get_kube_object()
        push_cluster_management_object(cluster_id, cluster_management)
        return cluster_management

    @staticmethod
    def get_cluster_management_object(ml_cluster_name,kube_cluster=None):
        if kube_cluster is not None:
            cluster_name = kube_cluster.name
        else:
            record=MLClusterInfo.select().where(MLClusterInfo.namespace == ml_cluster_name).get()
            kube_cluster = KubeCluster.select().where(KubeCluster.id == record.clusterId).get()
            cluster_name=kube_cluster.name
        if cluster_name is not None:
            # cluster = KubeCluster.select().where(KubeCluster.name == cluster_name).get()
            cluster_master = MachinePool.select().where((MachinePool.clusterId == kube_cluster.id) &
                                                        (MachinePool.role == ClusterRole.getString(ClusterRole.MASTER.value))).get()
            master_machine = machine_executor(cluster_master)

        records=MachinePool.select().where((MachinePool.clusterId == kube_cluster.id) &
                                                        (MachinePool.role == MachinePool.role == ClusterRole.getString(ClusterRole.WORKER.value)))
        worker_machines=[]
        for record in records:
            executor = machine_executor(record)
            worker_machines.append(executor)
        cluster_management = get_cluster_management_object(kube_cluster.id)
        if cluster_management is  None:
            cluster_management = ClusterManagement.get_cluster(kube_cluster.id, master_machine)
        return cluster_management

