import argparse
import os
import sys
import subprocess
import urllib.request
import ctypes
import json

PACKAGE_JSON_URL = "https://gitlab.com/PPPPPPPPPPPPPPotato/sap/-/raw/main/Packages.json?ref_type=heads"

def load_packages():
    """Fetch the latest package list from GitHub JSON."""
    try:
        print(f"Fetching package list from {PACKAGE_JSON_URL} ...")
        with urllib.request.urlopen(PACKAGE_JSON_URL) as response:
            data = response.read()
            try:
                packages = json.loads(data)
            except json.JSONDecodeError as e:
                print(f"ERROR: Failed to parse JSON from {PACKAGE_JSON_URL}")
                print(f"Details: {e}")
                print("Make sure you are using the RAW URL from GitHub (raw.githubusercontent.com)")
                sys.exit(1)

            if not isinstance(packages, dict):
                print(f"ERROR: Expected JSON object at top level, got {type(packages)}")
                sys.exit(1)

            return packages
    except urllib.error.URLError as e:
        print(f"ERROR: Could not fetch package list: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error fetching packages: {e}")
        sys.exit(1)

def download_file(url):
    filename = os.path.basename(url)
    temp_path = os.path.join(os.getenv("TEMP"), filename)
    print(f"Downloading {url} ...")
    urllib.request.urlretrieve(url, temp_path)
    print(f"Saved to {temp_path}")
    return temp_path

def run_installer(installer_path):
    print("Launching installer... (may require Admin approval)")
    ctypes.windll.shell32.ShellExecuteW(None, "runas", installer_path, None, None, 1)

def pip_install(target):
    print(f"Installing via pip: {target}")
    subprocess.run([sys.executable, "-m", "pip", "install", target], check=True)

def pip_uninstall(package):
    print(f"Uninstalling via pip: {package}")
    subprocess.run([sys.executable, "-m", "pip", "uninstall", "-y", package], check=True)

def install_package(name):
    PACKAGES = load_packages()
    if name not in PACKAGES:
        print(f"ERROR: Unknown package '{name}'. Check Repo for available packages.")
        sys.exit(1)

    pkg = PACKAGES[name]
    url = pkg["url"]

    # Python package
    if not url.startswith("http"):
        pip_install(url)
        return

    installer_path = download_file(url)

    # Detect file type
    if installer_path.endswith((".exe", ".msi")):
        run_installer(installer_path)
    elif installer_path.endswith((".whl", ".zip", ".tar.gz")):
        pip_install(installer_path)
    else:
        print(f"ERROR: Unknown file type for '{installer_path}'")

def uninstall_package(name):
    PACKAGES = load_packages()
    if name not in PACKAGES:
        print(f"ERROR: Unknown package '{name}'. Check your GitHub JSON for available packages.")
        sys.exit(1)

    pkg = PACKAGES[name]
    url = pkg["url"]

    # Python package uninstall
    if not url.startswith("http"):
        pip_uninstall(url)
        return

    # Windows app uninstall
    uninstall_cmd = pkg.get("uninstall")
    if uninstall_cmd and os.path.exists(uninstall_cmd):
        print(f"Launching uninstaller for {name}... (may require Admin approval)")
        ctypes.windll.shell32.ShellExecuteW(None, "runas", uninstall_cmd, None, None, 1)
    else:
        print(f"WARNING: No uninstaller defined or path invalid for '{name}'")

def main():
    parser = argparse.ArgumentParser(
        description="SAP — Super Awesome Packages"
    )
    subparsers = parser.add_subparsers(dest="command", title="commands", required=True)

    # Install command
    install_parser = subparsers.add_parser(
        "install",
        help="Install a package from repo"
    )
    install_parser.add_argument(
        "name",
        help="Name of the package to install (must exist in the GitHub JSON)"
    )

    # Uninstall command
    uninstall_parser = subparsers.add_parser(
        "uninstall",
        help="Uninstall a package"
    )
    uninstall_parser.add_argument(
        "name",
        help="Name of the package to uninstall (must exist in the GitHub JSON)"
    )

    args = parser.parse_args()

    if args.command == "install":
        install_package(args.name)
    elif args.command == "uninstall":
        uninstall_package(args.name)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()

# Liam
