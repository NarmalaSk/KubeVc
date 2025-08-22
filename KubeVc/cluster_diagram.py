import boto3
import datetime
import json
import os
import yaml
from kubernetes import client, config
from diagrams import Diagram, Cluster
from diagrams.k8s.compute import Pod, Deployment
from diagrams.k8s.network import Service

# ---- Load KubeVc.yaml ----
CONFIG_FILE = "KubeVc.yaml"
if not os.path.exists(CONFIG_FILE):
    raise FileNotFoundError(f"{CONFIG_FILE} not found!")

with open(CONFIG_FILE, "r") as f:
    cfg = yaml.safe_load(f)

# ---- S3 Config ----
S3_BUCKET = cfg["s3"]["bucket"]
S3_REGION = cfg["s3"]["region"]
S3_ACCESS_KEY = cfg["s3"]["access_key"]
S3_SECRET_KEY = cfg["s3"]["secret_key"]

# ---- Kubernetes Config ----
KUBECONFIG_PATH = cfg["kubeconfig"]["path"]
config.load_kube_config(config_file=KUBECONFIG_PATH)

# ---- Kubernetes API clients ----
v1 = client.CoreV1Api()
apps_v1 = client.AppsV1Api()

# ---- Fetch Cluster State ----
pods = v1.list_pod_for_all_namespaces().items
deployments = apps_v1.list_deployment_for_all_namespaces().items
services = v1.list_service_for_all_namespaces().items

# ---- Generate Diagram ----
diagram_file = "cluster_state.png"
with Diagram("Cluster State", show=False, filename="cluster_state", outformat="png"):
    with Cluster("Kubernetes Cluster"):
        dep_nodes = {}
        for dep in deployments:
            dep_nodes[dep.metadata.name] = Deployment(dep.metadata.name)

        for svc in services:
            svc_node = Service(svc.metadata.name)
            for dep in deployments:
                if dep.metadata.namespace == svc.metadata.namespace:
                    svc_node >> dep_nodes[dep.metadata.name]

        for pod in pods:
            pod_node = Pod(pod.metadata.name)
            for owner in pod.metadata.owner_references or []:
                if owner.kind == "ReplicaSet":
                    # Connect the pod to the deployment
                    for dep_node in dep_nodes.values():
                        dep_node >> pod_node

# ---- Metadata ----
commit_hash = cfg.get("commit_hash", "local-run")
repo_name = cfg.get("repo_name", "unknown-repo")
file_changed = cfg.get("file_changed", "unknown.yaml")

metadata = {
    "commit_hash": commit_hash,
    "repo_name": repo_name,
    "file_changed": file_changed,
    "timestamp": datetime.datetime.utcnow().isoformat() + "Z"
}

metadata_file = "metadata.json"
with open(metadata_file, "w") as f:
    json.dump(metadata, f, indent=4)

# ---- Upload to S3 ----
s3 = boto3.client(
    "s3",
    aws_access_key_id=S3_ACCESS_KEY,
    aws_secret_access_key=S3_SECRET_KEY,
    region_name=S3_REGION
)

diagram_key = f"diagrams/{commit_hash}_{diagram_file}"
metadata_key = f"metadata/{commit_hash}.json"

s3.upload_file(diagram_file, S3_BUCKET, diagram_key)
s3.upload_file(metadata_file, S3_BUCKET, metadata_key)

print(f"✅ Uploaded diagram: s3://{S3_BUCKET}/{diagram_key}")
print(f"✅ Uploaded metadata: s3://{S3_BUCKET}/{metadata_key}")

