import os


os.environ["CHALLENGE_ERRORS"] = "False"

HOST_CONFIG_FILE_PATH = "github/host_config.json"
# Updated API endpoints to match the new backend structure
CHALLENGE_CONFIG_VALIDATION_URL = "/api/v1/challenges/challenge_host_team/{}/validate_challenge_config/"
CHALLENGE_CREATE_OR_UPDATE_URL = "/api/v1/challenges/challenge_host_team/{}/create_or_update_github_challenge/"
# One-way sync endpoints (EvalAI → GitHub)
GITHUB_SYNC_STATUS_URL = "/api/v1/challenges/{}/github/sync_status/"
EVALAI_ERROR_CODES = [400, 401, 406]
API_HOST_URL = "https://eval.ai"
IGNORE_DIRS = [
    ".git",
    ".github",
    "code_upload_challenge_evaluation",
    "remote_challenge_evaluation",
]
IGNORE_FILES = [
    ".gitignore",
    "challenge_config.zip",
    "README.md",
    "run.sh",
    "submission.json",
]
CHALLENGE_ZIP_FILE_PATH = "challenge_config.zip"
GITHUB_REPOSITORY = os.getenv("GITHUB_REPOSITORY")
# GitHub branch - try multiple environment variables that might contain the branch name
GITHUB_BRANCH = os.getenv("GITHUB_REF_NAME") or os.getenv("GITHUB_BRANCH") or os.getenv("GITHUB_REF", "refs/heads/main").replace("refs/heads/", "") or "main"
GITHUB_EVENT_NAME = os.getenv("GITHUB_EVENT_NAME")
VALIDATION_STEP = os.getenv("IS_VALIDATION")

# Debug: Print the values to help troubleshoot
print(f"DEBUG: GITHUB_REPOSITORY = {GITHUB_REPOSITORY}")
print(f"DEBUG: GITHUB_BRANCH = {GITHUB_BRANCH}")
print(f"DEBUG: GITHUB_EVENT_NAME = {GITHUB_EVENT_NAME}")
print(f"DEBUG: VALIDATION_STEP = {VALIDATION_STEP}")
