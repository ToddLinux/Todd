import sys
import time
import datetime
import json
import os
import shutil
import pathlib
from typing import List, Dict
from distutils.dir_util import copy_tree

from .index import create_pkg_index, get_index, add_to_index
from .cache_sources import get_pkg_cache_dir, is_cached, fetch_package_sources
from .package_classes import Package

__all__ = ["install_packages", "load_packages"]


FILE_DIR_PATH = pathlib.Path(__file__).parent.resolve()
BUILD_FOLDER = "/tmp/todd_linux_build"
FAKE_ROOT = "/tmp/todd_linux_fake_root"
LFS_TGT = "x86_64-lfs-linux-gnu"


def get_sources(lfs_dir: str, package: Package) -> bool:
    """Fetch all sources that haven't been cached yet."""
    pkg_cache_dir = get_pkg_cache_dir(lfs_dir, package)
    if not is_cached(lfs_dir, package):
        if not fetch_package_sources(lfs_dir, package):
            return False

    print("copying package sources into build directory: ...")
    for file in os.listdir(pkg_cache_dir):
        shutil.copy(f"{pkg_cache_dir}/{file}", BUILD_FOLDER)
    print("copying package sources into build directory: ok")

    return True


def install_package(lfs_dir: str, package: Package, verbose=False) -> bool:
    print(f"preparing {package.name}: ...")
    # delete and create build and fake root folder
    if os.path.isdir(BUILD_FOLDER):
        shutil.rmtree(BUILD_FOLDER)
    os.mkdir(BUILD_FOLDER)
    if os.path.isdir(FAKE_ROOT):
        shutil.rmtree(FAKE_ROOT)
    os.mkdir(FAKE_ROOT)

    os.chdir(BUILD_FOLDER)
    print(f"preparing {package.name}: ok")

    print(f"getting sources for {package.name}: ...")
    if not get_sources(lfs_dir, package):
        return False
    print(f"getting sources for {package.name}: ok")

    print(f"running build script for {package.name}: ...")
    os.environ["TODD_BUILD_DIR"] = BUILD_FOLDER
    os.environ["TODD_FAKE_ROOT_DIR"] = FAKE_ROOT
    os.environ["LFS_TGT"] = LFS_TGT
    cmd_suffix = "" if verbose else " >/dev/null 2>&1"
    if os.system(f"{package.build_script}{cmd_suffix}") != 0:
        print(f"running build script for {package.name}: failure", file=sys.stderr)
        return False
    print(f"running build script for {package.name}: ok")

    print("copying files into root: ...")
    pkg_index = create_pkg_index(FAKE_ROOT, package)
    copy_tree(FAKE_ROOT, lfs_dir)
    add_to_index(lfs_dir, pkg_index)
    print("copying files into root: ok, index updated")

    return True


def load_packages(repo: str) -> Dict[str, Package]:
    """Load all available packages from repo."""
    with open(f"{repo}/packages.json", "r", newline="") as file:
        raw_packages = json.loads(file.read())["packages"]
    packages = {}
    for raw_pkg in raw_packages:
        # check integrity of packages file
        # TODO: use json schema
        if (
            raw_pkg.get("name") is None
            or raw_pkg.get("version") is None
            or raw_pkg.get("src_urls") is None
            or raw_pkg.get("env") is None
        ):
            raise ValueError(f"package {raw_pkg} is faulty")

        package = Package(
            raw_pkg["name"],
            raw_pkg["version"],
            raw_pkg["src_urls"],
            raw_pkg["env"],
            repo,
            # using get() <- return None when not found
            raw_pkg.get("build_script"),
        )
        # TODO: work with versions
        if package.name in packages:
            raise ValueError(
                f"The repository '{repo}' contains the package '{package.name}' twice"
            )
        packages[package.name] = package

    return packages


def install_packages(
    names: List[str],
    repo: str,
    env: str,
    lfs_dir: str,
    verbose: bool,
    jobs: int,
) -> bool:
    """install all requested packages in order"""
    os.environ["MAKEFLAGS"] = f"-j{jobs}"
    index = get_index(lfs_dir)
    packages = load_packages(repo)

    print("attempting installation of the following packages:")
    print(", ".join(names))
    start = time.time()
    for name in names:
        # go/no-go poll for installation
        if name not in packages:
            print(f"package '{name}' couldn't be found")
            return False
        if packages[name].env != env:
            print(
                f"package '{name}' couldn't be found for environment '{env}'")
            return False
        if name in index:
            print(f"installing {name}: already installed")
            continue
        # TODO: check version

        if not install_package(lfs_dir, packages[name],  verbose=verbose):
            return False
    end = time.time()
    print("all packages installed time:", datetime.timedelta(seconds=(end - start)))
    return True
