from pathlib import Path
from huggingface_hub import create_repo, Repository
import tempfile
import subprocess
import os
import shutil
import logging

logger = logging.getLogger(__name__)

def copy_recursive(source_base_path, target_base_path):
    """Copy directory recursively and overwrite existing files."""
    for item in source_base_path.iterdir():
        traget_path = target_base_path / item.name
        if item.is_dir():
            traget_path.mkdir(exist_ok=True)
            copy_recursive(item, traget_path)
        else:
            shutil.copy(item, traget_path)


def push_module_to_hub(module_path, type, token):
    module_name = module_path.stem
    org = f"evaluate-{type}"
    
    repo_url = create_repo(module_name, organization=org, repo_type="space", space_sdk="gradio", exist_ok=True, token=token)    
    repo_path = Path(tempfile.mkdtemp())
    
    subprocess.run(
        f"git clone {repo_url}".split(),
        stderr=subprocess.PIPE,
        stdout=subprocess.PIPE,
        check=True,
        encoding="utf-8",
        cwd=repo_path,
        env=os.environ.copy(),
    )

    repo = Repository(local_dir=repo_path / module_name, token=token)
    
    copy_recursive(module_path, repo_path / module_name)
    
    repo.git_add()
    try:
        repo.git_commit(f"Update Space (evaluate main: {commit_hash[:8]})")
        repo.git_push()
        logger.info(f"Module '{module_name}' pushed to the hub")
    except OSError:
        logger.info(f"Module '{module_name}' already up to date.")
    shutil.rmtree(repo_path)


if __name__ == "__name__":
    evaluation_paths = ["metrics", "comparisons", "measurements"]
    evaluation_types = ["metric", "comparison", "measurement"]

    token = os.getenv("HF_TOKEN")
    evaluate_lib_path = Path(os.getenv("EVALUATE_LIB_PATH"))
    commit_hash = os.getenv("GIT_HASH")

    for type, dir in zip(evaluation_types, evaluation_paths):
        if (evaluate_lib_path/dir).exists():
            for module_path in (evaluate_lib_path/dir).iterdir():
                if module_path.is_dir():
                    push_module_to_hub(module_path, type, token, commit_hash)
        else:
            logger.warning(f"No folder {str(evaluate_lib_path/dir)} for {type} found.")