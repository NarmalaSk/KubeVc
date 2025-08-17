# KubeVCls

KubeVC (**Kubernetes Version Control**) is a CLI tool that helps you **snapshot, version-control, visualize, and rollback** Kubernetes cluster states.  
It integrates with **Git** and **S3** to provide a history of your cluster’s evolution, making debugging, auditing, and recovery easier.
<img width="1536" height="1024" alt="" src="https://github.com/user-attachments/assets/631d77f1-587c-4691-bb5a-10278acc851c" />

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
git clone https://github.com/your-username/kubevc.git
cd kubevc
