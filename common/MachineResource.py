from common.AppEnums import Resources
from common.remote_execution.RemoteExecutor import RemoteExecuter
from dataModels.MachineGPUResourceInfo import MachineGPUResourceInfo
from dataModels.MachinePool import *
from dataModels.DPU import *
from common import Logging as log
from common.Utils import *
from Constants import *


def get_free_resource(resource_dict,cluster_name):
    machines=[]
    for resouce in resource_dict:
        dpu_type=resouce
        count=resource_dict[resouce]
        dpu=DPU.select().where(DPU.name==dpu_type).get()
        records=MachinePool.select().where(MachinePool.dpuId==dpu and MachinePool.role=="WORKER")\
                                        .order_by(MachinePool.dpuCount)
        available_count=0
        for record in records:
            record_resource=0
            if available_count >= count:
                break
            if record.dpuCount >= count:
                available_count+=count
                record_resource=count
            else:
                available_count += record.dpuCount
                record_resource=record.dpuCount

            machine=machine_executor(record)
            machines.append(machine)
            record.clusterName=cluster_name
            record.save()

    return machines


def machine_executor(record):
    machine = {"ipAddress": record.ipAddress, "userName": record.userId, "password": record.password,
               "sshFilePath": record.sshFilePath, "internalIpAddress": record.internalIpAddress}
    ssh_conf = get_ssh_conf_object(machine)
    executor = RemoteExecuter(machine["ipAddress"], ssh_conf)
    machine["executor"] = executor
    return machine

def get_machine(master_ip, cluster_id):
    try:
        records=MachinePool.select().where((MachinePool.internalIpAddress==master_ip) &
                                           (MachinePool.clusterId==None))
        if len(records)==0:
            raise Exception("Master %s,%s machines are not avalable" %(master_ip,cluster_id))
        machine_record=records.get()
        record=MachineGPUResourceInfo.select().where(MachineGPUResourceInfo.machinePool==machine_record).get()
        record.allocatedDPUCount = record.allocatedDPUCount + 1
        record.save()
        machine_record.clusterId=cluster_id
        machine_record.save()
        machine=machine_executor(machine_record)
    except Exception as exp:
        raise exp
    return machine

def get_worker_machine(master_ip, cluster_id):
    records=MachinePool.select().where((MachinePool.internalIpAddress==master_ip) &
                                       (MachinePool.clusterId==None))
    if len(records)==0:
        raise Exception("Master %s,%s machines are not avalable" %(master_ip,cluster_id))
    record=records.get()
    record.clusterId=cluster_id
    record.save()
    machine=machine_executor(record)
    return machine

def read_config_file(file_path):
    data = ""
    with open(file_path) as myfile:
        lines = myfile.readlines()
        for line in lines:
            data = data + line
    return data
