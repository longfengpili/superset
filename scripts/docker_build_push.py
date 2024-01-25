import os
import re
import subprocess
import sys


def run_cmd(command: str) -> str:
    return subprocess.getoutput(command)


if len(sys.argv) < 4:
    print(
        "Usage: python docker_build_push.py "
        "<GITHUB_RELEASE_TAG_NAME> <TARGET> <BUILD_PLATFORM>"
    )
    sys.exit(1)

# Assign command line arguments to variables
GITHUB_RELEASE_TAG_NAME = sys.argv[1]
TARGET = sys.argv[2]
BUILD_PLATFORM = sys.argv[3]  # Should be either 'linux/amd64' or 'linux/arm64'


# Common variables
GITHUB_EVENT_NAME = os.getenv("GITHUB_EVENT_NAME")
GITHUB_HEAD_REF = os.getenv("GITHUB_HEAD_REF", "")
GITHUB_REF = os.getenv("GITHUB_REF", "")
TEST_ENV = os.getenv("TEST_ENV")
TEST_ENV = "true"
DOCKERHUB_TOKEN = os.getenv("DOCKERHUB_TOKEN")
DOCKERHUB_USER = os.getenv("DOCKERHUB_USER")
REPO_NAME = "apache/superset"
SHA = run_cmd("git rev-parse HEAD")
DOCKER_ARGS = "--load"
DOCKER_CONTEXT = "."

REFSPEC = ""
LATEST_TAG = ""
TAG = ""
BUILD_TARGET = ""
DEV_TAG = ""
SAFE_BUILD_PLATFORM = ""
PLATFORM_SUFFIX = ""
DOCKER_TAGS = ""
TAG_SUFFIX = ""
TARGET_ARGUMENT = ""
CACHE_REF = ""

if GITHUB_EVENT_NAME == "pull_request":
    REFSPEC = re.sub("[^a-zA-Z0-9]", "-", GITHUB_HEAD_REF)[:40]
    PR_NUM = re.sub("/merge$", "", re.sub("refs/pull/", "", GITHUB_REF))
    LATEST_TAG = f"pr-{PR_NUM}"
elif GITHUB_EVENT_NAME == "release":
    REFSPEC = re.sub("refs/tags/", "", GITHUB_REF)[:40]
    LATEST_TAG = REFSPEC
else:
    REFSPEC = re.sub("[^a-zA-Z0-9]", "-", re.sub("refs/heads/", "", GITHUB_REF))[:40]
    LATEST_TAG = REFSPEC

if REFSPEC == "master":
    LATEST_TAG = "master"

if GITHUB_RELEASE_TAG_NAME:
    output = (
        run_cmd(f"./scripts/tag_latest_release.sh {GITHUB_RELEASE_TAG_NAME} --dry-run")
        or ""
    )

    match = re.search(r"SKIP_TAG=(.*)", output)
    print("-=" * 30)
    print(f"output: {output}")
    print(f"LATEST_TAG: {LATEST_TAG}")
    print("-=" * 30)
    if match and match.group(1) == "SKIP_TAG::false":
        LATEST_TAG = "latest"

if TEST_ENV == "true":
    print(f"LATEST_TAG is {LATEST_TAG}")
    exit(0)

if LATEST_TAG == "master":
    DEV_TAG = f"{REPO_NAME}:latest-dev"
else:
    DEV_TAG = f"{REPO_NAME}:{LATEST_TAG}-dev"

BUILD_ARG = "3.9-slim-bookworm"

# Replace 'linux/amd64' with 'amd' and 'linux/arm64' with 'arm'
SAFE_BUILD_PLATFORM = re.sub(
    "linux/amd64", "amd", re.sub("linux/arm64", "arm", BUILD_PLATFORM)
)

if BUILD_PLATFORM == "linux/arm64":
    PLATFORM_SUFFIX = "-arm"

VERBOSE_TAG = f"{REPO_NAME}:{SHA}-{TARGET}-{SAFE_BUILD_PLATFORM}-{BUILD_ARG}"

if TARGET == "dev":
    TAG = "dev"
    BUILD_TARGET = "dev"
elif TARGET == "lean":
    TAG = "lean"
    BUILD_TARGET = "lean"
elif TARGET == "lean310":
    BUILD_TARGET = "lean"
    TAG = "py310"
    BUILD_ARG = "3.10-slim-bookworm"
elif TARGET == "websocket":
    BUILD_TARGET = ""
    TAG = "websocket"
    DOCKER_CONTEXT = "superset-websocket"
elif TARGET == "dockerize":
    BUILD_TARGET = ""
    TAG = "dockerize"
    DOCKER_CONTEXT = "-f dockerize.Dockerfile ."
else:
    print(f"Invalid TARGET: {TARGET}")
    exit(1)

if TAG:
    TAG_SUFFIX = f"-{TAG}"

DOCKER_TAGS = f"-t {VERBOSE_TAG}"
DOCKER_TAGS += f" -t {REPO_NAME}:{SHA}{TAG_SUFFIX}{PLATFORM_SUFFIX}"
DOCKER_TAGS += f" -t {REPO_NAME}:{REFSPEC}{TAG_SUFFIX}{PLATFORM_SUFFIX}"
DOCKER_TAGS += f" -t {REPO_NAME}:{LATEST_TAG}{TAG_SUFFIX}{PLATFORM_SUFFIX}"

if GITHUB_EVENT_NAME == "push" and GITHUB_REF == "refs/heads/master" and TAG == "dev":
    DOCKER_TAGS += f" -t {REPO_NAME}:{TAG}{PLATFORM_SUFFIX}"
elif GITHUB_EVENT_NAME == "release":
    DOCKER_TAGS += f" -t {REPO_NAME}:{TAG}{PLATFORM_SUFFIX}"
    if TAG == "lean" and BUILD_PLATFORM == "linux/amd64":
        DOCKER_TAGS += f" -t {REPO_NAME}"

if not DOCKERHUB_TOKEN:
    print("Skipping Docker push")
    DOCKER_ARGS = "--load"
else:
    run_cmd("docker logout")
    run_cmd(f"docker login --username {DOCKERHUB_USER} --password {DOCKERHUB_TOKEN}")
    DOCKER_ARGS = "--push"

if BUILD_TARGET:
    TARGET_ARGUMENT = f"--target {BUILD_TARGET}"

CACHE_REF = f"{REPO_NAME}-cache:{TARGET}-{BUILD_ARG}"
CACHE_REF = re.sub(r"\.", "", CACHE_REF)
CACHE_FROM_ARG = f"--cache-from=type=registry,ref={CACHE_REF}"
CACHE_TO_ARG = ""
if DOCKERHUB_TOKEN:
    CACHE_TO_ARG = f"--cache-to=type=registry,mode=max,ref={CACHE_REF}"

docker_build_command = f"""\
docker buildx build \\
    {TARGET_ARGUMENT} \\
    {DOCKER_ARGS} \\
    {DOCKER_TAGS} \\
    {CACHE_FROM_ARG} \\
    {CACHE_TO_ARG} \\
    --platform {BUILD_PLATFORM} \\
    --label sha={SHA} \\
    --label built_at=$(date) \\
    --label target={TARGET} \\
    --label base={BUILD_ARG} \\
    --label build_actor={os.getenv('GITHUB_ACTOR')} \\
    {f'--build-arg PY_VER={BUILD_ARG}' if BUILD_ARG else ''} \\
    {DOCKER_CONTEXT}\
"""

print("Executing Docker Build Command:")
print(docker_build_command)
stdout = run_cmd(docker_build_command)
print(stdout)
