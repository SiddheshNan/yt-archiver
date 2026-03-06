import os
import subprocess
import sys
import yaml

APP_NAME = "yt_archiver"
APP_PORT = 8000
BASE_DIR = os.path.dirname(os.path.abspath(__file__))


def main():

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
