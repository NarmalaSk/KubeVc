#!/usr/bin/env python3
import os
import sys
import yaml
import boto3
import subprocess
from pathlib import Path

CONFIG_FILE = Path.home() / "kubevc.yaml"

def print_help():
    help_text = """
KubeVC CLI - Kubernetes Git Cluster Visualization

Usage:
  kubevc configure   Configure S3 credentials and kubeconfig path
  kubevc start       Start the KubeVC dashboard UI
  kubevc help        Show this help message
"""
    print(help_text)

def configure():
    print("Configuring KubeVC...")

    access_key = input("Enter S3 Access Key ID: ").strip()
    secret_key = input("Enter S3 Secret Access Key: ").strip()
    bucket = input("Enter S3 Bucket Name: ").strip()
    region = input("Enter S3 Region (default: ap-south-1): ").strip() or "ap-south-1"

    kube_path = input("Enter Kubeconfig path (default ~/.kube/config): ").strip() or str(Path.home() / ".kube/config")

    config_data = {
        "s3": {
            "access_key_id": access_key,
            "secret_access_key": secret_key,
            "bucket": bucket,
            "region": region
        },
        "kube": {
            "config_path": kube_path
        }
    }

    with open(CONFIG_FILE, "w") as f:
        yaml.dump(config_data, f)

    print(f"Configuration saved to {CONFIG_FILE}")

def start():
    if not CONFIG_FILE.exists():
        print("Configuration not found. Run `kubevc configure` first.")
        sys.exit(1)

    with open(CONFIG_FILE) as f:
        config_data = yaml.safe_load(f)

    # Validate S3 access
    try:
        s3 = boto3.client(
            "s3",
            aws_access_key_id=config_data["s3"]["access_key_id"],
            aws_secret_access_key=config_data["s3"]["secret_access_key"],
            region_name=config_data["s3"]["region"]
        )
        s3.list_buckets()
        print(f"S3 access validated for bucket: {config_data['s3']['bucket']}")
    except Exception as e:
        print("Failed to access S3:", e)
        sys.exit(1)

    # Validate kubeconfig path
    kube_path = os.path.expanduser(config_data["kube"]["config_path"])
    if not os.path.exists(kube_path):
        print(f"Kubeconfig not found at {kube_path}")
        sys.exit(1)

    print("Starting KubeVC UI...")
    # Assuming your Flask app is in webhook.py or app.py
    subprocess.run(["python3", "webhook.py"])

def main():
    if len(sys.argv) < 2:
        print_help()
        sys.exit(0)

    cmd = sys.argv[1].lower()
    if cmd == "configure":
        configure()
    elif cmd == "start":
        start()
    elif cmd == "help":
        print_help()
    else:
        print(f"Unknown command: {cmd}")
        print_help()
        sys.exit(1)

if __name__ == "__main__":
    main()

