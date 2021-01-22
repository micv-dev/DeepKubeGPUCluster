# DeepKubeGPUCluster
This project aims to ease the job(one click set up) of setting up kubernetes cluster to use attached nvidia gpu to the underlying host in a POD.It takes care of configuring the nvidia GPU and GlusterFs distributed storage to make it available inside the kubernetes cluster with the resource management.
# Following functionality have been implemented:
 - Create Kubernetes cluster
 - Create namespace with required number and type of GPU resources and distributed storage
 - Add new node and resources to the existing kubernetes cluster
 - List cluster
 - Delete cluster

# Steps to set up
 - git clone <> and cd DeepKubeGPUCluster
 - Run install -r requirementes.txt
 - Create database named 'deepkube' and configure db details in app.config
 - Create GlusterFs cluster (minimum 3 nodes)
 - Set up Heketi for GlusterFs
 - Add available host details in 'machinePool' db table
 - Start app.py

# Benefits are :
 - Get ready GPU kubernetes cluster platform in a matter of few minutes.
 - Supports hybrid GPU kubernetes cluster creation.
 - Resource allocation will be done intelligently.
 - Uses high throughput read optimized GlusterFs volume to read the data.
 - Fault tolerant , highly available persistent storage.
 - Easy management of the cluster through intuitive UI.
 
 For more info, please contact to  contact@micv.in 