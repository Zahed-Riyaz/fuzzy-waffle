import http
import json
import os
import requests
import sys
import urllib3
from urllib.parse import urlparse

# --- add near the top of the file (after imports) ----------------------------
import logging
import http.client as _http_client

def _mask(token: str, keep=6):
    if not token:
        return "<empty>"
    t = token.strip()
    return t[:keep] + "…" + t[-keep:] if len(t) > 2*keep else "<len:{}>".format(len(t))

def enable_verbose_http(condition: bool):
    """Turn on very noisy HTTP logs only when asked."""
    if not condition:
        return
    _http_client.HTTPConnection.debuglevel = 1
    logging.basicConfig(level=logging.DEBUG)
    logging.getLogger("urllib3").setLevel(logging.DEBUG)
    logging.getLogger("requests").setLevel(logging.DEBUG)

# flip this by env var if you like
DEBUG = os.getenv("EVALAI_SYNC_DEBUG", "0") in ("1", "true", "True", "YES", "yes")
enable_verbose_http(DEBUG)

# Import config again by module so we can print its file path
import config as _cfg
# -----------------------------------------------------------------------------

from config import *
from utils import (
    add_pull_request_comment,
    check_for_errors,
    check_if_merge_or_commit,
    check_if_pull_request,
    create_challenge_zip_file,
    create_github_repository_issue,
    get_request_header,
    load_host_configs,
    validate_token,
)

sys.dont_write_bytecode = True

GITHUB_CONTEXT = json.loads(os.getenv("GITHUB_CONTEXT", "{}"))
GITHUB_AUTH_TOKEN = os.getenv("GITHUB_AUTH_TOKEN")
if not GITHUB_AUTH_TOKEN:
    print(
        "Please add your github access token to the repository secrets with the name AUTH_TOKEN"
    )
    sys.exit(1)

# Clean up the GitHub token (remove any whitespace/newlines)
GITHUB_AUTH_TOKEN = GITHUB_AUTH_TOKEN.strip()
HOST_AUTH_TOKEN = None
CHALLENGE_HOST_TEAM_PK = None
EVALAI_HOST_URL = None


def is_localhost_url(url):
    """
    Check if the provided URL is a localhost URL
    
    Arguments:
        url {str}: The URL to check
    
    Returns:
        bool: True if it's a localhost URL, False otherwise
    """
    localhost_indicators = [
        "127.0.0.1",
        "localhost", 
        "0.0.0.0",
        "host.docker.internal"
    ]
    return any(indicator in url.lower() for indicator in localhost_indicators)


def get_runner_info():
    """Return a minimal dict about the runner (only what we need for error msgs)."""
    return {
        "is_self_hosted": os.getenv("RUNNER_ENVIRONMENT") != "github-hosted",
    }


def configure_requests_for_localhost():
    """
    Configure requests and urllib3 for localhost development servers
    This disables SSL warnings for self-signed certificates commonly used in development
    """
    # Disable SSL warnings for localhost development
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    print("INFO: SSL verification disabled for localhost development server")


if __name__ == "__main__":
    if GITHUB_CONTEXT["event"]["head_commit"]["message"].startswith("evalai_bot"):
        print("Sync from Evalai")
        sys.exit(0)

    
    configs = load_host_configs(HOST_CONFIG_FILE_PATH)
    if configs:
        HOST_AUTH_TOKEN = configs[0]
        CHALLENGE_HOST_TEAM_PK = configs[1]
        EVALAI_HOST_URL = configs[2]
    else:
        sys.exit(1)

    # After: configs = load_host_configs(HOST_CONFIG_FILE_PATH)
    ### DEBUG: show exactly which config module & values are in play
    print("\n🐞 CONFIG MODULE PATH:", getattr(_cfg, "__file__", "<unknown>"))
    print("🐞 HOST_CONFIG_FILE_PATH:", HOST_CONFIG_FILE_PATH)
    print("🐞 VALIDATION_STEP:", repr(VALIDATION_STEP))
    print("🐞 CHALLENGE_CONFIG_VALIDATION_URL:", repr(CHALLENGE_CONFIG_VALIDATION_URL))
    print("🐞 CHALLENGE_CREATE_OR_UPDATE_URL:", repr(CHALLENGE_CREATE_OR_UPDATE_URL))
    print("🐞 GITHUB_REPOSITORY:", repr(GITHUB_REPOSITORY))
    print("🐞 HOST_AUTH_TOKEN (masked):", _mask(HOST_AUTH_TOKEN))
    print("🐞 GITHUB_AUTH_TOKEN (masked):", _mask(GITHUB_AUTH_TOKEN))
    print("🐞 CHALLENGE_HOST_TEAM_PK:", CHALLENGE_HOST_TEAM_PK)

    # Check if we're using a localhost server and configure accordingly
    is_localhost = is_localhost_url(EVALAI_HOST_URL)
    runner_info = get_runner_info()
    
    print(f"\n🌐 EvalAI Server: {EVALAI_HOST_URL}")
    print(f"🏠 Localhost Mode: {is_localhost}")
    print(f"🤖 Self-hosted Runner: {runner_info['is_self_hosted']}")
    
    if is_localhost:
        configure_requests_for_localhost()
        print(f"INFO: Using localhost server: {EVALAI_HOST_URL}")
        
    # Build path safely to avoid accidental double '//' or missing '/'
    base = (EVALAI_HOST_URL or "").rstrip("/")
    if VALIDATION_STEP == "True":
        print(f"\n🔍 VALIDATION MODE: Validating challenge configuration...")
        rel = CHALLENGE_CONFIG_VALIDATION_URL.format(CHALLENGE_HOST_TEAM_PK).lstrip("/")
        mode = "validation"
    else:
        print(f"\n🚀 CREATION MODE: Creating/updating challenge...")
        rel = CHALLENGE_CREATE_OR_UPDATE_URL.format(CHALLENGE_HOST_TEAM_PK).lstrip("/")
        mode = "create/update"

    url = f"{base}/{rel}"

    ### DEBUG: print the *exact* URL we will hit and sanity-check common mistakes
    print(f"\n🐞 URL BUILD ({mode}): base={base!r}, rel={rel!r}")
    print("🐞 Final URL:", url)
    if "/challenge/challenge_host_team/" in url:
        print("⚠️  DETECTED suspicious segment '/challenge/challenge_host_team/' in URL")

    print(f"📡 API Endpoint: {url}")
    
    ### DEBUG: quick OPTIONS probe on likely variants
    candidates = [
        url,
        url.replace("/challenge/challenge_host_team/", "/challenge_host_team/"),
        url[:-1] if url.endswith("/") else url + "/",
    ]
    print("\n🐞 Preflight OPTIONS on candidates:")
    for u in dict.fromkeys(candidates):  # de-dup while preserving order
        try:
            r = requests.options(u, verify=not is_localhost, timeout=10)
            print(f"   • {u}  ->  {r.status_code}  Allow={r.headers.get('Allow')}")
        except Exception as e:
            print(f"   • {u}  ->  EXCEPTION: {e}")
    
    headers = get_request_header(HOST_AUTH_TOKEN)

    # Creating the challenge zip file and storing in a dict to send to EvalAI
    print(f"\n📦 Creating challenge configuration package...")
    create_challenge_zip_file(CHALLENGE_ZIP_FILE_PATH, IGNORE_DIRS, IGNORE_FILES)

    # Configure SSL verification based on whether we're using localhost
    verify_ssl = not is_localhost
    print(f"🔒 SSL Verification: {'Disabled (localhost)' if not verify_ssl else 'Enabled'}")

    from requests import Session, Request
    sess = Session()

    # Prepare once, so we can inspect
    req = Request(
        "POST",
        url,
        headers=headers,
        data={"GITHUB_REPOSITORY": GITHUB_REPOSITORY, "GITHUB_AUTH_TOKEN": GITHUB_AUTH_TOKEN},
        files={"zip_configuration": open(CHALLENGE_ZIP_FILE_PATH, "rb")},
    )
    prepped = sess.prepare_request(req)

    # DEBUG dump (mask sensitive)
    print("\n🐞 Prepared Request")
    print("   Method:", prepped.method)
    print("   URL   :", prepped.url)
    # headers with masked tokens
    safe_headers = dict(prepped.headers)
    for k in ("Authorization", "authorization"):
        if k in safe_headers:
            safe_headers[k] = safe_headers[k].split(" ")[0] + " " + _mask(safe_headers[k].split(" ", 1)[1])
    print("   Headers:", safe_headers)
    # Don't print raw body (multipart). Show part names instead:
    print("   Multipart parts:", ["zip_configuration", "GITHUB_REPOSITORY", "GITHUB_AUTH_TOKEN"])

    print(f"\n🌐 Sending request to EvalAI server...")
    response = sess.send(prepped, verify=not is_localhost)

    try:
        if response.status_code != http.HTTPStatus.OK and response.status_code != http.HTTPStatus.CREATED:
            response.raise_for_status()
        else:
            print("\n✅ Challenge processed successfully on EvalAI")
            
    except requests.exceptions.ConnectionError as conn_err:
        # Handle connection errors specifically for localhost
        if is_localhost:
            error_message = "\n🚨 LOCALHOST SERVER CONNECTION FAILED\n"
            error_message += f"❌ Could not connect to your localhost EvalAI server at: {EVALAI_HOST_URL}\n"
            error_message += "\n📋 Please check the following:\n"
            error_message += "   1. Is your EvalAI server running?\n"
            error_message += f"   2. Is it accessible at {EVALAI_HOST_URL}?\n"
            error_message += "   3. Check server logs for any startup errors\n"
            
            if runner_info['is_self_hosted']:
                error_message += "\n💡 Self-hosted runner troubleshooting:\n"
                error_message += "   • Verify runner can reach the server: ping/curl test\n"
                error_message += "   • Check network configuration and firewall settings\n"
                error_message += "   • Ensure server is binding to correct interface (0.0.0.0 vs 127.0.0.1)\n"
            else:
                error_message += "\n⚠️  CONFIGURATION ISSUE:\n"
                error_message += "   You're using a GitHub-hosted runner with a localhost URL.\n"
                error_message += "   GitHub-hosted runners cannot access your local machine.\n"
                error_message += "   Please set up a self-hosted runner for localhost development.\n"
                
            error_message += "\n💡 To start your local server, typically run:\n"
            error_message += "   python manage.py runserver 0.0.0.0:8888\n"
            error_message += f"\nOriginal error: {conn_err}"
        else:
            error_message = f"\nConnection failed to EvalAI server: {conn_err}"
        
        print(error_message)
        os.environ["CHALLENGE_ERRORS"] = error_message

        # Fail the job so CI visibly reports the problem
        sys.exit(1)

    except requests.exceptions.HTTPError as err:
        try:
            if response.status_code not in (http.HTTPStatus.OK, http.HTTPStatus.CREATED):
                # print detailed server response before raising
                ct = response.headers.get("Content-Type")
                print(f"\n🐞 Server response: status={response.status_code} {response.reason}  Content-Type={ct}")
                body = response.text
                print("🐞 Response body (first 2k chars):\n", body[:2000])
                response.raise_for_status()
            else:
                print("\n✅ Challenge processed successfully on EvalAI")
        except requests.exceptions.HTTPError as err:
            # If 404 and the common double-segment bug is present, auto-retry once
            if response.status_code == 404 and "/challenge/challenge_host_team/" in url:
                fixed_url = url.replace("/challenge/challenge_host_team/", "/challenge_host_team/")
                print(f"\n🐞 Auto-retrying with fixed URL: {fixed_url}")
                retry = sess.send(sess.prepare_request(Request(
                    "POST", fixed_url, headers=headers,
                    data={"GITHUB_REPOSITORY": GITHUB_REPOSITORY, "GITHUB_AUTH_TOKEN": GITHUB_AUTH_TOKEN},
                    files={"zip_configuration": open(CHALLENGE_ZIP_FILE_PATH, "rb")},
                )), verify=not is_localhost)
                print("🐞 Retry status:", retry.status_code, retry.reason)
                if retry.status_code not in (http.HTTPStatus.OK, http.HTTPStatus.CREATED):
                    print("🐞 Retry response (first 2k):\n", retry.text[:2000])
                    retry.raise_for_status()
                else:
                    print("\n✅ Challenge processed successfully on EvalAI (after retry)")
            else:
                if response.status_code in EVALAI_ERROR_CODES:
                    is_token_valid = validate_token(response.json())
                    if is_token_valid:
                        error = response.json()["error"]
                        error_message = "\nFollowing errors occurred while validating the challenge config:\n{}".format(
                            error
                        )
                        print(error_message)
                        os.environ["CHALLENGE_ERRORS"] = error_message
                else:
                    print(
                        "\nFollowing errors occurred while validating the challenge config: {}".format(
                            err
                        )
                    )
                    os.environ["CHALLENGE_ERRORS"] = str(err)

    except Exception as e:
        if VALIDATION_STEP == "True":
            error_message = "\nFollowing errors occurred while validating the challenge config: {}".format(
                e
            )
            print(error_message)
            os.environ["CHALLENGE_ERRORS"] = error_message
        else:
            error_message = "\nFollowing errors occurred while processing the challenge config: {}".format(
                e
            )
            print(error_message)
            os.environ["CHALLENGE_ERRORS"] = error_message



    is_valid, errors = check_for_errors()
    if not is_valid:
        # Check if this is a localhost connection error - don't create GitHub issues for expected localhost failures
        is_localhost_connection_error = (
            is_localhost and 
            errors and 
            ("Connection refused" in errors or "LOCALHOST SERVER CONNECTION FAILED" in errors)
        )
        
        # Also check if this is a GitHub-hosted runner trying to access localhost
        is_github_hosted_localhost_error = (
            is_localhost and 
            not runner_info['is_self_hosted'] and
            errors and
            "Connection" in errors
        )
        
        if is_localhost_connection_error or is_github_hosted_localhost_error:
            print("\nℹ️  Localhost connection error detected. Skipping GitHub issue creation.")
            if is_github_hosted_localhost_error:
                print("   This is expected when using GitHub-hosted runners with localhost URLs.")
                print("   Please configure a self-hosted runner for local development.")
            else:
                print("   This is expected when your local EvalAI server isn't running.")
                
            # Fail the job so CI visibly reports the problem
            sys.exit(1)

        elif VALIDATION_STEP == "True" and check_if_pull_request():
            pr_number = GITHUB_CONTEXT.get("event", {}).get("number")
            if not pr_number:
                print("⚠️  Warning: Could not get PR number from GITHUB_CONTEXT")
                print("   Skipping pull request comment creation")
            else:
                add_pull_request_comment(
                    GITHUB_AUTH_TOKEN,
                    os.path.basename(GITHUB_REPOSITORY),
                    pr_number,
                    errors,
                )
        else:
            issue_title = (
                "Following errors occurred while validating the challenge config:"
            )
            repo_name = os.path.basename(GITHUB_REPOSITORY) if GITHUB_REPOSITORY else ""
            create_github_repository_issue(
                GITHUB_AUTH_TOKEN,
                repo_name,
                issue_title,
                errors,
            )
            print(
                    "\nExiting the {} script after failure\n".format(
                        os.path.basename(__file__)
                    )
                )
            sys.exit(1)

    print("\nExiting the {} script after success\n".format(os.path.basename(__file__)))
