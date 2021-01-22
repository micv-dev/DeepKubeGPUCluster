from clusterManagement.tensorflow.TensorflowCluster import TensorflowCluster


def get_ml_object(cluster_type):
    if cluster_type == "TENSORFLOW-GPU":
        return TensorflowCluster()


