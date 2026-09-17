import json
import os
import subprocess
import sys
import time
import urllib.request
from dataclasses import dataclass

from version import APP_VERSION

# =====================================================
# GITHUB UPDATE SETTINGS
# =====================================================

GITHUB_OWNER = "metodidrumev-design"
GITHUB_REPO = "MP3_Order_PRO"

GITHUB_API_VERSION = "2026-03-10"

# =====================================================
# UPDATE INFORMATION
# =====================================================


@dataclass
class UpdateInfo:

    current_version: str
    latest_version: str
    release_url: str
    release_notes: str
    download_url: str | None = None
    file_name: str | None = None


# =====================================================
# VERSION HELPERS
# =====================================================


def normalize_version(version):

    version = str(version).strip()

    if version.lower().startswith("v"):
        version = version[1:]

    return version


def version_tuple(version):

    version = normalize_version(version)

    parts = version.split(".")

    numbers = []

    for part in parts[:3]:

        try:
            numbers.append(int(part))

        except ValueError:
            numbers.append(0)

    while len(numbers) < 3:

        numbers.append(0)

    return tuple(numbers)


def is_newer_version(current_version, latest_version):

    return version_tuple(latest_version) > version_tuple(current_version)


# =====================================================
# CHECK FOR UPDATE
# =====================================================


def check_for_update(current_version=APP_VERSION):

    url = (
        f"https://api.github.com/repos/" f"{GITHUB_OWNER}/{GITHUB_REPO}/releases/latest"
    )

    request = urllib.request.Request(
        url,
        headers={
            "Accept": "application/vnd.github+json",
            "User-Agent": "MP3_Order_PRO",
            "X-GitHub-Api-Version": GITHUB_API_VERSION,
        },
    )

    try:

        with urllib.request.urlopen(request, timeout=10) as response:

            data = json.loads(response.read().decode("utf-8"))

    except Exception:

        return None

    latest_version = data.get("tag_name", "")

    if not latest_version:

        return None

    if not is_newer_version(current_version, latest_version):

        return None

    assets = data.get("assets", [])

    download_url = None
    file_name = None

    for asset in assets:

        asset_name = asset.get("name", "")

        if asset_name.lower().endswith(".exe"):

            download_url = asset.get("browser_download_url")

            file_name = asset_name

            break

    if not download_url:

        return None

    return UpdateInfo(
        current_version=current_version,
        latest_version=normalize_version(latest_version),
        release_url=data.get("html_url", ""),
        release_notes=data.get("body", ""),
        download_url=download_url,
        file_name=file_name,
    )


# =====================================================
# DOWNLOAD UPDATE
# =====================================================


def download_update(update_info, destination):

    if not update_info.download_url:

        return False

    request = urllib.request.Request(
        update_info.download_url,
        headers={
            "User-Agent": "MP3_Order_PRO",
        },
    )

    try:

        with urllib.request.urlopen(request, timeout=30) as response:

            with open(destination, "wb") as file:

                file.write(response.read())

        return True

    except Exception:

        return False


# =====================================================
# APPLY UPDATE
# =====================================================


def apply_update(old_exe, new_exe, restart_exe=None):

    try:

        # Изчакваме старата програма да освободи файла
        time.sleep(2)

        # Заменяме старата версия с новата
        os.replace(new_exe, old_exe)

        # Стартираме новата версия
        if restart_exe:

            subprocess.Popen([restart_exe], close_fds=True)

        return True

    except Exception:

        return False


# =====================================================
# WAIT FOR OLD PROCESS
# =====================================================


def wait_for_process(process_id, timeout=30):

    if not process_id:

        return True

    start_time = time.time()

    while time.time() - start_time < timeout:

        try:

            result = subprocess.run(
                [
                    "tasklist",
                    "/FI",
                    f"PID eq {process_id}",
                ],
                capture_output=True,
                text=True,
                creationflags=subprocess.CREATE_NO_WINDOW,
            )

            if str(process_id) not in result.stdout:

                return True

        except Exception:

            return True

        time.sleep(0.5)

    return False


# =====================================================
# UPDATER PROCESS
# =====================================================


def run_updater():

    if len(sys.argv) < 4:

        return

    old_exe = sys.argv[1]
    new_exe = sys.argv[2]
    restart_exe = sys.argv[3]

    process_id = None

    if len(sys.argv) >= 5:

        try:

            process_id = int(sys.argv[4])

        except ValueError:

            process_id = None

    if not wait_for_process(process_id):

        return

    apply_update(
        old_exe,
        new_exe,
        restart_exe,
    )


# =====================================================
# START UPDATER
# =====================================================


if __name__ == "__main__":

    run_updater()
