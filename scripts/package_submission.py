# Build the Moodle submission zip: MohannadAlGhourayeb-JadMoharam-OmarTabsh-430L.zip
# Omar Tabsh - 202400798
#
#   python -m scripts.package_submission [extra files...]
#
# Contents:
#   - every file tracked by git (complete source code, database scripts, Postman collections, docs)
#   - database/security_system.db (the real database with your records), if it exists
#   - any extra files you pass, e.g. the exported report: python -m scripts.package_submission Final_Report.docx
# Never included: .env (secrets), virtual environments, caches.

import os
import subprocess
import sys
import zipfile

from common.config import BASE_DIR

PROJECT_NAME = "MohannadAlGhourayeb-JadMoharam-OmarTabsh-430L"
DATABASE_FILE = os.path.join("database", "security_system.db")
NEVER_INCLUDE = (".env",)


def tracked_files():
    output = subprocess.run(["git", "ls-files"], cwd=BASE_DIR, capture_output=True, text=True, check=True)
    return [line for line in output.stdout.splitlines() if line]


def main(extra_files):
    files = tracked_files()
    if os.path.exists(os.path.join(BASE_DIR, DATABASE_FILE)):
        files.append(DATABASE_FILE)
    else:
        print(f"WARNING: {DATABASE_FILE} not found. Run the services and your Postman tests first.")

    zip_path = os.path.join(BASE_DIR, f"{PROJECT_NAME}.zip")
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as archive:
        for relative in files:
            if os.path.basename(relative) in NEVER_INCLUDE:
                continue
            archive.write(os.path.join(BASE_DIR, relative), f"{PROJECT_NAME}/{relative}")
        for extra in extra_files:
            archive.write(extra, f"{PROJECT_NAME}/{os.path.basename(extra)}")

    with zipfile.ZipFile(zip_path) as archive:
        count = len(archive.namelist())
    print(f"Created {zip_path} with {count} files")


if __name__ == "__main__":
    main(sys.argv[1:])
