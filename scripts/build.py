#!/usr/bin/env python3
"""Build a YT Archiver release.

Writes the version into the backend, UI and extension, optionally lints,
builds the Docker image (the UI is built inside it) and zips the extension:

    yt-archiver:<version> and yt-archiver:latest
    dist/yt-archiver-extension.zip

Run it with:  docker compose up -d   (or see docs for plain docker run)
"""

import argparse
import re
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DIST = ROOT / "dist"
EXTENSION = ROOT / "extension"
IMAGE = "yt-archiver"
SEMVER_RE = re.compile(r"\d+\.\d+\.\d+")

# file -> pattern whose first group is followed by the quoted version
VERSION_FILES = {
    ROOT / "yt_archiver" / "__init__.py": re.compile(r'(__version__ = )"[^"]*"'),
    ROOT / "pyproject.toml": re.compile(r'^(version = )"[^"]*"', re.M),
    ROOT / "ui" / "package.json": re.compile(r'("version":\s*)"[^"]*"'),
    EXTENSION / "manifest.json": re.compile(r'("version":\s*)"[^"]*"'),
}


class BuildError(Exception):
    pass


def step(msg: str) -> None:
    print(f"==> {msg}", flush=True)


def tool(name: str) -> str:
    path = shutil.which(name)
    if not path:
        raise BuildError(f"'{name}' was not found on PATH")
    return path


def run(cmd: list, cwd: Path = ROOT) -> None:
    """Run a build step, streaming its output to the terminal."""
    line = " ".join([Path(cmd[0]).name, *cmd[1:]])
    print(f"    $ {line}", flush=True)
    result = subprocess.run(cmd, cwd=cwd)
    if result.returncode != 0:
        raise BuildError(f"{line} failed (exit code {result.returncode})")


def current_version() -> str:
    match = re.search(r'__version__ = "([^"]*)"', (ROOT / "yt_archiver" / "__init__.py").read_text())
    if not match:
        raise BuildError("no __version__ found in yt_archiver/__init__.py")
    return match.group(1)


def set_version(ver: str) -> None:
    for path, pattern in VERSION_FILES.items():
        path.write_text(pattern.sub(rf'\g<1>"{ver}"', path.read_text(), count=1))


def lint() -> None:
    step("Linting (ruff)")
    run([tool("ruff"), "check", "."])


def build_image(ver: str) -> None:
    step(f"Building Docker image {IMAGE}:{ver}")
    run([tool("docker"), "build", "-t", f"{IMAGE}:{ver}", "-t", f"{IMAGE}:latest", "."])


def zip_extension() -> Path:
    step("Packaging the browser extension")
    DIST.mkdir(exist_ok=True)
    out = DIST / "yt-archiver-extension.zip"
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as zf:
        for file in sorted(EXTENSION.rglob("*")):
            if file.is_file() and file.name != ".DS_Store":
                zf.write(file, file.relative_to(EXTENSION))
    return out


def ask(prompt: str, default: str) -> str:
    if not sys.stdin.isatty():
        return default
    answer = input(f"{prompt} [{default}]: ").strip()
    return answer or default


def confirm(prompt: str, default: bool = True) -> bool:
    if not sys.stdin.isatty():
        return default
    hint = "Y/n" if default else "y/N"
    while True:
        answer = input(f"{prompt} [{hint}]: ").strip().lower()
        if not answer:
            return default
        if answer in ("y", "yes", "n", "no"):
            return answer.startswith("y")


def ask_version(given: str = None) -> str:
    if given:
        ver = given.removeprefix("v")
        if not SEMVER_RE.fullmatch(ver):
            raise BuildError(f'version must look like "1.2.0", got "{given}"')
        return ver
    while True:
        ver = ask("Version", current_version()).removeprefix("v")
        if SEMVER_RE.fullmatch(ver):
            return ver
        print('  version must look like "1.2.0"')


def main() -> int:
    parser = argparse.ArgumentParser(description="Build a YT Archiver release. Asks for anything not given; without a terminal it uses the defaults.")
    parser.add_argument("--version", help='release version, e.g. "1.2.0" (default: the current one)')
    parser.add_argument("--no-image", action="store_true", help="skip the Docker image (CI builds and pushes it itself)")
    args = parser.parse_args()

    try:
        ver = ask_version(args.version)
        with_image = not args.no_image and confirm("Build the Docker image?")
        with_lint = confirm("Run ruff?", default=False)

        print(f"\n  version:  v{ver}\n  image:    {f'{IMAGE}:{ver}' if with_image else 'no'}\n  lint:     {'yes' if with_lint else 'no'}\n")
        if not confirm("Build with these settings?"):
            print("aborted")
            return 1

        set_version(ver)
        if with_lint:
            lint()
        if with_image:
            build_image(ver)
        extension = zip_extension()
    except (KeyboardInterrupt, EOFError):
        print("\naborted", file=sys.stderr)
        return 1
    except BuildError as err:
        print(f"error: {err}", file=sys.stderr)
        return 1

    step("Done")
    if with_image:
        print(f"    image: {IMAGE}:{ver}")
    print(f"    extension: {extension}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
