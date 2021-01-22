from common.remote_execution.SSHConf import sshConfig
import socket
from Constants import *
import json

from dataModels.KubeCluster import KubeCluster

cluster_management_objects={}
def get_cluster_management_object(kube_cluster_name):
    if kube_cluster_name not in cluster_management_objects:
        return None
    else:
        return cluster_management_objects[kube_cluster_name]

def push_cluster_management_object(kube_cluster_name,cluster_management_object):
    cluster_management_objects[kube_cluster_name]=cluster_management_object

def get_ssh_conf_object(machine):
    ssh_conf=None
    if machine["sshFilePath"] is not None:
        ssh_conf = sshConfig(ssh_host=machine["ipAddress"], ssh_user=machine["userName"],
                             ssh_pass_file=machine["sshFilePath"],ssh_pass=None)
    else:
        ssh_conf = sshConfig(ssh_host=machine["ipAddress"], ssh_user=machine["userName"],
                             ssh_pass=machine["password"])
    return ssh_conf

def get_join_token(remote_executor):
    output=remote_executor.executeRemoteCommand("kubeadm token create --print-join-command ")
    if output.errCode!=0:
        raise Exception("Not able to fetch join token.%s", output.errString)
    return output.outString.strip()


def validate_error(output, message):
    if output.errCode != 0:
        raise Exception("%s,%s " %(message,output.errString))

def validate_output(output,text):
    if text not in output.outString:
        raise Exception("%s is not in %s" %(text,output.outString))



def get_available_port(host,count):
    port_list=[]
    for port in range(POLYAXON_NODE_PORT_RANGE_START, POLYAXON_NODE_PORT_RANGE_END):
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            res = sock.connect_ex((host, port))
            if res !=0:
                port_list.append(port)
                if len(port_list)==count:
                    break
        finally:
                sock.close()
    if len(port_list) != count:
        raise Exception("Ports are not availablwe")
    return port_list


def get_volume_usage(volume_name,cluster_management):
    disk_space_free_txt = "Disk Space Free"
    total_disk_space_txt = "Total Disk Space"
    disk_space_free = 0
    total_disk_space = 0

    executor=cluster_management.master_machine[EXECUTOR]
    output=executor.executeRemoteCommand("gluster volume status "+volume_name+" detail")
    lines = output.outString.split("\n")
    for line in lines:
        line = line.strip()
        if disk_space_free_txt in line:
            arr = line.split(":")
            space = arr[1]
            space = space.replace("GB", "")
            disk_space_free += float(space)
        if total_disk_space_txt in line:
            if total_disk_space_txt in line:
                arr = line.split(":")
                space = arr[1]
                space = space.replace("GB", "")
                total_disk_space += float(space)
    disk_space_free=float(disk_space_free)/GLUSTER_DEFAULT_REP_FACTOR
    return str(disk_space_free)

def object_to_json(obj):
    return json.dumps(obj, default=lambda o: o.__dict__)

def get_cluster_id(cluster_name,user_id):
    cluster=KubeCluster.select().where((KubeCluster.name==cluster_name)&(KubeCluster.userId==user_id)).get()
    return cluster


def mount_gf_volume(cluster_management, volume_name, mount_path):
    executor=cluster_management.master_machine[EXECUTOR]
    executor.executeRemoteCommand("mkdir -p "+mount_path)
    # validate_error(output,"Mount dataset path creation.Path is {0}".format(mount_path))
    cmd="umount  {0}".format(mount_path)
    executor.executeRemoteCommand(cmd)
    cmd = "mount -o acl,rw -t glusterfs  {0}:/{1} {2}".format(DEFAULT_GLUSTER_SERVER,volume_name,mount_path)
    output=executor.executeRemoteCommand(cmd)
    validate_error(output,"Mount dataset path "+mount_path)

    fstab_entry="{0}:/{1} {2}  glusterfs acl,rw,defaults,_netdev,x-systemd.automount 0 0".format(DEFAULT_GLUSTER_SERVER,
                                                                                                 volume_name,
                                                                                                 mount_path)
    # fstab_entry = DEFAULT_GLUSTER_SERVER + ":/" + volume_name + " " + mount_path + " glusterfs acl,rw,defaults,_netdev,x-systemd.automount 0 0"
    cmd="echo {0} >> /etc/fstab".format(fstab_entry)
    executor.executeRemoteCommand(cmd)


def get_gfs_endpoint_name(cluster_management,namespace_name):
    api_response = cluster_management.kube_api.list_namespaced_endpoints(namespace_name)
    endpont_name=None
    for item in api_response.items:
        if DYNAMIC_GLUSTERFS_ENDPOINT_STARTS_WITH in item.metadata.name:
            endpont_name=item.metadata.name
            break
    return endpont_name