# KubeVC

KubeVC (**Kubernetes Version Control**) is a CLI tool that helps you **snapshot, version-control, visualize, and rollback** Kubernetes cluster states.  
It integrates with **Git** and **S3** to provide a history of your cluster’s evolution, making debugging, auditing, and recovery easier.
<img width="500" height="500" alt="" src="https://github.com/user-attachments/assets/631d77f1-587c-4691-bb5a-10278acc851c" />

---

## 🚀 Features
- **Cluster Snapshots** → Export complete cluster state (YAML).
- **Version Control** → Track changes in Git or S3.
- **Visual Diagrams** → Auto-generate cluster diagrams
- **History Tracking** → View timeline of snapshots and diffs.
- **Rollback Support** → Restore cluster to any previous state.
- **Multi-backend Support** → Local, Git, or S3 storage.

---

## 📦 Installation

### Prerequisites
- Kubernetes cluster + `kubectl` configured
- Git installed
- AWS CLI (if using S3 backend)

### Clone the repo
```bash
git clone https://github.com/NarmalaSk/KubeVc.git
cd kubevc
```

### Configure S3 for Remote Backend and KubeConfig for K8s Cluster access
```yaml
cd KubeVc
vi KubeVc.yaml or nano KubeVc.yaml
```
```yaml 
kube:
  config_path: 
s3:
  access_key_id: 
  bucket: 
  region: 
  secret_access_key:
```
### Run KubeVc Configure for applying creds
```bash
python3 KubeVc.py configure

```
### Run KubeVc as service
```bash
python3 KubeVc.py start
```
#### Expose it as Service && copy Ip
```bash
copy instance ip/webhook
```
### Configure webhook for your git repo
```
payload url :paste instance ip/webhook

content type: application/json

send push_event
```
##### Congrats 🎉🎉 you have setupped KubeVc go to https://service-ip:5000/

 
