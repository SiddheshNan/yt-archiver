import os
import subprocess
import sys
import yaml

APP_NAME = "yt_archiver"
APP_PORT = 8000
BASE_DIR = os.path.dirname(os.path.abspath(__file__))


# def prepare_docker_config():
#     dev_config_path = os.path.join(BASE_DIR, "runtime", "config", "dev.yaml")
#     docker_config_path = os.path.join(
#         BASE_DIR, "runtime", "config", "docker.yaml")

#     print("Preparing docker.yaml based on dev.yaml...")
#     if not os.path.exists(dev_config_path):
#         print(f"Error: {dev_config_path} not found.")
#         sys.exit(1)

#     with open(dev_config_path, "r") as f:
#         config = yaml.safe_load(f)

#     # 1. Modify MongoDB URL to target the host machine from inside Docker
#     if "database" in config and "url" in config["database"]:
#         config["database"]["url"] = config["database"]["url"].replace(
#             "localhost", "host.docker.internal"
#         ).replace("127.0.0.1", "host.docker.internal")

#     # 2. Modify tools to point to the Linux binaries inside the container
#     if "tools" not in config:
#         config["tools"] = {}

#     config["tools"]["ytdlp_path"] = "yt-dlp"  # Installed natively via pip
#     # Uses system ffmpeg installed via apt-get
#     config["tools"]["ffmpeg_path"] = "ffmpeg"

#     with open(docker_config_path, "w") as f:
#         yaml.dump(config, f)
#     print("Successfully generated runtime/config/docker.yaml")


def main():
    # prepare_docker_config()

    print(f"\n[1/3] Building docker image '{APP_NAME}'...")
    build_cmd = f"docker build -t {APP_NAME} ."
    res = subprocess.run(build_cmd, shell=True)
    if res.returncode != 0:
        print("Docker build failed.")
        sys.exit(1)

    print(f"\n[2/3] Cleaning up any existing container named {APP_NAME}...")
    subprocess.run(f"docker rm -f {APP_NAME}",
                   shell=True, stderr=subprocess.DEVNULL)

    print(f"\n[3/3] Running container '{APP_NAME}' on port {APP_PORT}...")
    run_cmd = (
        f'docker run --rm -p {APP_PORT}:{APP_PORT} '
        f'-v "{os.path.join(BASE_DIR, "runtime")}:/app/runtime" '
        f'--name "{APP_NAME}" {APP_NAME}'
    )

    try:
        subprocess.run(run_cmd, shell=True, check=True)
    except KeyboardInterrupt:
        print("\nStopping container...")
        subprocess.run(f"docker rm -f {APP_NAME}",
                       shell=True, stderr=subprocess.DEVNULL)
    except subprocess.CalledProcessError as e:
        print(f"Container exited with error: {e}")


if __name__ == "__main__":
    main()
