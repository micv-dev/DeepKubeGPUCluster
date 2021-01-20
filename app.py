from flask import Flask, request, jsonify
from flask_cors import CORS
import tornado.wsgi
import tornado.httpserver

from clusterManagement.Framework import Framework
from clusterManagement.ClusterManagement import ClusterManagement
from common import Logging as log
from common import ReadConfig as conf
import Paths
from common.RestResponse import RestResponse
from dataModels.MachineGPUResourceInfo import MachineGPUResourceInfo
from dataModels.BaseModel import *
from dataModels.DPU import DPU
from dataModels.GlusterFSVolume import GlusterFSVolume
from dataModels.KubeCluster import KubeCluster
from dataModels.MachinePool import MachinePool
from dataModels.MLClusterInfo import MLClusterInfo
from dataModels.User import User
from common.Utils import *

db.create_tables([KubeCluster, GlusterFSVolume, DPU, MachinePool, User, MLClusterInfo, MachineGPUResourceInfo])

config=conf.getConfig()
app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

@app.route(Paths.CREATE_CLUSTER_PATH, methods=['PUT'])
def create_kube_cluster():
    payload = request.get_json(force=True)
    log.debug("Create cluster payload is {0}".format(payload))
    ClusterManagement.create_cluster(payload)
    out = {"status": "SUCCESS", "message": "Successfully processed", "data": None}
    return jsonify(out)

@app.route(Paths.CREATE_FRAMEWORK, methods=['PUT'])
def deploy_ml_cluster():
    payload = request.get_json(force=True)
    log.debug("Create cluster payload is {0}".format(payload))
    framework = Framework()
    cluster_name=framework.create_cluster(payload)
    info = framework.get_cluster_info(cluster_name, user_id=1)
    response=RestResponse(status=SUCCESS_MESSAGE_STATUS,message="Successfully processed",data=info)
    return object_to_json(response)



@app.route(Paths.ML_CLUSTER, methods=['GET'])
def get_ml_cluster(clusterName):
    framework = Framework()
    info=framework.get_cluster_info(clusterName,user_id=1)
    response=RestResponse(status=SUCCESS_MESSAGE_STATUS,message="Successfully processed",data=info)
    return object_to_json(response)


##Not yet implemented completely ###
@app.route(Paths.DELETE_CLUSTER_PATH, methods=['PUT'])
def delete_cluster():
    payload = request.get_json(force=True)
    cluster_management = ClusterManagement()
    cluster_management.delete_cluster(payload)
    out = {"status": "SUCCESS", "message": "Successfully processed", "data": "test"}
    return jsonify(out)

@app.route(Paths.ADD_NODE_KUBE_CLUSTER, methods=['PUT'])
def add_node():
    payload = request.get_json(force=True)
    if USER_ID not in payload:
        payload[USER_ID]=DEFAULT_USER_ID
    # cluster_management = ClusterManagement.get_cluster_management_object(ml_cluster_name=None,kube_cluster=cluster)
    ClusterManagement.add_node(payload)
    out = {"status": "SUCCESS", "message": "Successfully processed", "data": None}
    return jsonify(out)

##Not yet implemented completely ###
# @app.route(Paths.ADD_NODE_KUBE_CLUSTER, methods=['PUT'])
# def add_worker():
#     payload = request.get_json(force=True)
#     cluster_name=payload[CLUSTER_NAME]
#     cluster_management = get_cluster_management_object(cluster_name)
#     cluster_management.delete_cluster(payload)
#     out = {"status": "SUCCESS", "message": "Successfully processed", "data": None}
#     return jsonify(out)

###########################################################################


def start_tornado(app, port=config.get("app","port")):
    try:
        http_server = tornado.httpserver.HTTPServer(
            tornado.wsgi.WSGIContainer(app))
        http_server.listen(port)
        tornado.ioloop.IOLoop.instance().start()
    except Exception as exp:
        log.exception(exp)


if __name__ == "__main__":
    start_tornado(app)