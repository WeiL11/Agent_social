"""Deploy backend + frontend to Hugging Face Spaces (Docker).

  python3 deploy/hf_deploy.py            # upload/refresh both spaces
  python3 deploy/hf_deploy.py --secrets  # (re)apply space secrets only

Stack: Supabase (Postgres) + HF Space wei25/agent-social-api (FastAPI, port 8000)
+ HF Space wei25/agent-social-web (Next.js, port 3000). Scaling later = point the
same Docker image at any host; the DB never moves.
"""

import os
import sys
import tempfile
from pathlib import Path

from huggingface_hub import HfApi

USER = "wei25"
API_SPACE = f"{USER}/agent-social-api"
WEB_SPACE = f"{USER}/agent-social-web"
ROOT = Path(__file__).resolve().parent.parent

API_README = """---
title: Agent Social API
emoji: 🪄
colorFrom: purple
colorTo: indigo
sdk: docker
app_port: 8000
pinned: false
---
FastAPI backend for AI Persona Game. DB = Supabase Postgres (secret DATABASE_URL).
"""

WEB_README = """---
title: Agent Social
emoji: 🧚
colorFrom: purple
colorTo: pink
sdk: docker
app_port: 3000
pinned: false
---
Next.js frontend for AI Persona Game. Talks to agent-social-api.
"""

# fnmatch patterns ('*' also crosses '/'): keep heavyweight/secret paths out.
IGNORE = ["*.pyc", "*__pycache__*", "*.venv*", "*node_modules*", "*.next*",
          "*.pytest_cache*", "*.ruff_cache*", ".env", "*.env.local", "*.DS_Store"]


def upload(api: HfApi, space: str, folder: Path, readme: str) -> None:
    # HF now requires PRO to CREATE new Docker Spaces; ours already exist, so
    # only create when missing (and surface a clear message if that fails).
    if not api.repo_exists(space, repo_type="space"):
        api.create_repo(space, repo_type="space", space_sdk="docker")
    api.upload_folder(repo_id=space, repo_type="space", folder_path=str(folder),
                      ignore_patterns=IGNORE, commit_message="deploy")
    with tempfile.NamedTemporaryFile("w", suffix=".md", delete=False) as f:
        f.write(readme)
    api.upload_file(repo_id=space, repo_type="space", path_or_fileobj=f.name,
                    path_in_repo="README.md", commit_message="space metadata")
    os.unlink(f.name)
    print(f"  ✓ {space} uploaded")


def set_secrets(api: HfApi) -> None:
    db_url = os.environ.get("SUPABASE_DB_URL", "")
    api.add_space_secret(API_SPACE, "CORS_ORIGINS",
                         f"https://{USER}-agent-social-web.hf.space")
    api.add_space_variable(API_SPACE, "ENVIRONMENT", "production")
    if db_url:
        api.add_space_secret(API_SPACE, "DATABASE_URL", db_url)
        print("  ✓ DATABASE_URL set")
    else:
        print("  ⚠ SUPABASE_DB_URL env not set — skipped DATABASE_URL "
              "(API will not boot until it is set)")
    gem = os.environ.get("GEMINI_API_KEY", "")
    if gem:
        api.add_space_secret(API_SPACE, "GEMINI_API_KEY", gem)
        print("  ✓ GEMINI_API_KEY set")
    print(f"  ✓ secrets/vars applied to {API_SPACE}")


def main() -> None:
    api = HfApi()
    if "--secrets" in sys.argv:
        set_secrets(api)
        return
    print("uploading backend…")
    upload(api, API_SPACE, ROOT / "backend", API_README)
    print("uploading frontend…")
    upload(api, WEB_SPACE, ROOT / "frontend", WEB_README)
    set_secrets(api)
    print(f"""
done.
  API: https://{USER}-agent-social-api.hf.space
  WEB: https://{USER}-agent-social-web.hf.space
""")


if __name__ == "__main__":
    main()
