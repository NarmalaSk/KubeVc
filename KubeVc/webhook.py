from flask import Flask, request, jsonify, Response
import os
import subprocess
import time
from datetime import datetime
import boto3
import json
import yaml  # PyYAML library

app = Flask(__name__, static_folder="static")
STATE = {"backend": "S3"}
os.makedirs(app.static_folder, exist_ok=True)

# ---- Load KubeVc.yaml ----
CONFIG_FILE = "KubeVc.yaml"
if not os.path.exists(CONFIG_FILE):
    raise FileNotFoundError(f"{CONFIG_FILE} not found!")

with open(CONFIG_FILE, "r") as f:
    config = yaml.safe_load(f)

S3_BUCKET = config["s3"]["bucket"]
S3_REGION = config["s3"]["region"]
S3_ACCESS_KEY = config["s3"]["access_key"]
S3_SECRET_KEY = config["s3"]["secret_key"]

KUBECONFIG_PATH = config["kubeconfig"]["path"]

# ---- S3 client ----
s3 = boto3.client(
    "s3",
    aws_access_key_id=S3_ACCESS_KEY,
    aws_secret_access_key=S3_SECRET_KEY,
    region_name=S3_REGION
)

# ---- Helpers ----
def _now():
    ts = time.time()
    return ts, datetime.utcfromtimestamp(ts).isoformat() + "Z"

def collect_changed_yaml(payload: dict):
    files = []
    for c in payload.get("commits", []):
        files.extend(c.get("added", []))
        files.extend(c.get("modified", []))
        files.extend(c.get("removed", []))
    return [f for f in files if f.lower().endswith((".yaml", ".yml"))]

def run_cluster_diagram(changed_yaml_files):
    diagram_path = os.path.join(app.static_folder, "cluster.png")
    script_path = os.path.join(os.getcwd(), "cluster_diagram.py")
    if os.path.exists(script_path):
        try:
            subprocess.run(["python3", script_path, *changed_yaml_files], check=True)
            return diagram_path
        except Exception as e:
            print("Error running cluster_diagram.py:", e)
            return None
    return None

def push_to_s3(commit_hash, repo_name, changed_yaml, diagram_path):
    metadata = {
        "commit_hash": commit_hash,
        "repo_name": repo_name,
        "changed_yaml": changed_yaml,
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }
    key_prefix = f"{repo_name}/{commit_hash}"

    if diagram_path and os.path.exists(diagram_path):
        s3.upload_file(diagram_path, S3_BUCKET, f"{key_prefix}/cluster.png")

    s3.put_object(
        Bucket=S3_BUCKET,
        Key=f"{key_prefix}/metadata.json",
        Body=json.dumps(metadata, indent=2).encode("utf-8"),
        ContentType="application/json"
    )

    return metadata

# ---- Webhook endpoint ----
@app.route("/webhook", methods=["POST"])
def webhook():
    payload = request.get_json(silent=True) or {}
    commit_hash = payload.get("after") or (payload.get("head_commit") or {}).get("id")
    repo_name = payload.get("repository", {}).get("name", "unknown-repo")
    STATE["last_commit"] = commit_hash

    yaml_files = collect_changed_yaml(payload)
    if yaml_files:
        diagram_path = run_cluster_diagram(yaml_files)
        meta = push_to_s3(commit_hash, repo_name, yaml_files, diagram_path)
        img_url = f"https://{S3_BUCKET}.s3.{S3_REGION}.amazonaws.com/{repo_name}/{commit_hash}/cluster.png?ts={meta['timestamp']}"
        return jsonify({
            "ok": True,
            "message": "YAML change detected; diagram updated + uploaded to S3",
            "changed_yaml": yaml_files,
            "diagram_url": img_url
        }), 200
    else:
        return jsonify({"ok": True, "message": "no YAML changes detected"}), 200

# ---- Dashboard ----
@app.route("/dashboard", methods=["GET"])
def dashboard():
    objs = s3.list_objects_v2(Bucket=S3_BUCKET, Prefix="", Delimiter="/")
    repos = [p["Prefix"].strip("/") for p in objs.get("CommonPrefixes", [])]
    cards_html = ""

    for repo_name in repos:
        repo_objs = s3.list_objects_v2(Bucket=S3_BUCKET, Prefix=f"{repo_name}/")
        commits = set()
        for obj in repo_objs.get("Contents", []):
            parts = obj["Key"].split("/")
            if len(parts) >= 2:
                commits.add(parts[1])

        for commit in sorted(commits, reverse=True):
            meta_key = f"{repo_name}/{commit}/metadata.json"
            try:
                meta_obj = s3.get_object(Bucket=S3_BUCKET, Key=meta_key)
                meta = json.loads(meta_obj["Body"].read())
            except:
                meta = {"commit_hash": commit, "changed_yaml": [], "timestamp": "N/A"}

            img_url = f"https://{S3_BUCKET}.s3.{S3_REGION}.amazonaws.com/{repo_name}/{commit}/cluster.png?ts={meta['timestamp']}"
            cards_html += f"""
            <div class='card'>
                <h3>Repo: {repo_name}</h3>
                <p><b>Commit:</b> {meta['commit_hash']}</p>
                <p><b>Timestamp:</b> {meta['timestamp']}</p>
                <p><b>Changed YAMLs:</b> {', '.join(meta.get('changed_yaml', []))}</p>
                <div class='diagram'><img src='{img_url}' alt='Cluster Diagram' /></div>
            </div>
            """

    body = f"<div class='wrap'><h1>K8s Git Cluster State</h1>{cards_html or '<p>No diagrams found in S3 yet.</p>'}</div>"
    return Response(_html_base(body, dashboard=True), mimetype="text/html")

def _html_base(body: str, dashboard=False) -> str:
    if dashboard:
        bg_color = "#0f172a"
        card_bg = "#1e293b"
        text_color = "#e2e8f0"
    else:
        bg_color = "#f0f4f8"
        card_bg = "#fff"
        text_color = "#0f172a"

    return f"""
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <title>{'K8s Git Cluster State' if dashboard else 'KubeVC'}</title>
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <style>
    body {{ font-family: Inter, sans-serif; background:{bg_color}; color:{text_color}; }}
    .wrap {{ max-width:1040px; margin:0 auto; padding:20px; }}
    .card {{ background:{card_bg}; border-radius:12px; padding:16px; margin-bottom:16px; box-shadow:0 4px 12px rgba(0,0,0,0.3); }}
    .card h3 {{ margin-top:0; }}
    .diagram img {{ max-width:100%; height:auto; border-radius:8px; margin-top:8px; }}
    a {{ color:#38bdf8; text-decoration:none; }}
    a:hover {{ text-decoration:underline; }}
  </style>
</head>
<body>
{body}
</body>
</html>
"""

@app.route("/", methods=["GET"])
def home():
    body = "<h1>Welcome to KubeVC</h1><p>Go to <a href='/dashboard'>Dashboard</a> to see cluster state</p>"
    return Response(_html_base(body), mimetype="text/html")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)

