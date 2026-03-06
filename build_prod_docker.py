#!/usr/bin/env python3
"""
Build script for YouTube Archiver Docker image.
- Builds frontend (npm install + npm run build)
- Copies assets to backend frontend-build
- Creates Docker image
- Optionally deploys (stops old container, runs new, cleans old images)
"""

import subprocess
import shutil
import sys
import os
from pathlib import Path

# Configuration
PROJECT_ROOT = Path(__file__).parent.resolve()
FRONTEND_DIR = PROJECT_ROOT / "yt-archiver-frontend"
BACKEND_DIR = PROJECT_ROOT / "yt-archiver-backend"
DOCKER_IMAGE_NAME = "yt_archiver"
DOCKER_TAG = "latest"
CONTAINER_NAME = "yt_archiver"

# Persistent runtime directory
RUNTIME_DIR = PROJECT_ROOT / "docker_runtime"


def run_command(cmd, cwd=None, description="", capture=False):
    """Run a shell command and handle errors."""
    print(f"\n{'='*50}")
    print(f"▶ {description}")
    print(f"  Command: {' '.join(cmd)}")
    print(f"{'='*50}")

    if capture:
        result = subprocess.run(
            cmd, cwd=cwd,
            shell=True if sys.platform == "win32" else False,
            capture_output=True, text=True
        )
    else:
        result = subprocess.run(
            cmd, cwd=cwd, shell=True if sys.platform == "win32" else False)

    if result.returncode != 0 and not capture:
        print(f"✗ Failed: {description}")
        sys.exit(1)

    print(f"✓ Complete: {description}")
    return result


def build_frontend():
    """Build the frontend with npm."""
    print("\n📦 Building Frontend...")

    # npm install
    run_command(
        ["npm", "install"],
        cwd=FRONTEND_DIR,
        description="Installing npm dependencies"
    )

    # npm run build
    run_command(
        ["npm", "run", "build"],
        cwd=FRONTEND_DIR,
        description="Building frontend (Vite)"
    )


def copy_assets():
    """Copy built frontend assets to backend."""
    print("\n📁 Copying Assets to Backend...")

    src_dist = FRONTEND_DIR / "dist"
    dest_build = BACKEND_DIR / "frontend-build"

    # Ensure source exists
    if not src_dist.exists():
        print(f"✗ Build output not found at {src_dist}")
        sys.exit(1)

    # Clean and copy assets folder
    if dest_build.exists():
        shutil.rmtree(dest_build)

    shutil.copytree(src_dist, dest_build)
    print(f"  ✓ Copied frontend build to {dest_build}")


def build_docker():
    """Build the Docker image."""
    print("\n🐳 Building Docker Image...")

    run_command(
        ["docker", "build", "-t", f"{DOCKER_IMAGE_NAME}:{DOCKER_TAG}", "."],
        cwd=BACKEND_DIR,
        description=f"Building Docker image: {DOCKER_IMAGE_NAME}:{DOCKER_TAG}"
    )


def stop_old_container():
    """Stop and remove the old container if running."""
    print("\n🛑 Stopping old container...")

    result = subprocess.run(
        ["docker", "ps", "-a", "-q", "-f", f"name={CONTAINER_NAME}"],
        capture_output=True, text=True
    )

    if result.stdout.strip():
        subprocess.run(["docker", "stop", CONTAINER_NAME], capture_output=True)
        print(f"  ✓ Stopped container: {CONTAINER_NAME}")
        subprocess.run(["docker", "rm", CONTAINER_NAME], capture_output=True)
        print(f"  ✓ Removed container: {CONTAINER_NAME}")
    else:
        print(f"  ℹ No existing container named '{CONTAINER_NAME}' found")


def cleanup_old_images():
    """Remove old/dangling images to free up space."""
    print("\n🧹 Cleaning up old Docker images...")

    result = subprocess.run(
        ["docker", "images", "-q", "-f", "dangling=true"],
        capture_output=True, text=True
    )

    if result.stdout.strip():
        dangling_ids = result.stdout.strip().split('\n')
        for img_id in dangling_ids:
            if img_id:
                subprocess.run(["docker", "rmi", img_id], capture_output=True)
        print(f"  ✓ Removed {len(dangling_ids)} dangling image(s)")
    else:
        print("  ℹ No dangling images to remove")

    subprocess.run(["docker", "builder", "prune", "-f"], capture_output=True)
    print("  ✓ Pruned build cache")


def deploy_container():
    """Deploy the new container with all volume mounts."""
    print("\n🚀 Deploying new container...")

    cmd = [
        "docker", "run", "-d",
        "--name", CONTAINER_NAME,
        "--restart", "unless-stopped",
        "-v", f"{RUNTIME_DIR}:/app/runtime",
        "-e", "APP_CONFIG_PATH=runtime/config/prod.yaml",
        "-p", "8000:8000",
        f"{DOCKER_IMAGE_NAME}:{DOCKER_TAG}"
    ]

    run_command(cmd, description=f"Starting container: {CONTAINER_NAME}")

    print(f"\n  📂 Mounted volumes:")
    print(f"     📁 Runtime: {RUNTIME_DIR} → /app/runtime")
    print(f"\n  🌐 Access at: http://localhost:8000")


def main():
    print("=" * 60)
    print("� YouTube Archiver - Production Docker Build Script")
    print("=" * 60)

    # Ensure runtime dir exists
    RUNTIME_DIR.mkdir(parents=True, exist_ok=True)

    # Step 1: Build frontend
    build_frontend()

    # Step 2: Copy assets
    copy_assets()

    # Step 3: Build Docker image
    build_docker()

    print("\n" + "=" * 60)
    print("✅ Build Complete!")
    print("=" * 60)

    # Ask user if they want to deploy
    print("\n" + "-" * 60)
    response = input("🚀 Do you want to deploy now? (y/n): ").strip().lower()

    if response in ('y', 'yes'):
        stop_old_container()
        cleanup_old_images()
        deploy_container()

        print("\n" + "=" * 60)
        print("✅ Deployment Complete!")
        print("=" * 60)
        print("\n📝 State will persist in the runtime directory across restarts.")
        print("The frontend is served from the backend directly via port 8000.")
    else:
        print("\n⏭ Skipping deployment.")
        print(f"\nTo deploy manually:")
        print(f"  docker run -d \\")
        print(f"    --name {CONTAINER_NAME} \\")
        print(f"    --restart unless-stopped \\")
        print(f"    -v {RUNTIME_DIR}:/app/runtime \\")
        print(f"    -e APP_CONFIG_PATH=runtime/config/prod.yaml \\")
        print(f"    -p 8000:8000 \\")
        print(f"    {DOCKER_IMAGE_NAME}:{DOCKER_TAG}")


if __name__ == "__main__":
    main()
