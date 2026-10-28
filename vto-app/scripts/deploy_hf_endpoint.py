"""python scripts/deploy_hf_endpoint.py --idm-vton-dir /path/to/cloned/IDM-VTON
Needs HUGGINGFACE_API_TOKEN (write access). Prints the endpoint URL for .env (HF_ENDPOINT_URL)."""
import argparse, os, shutil, tempfile
from huggingface_hub import HfApi, create_inference_endpoint

ap = argparse.ArgumentParser()
ap.add_argument("--idm-vton-dir", required=True)
ap.add_argument("--repo", default="vto-tryon-handler")
ap.add_argument("--name", default="vto-tryon")
ap.add_argument("--instance", default="nvidia-a10g")
a = ap.parse_args()
tok = os.environ["HUGGINGFACE_API_TOKEN"]
api = HfApi(token=tok)
repo_id = api.create_repo(a.repo, private=True, exist_ok=True).repo_id
with tempfile.TemporaryDirectory() as t:
    for d in ("src", "gradio_demo", "configs", "preprocess"):
        s = os.path.join(a.idm_vton_dir, d)
        if os.path.isdir(s): shutil.copytree(s, os.path.join(t, d))
    for f in ("handler.py", "requirements.txt"):
        shutil.copy(os.path.join("hf_endpoint", f), t)
    ck = os.path.join(a.idm_vton_dir, "ckpt")
    if os.path.isdir(ck): shutil.copytree(ck, os.path.join(t, "ckpt"))
    api.upload_folder(repo_id=repo_id, folder_path=t)
ep = create_inference_endpoint(a.name, repository=repo_id, framework="pytorch", task="custom",
    accelerator="gpu", vendor="aws", region="us-east-1", type="protected",
    instance_size="x1", instance_type=a.instance, min_replica=0, max_replica=1,
    scale_to_zero_timeout=15, token=tok)
ep.wait()
print("HF_ENDPOINT_URL=" + ep.url)
