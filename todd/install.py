import datetime
import json
import os
import pathlib
import shutil
import sys
import time
from distutils.dir_util import copy_tree
from typing import Dict, List, Tuple

from .cache_sources import fetch_package_sources, get_pkg_cache_dir, is_cached
from .index import add_to_index, augment_to_index, create_pkg_index, get_index
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


def install_package(lfs_dir: str, pkg: Package, verbose=False) -> bool:
    print(f"preparing {pkg.name} for pass {pkg.pass_idx}: ...")
    # delete and create build and fake root folder
    if os.path.isdir(BUILD_FOLDER):
        shutil.rmtree(BUILD_FOLDER)
    os.mkdir(BUILD_FOLDER)
    if os.path.isdir(FAKE_ROOT):
        shutil.rmtree(FAKE_ROOT)
    os.mkdir(FAKE_ROOT)

    os.chdir(BUILD_FOLDER)
    print(f"preparing {pkg.name} for pass {pkg.pass_idx}: ok")

    print(f"getting sources for {pkg.name} for pass {pkg.pass_idx}: ...")
    if not get_sources(lfs_dir, pkg):
        return False
    print(f"getting sources for {pkg.name} for pass {pkg.pass_idx}: ok")

    print(f"running build script for {pkg.name} for pass {pkg.pass_idx}: ...")
    os.environ["TODD_BUILD_DIR"] = BUILD_FOLDER
    os.environ["TODD_FAKE_ROOT_DIR"] = FAKE_ROOT
    os.environ["LFS_TGT"] = LFS_TGT
    cmd_suffix = "" if verbose else " >/dev/null 2>&1"
    if os.system(f"{pkg.build_script}{cmd_suffix}") != 0:
        print(
            f"running build script for {pkg.name} for pass {pkg.pass_idx}: failure",
            file=sys.stderr,
        )
        return False
    print(f"running build script for {pkg.name} for pass {pkg.pass_idx}: ok")

    print("copying files into root: ...")
    pkg_index = create_pkg_index(FAKE_ROOT, pkg)
    copy_tree(FAKE_ROOT, lfs_dir)
    # create new entry or augment old one
    if pkg.pass_idx:
        augment_to_index(lfs_dir, pkg_index)
    else:
        add_to_index(lfs_dir, pkg_index)
    print("copying files into root: ok, index updated")

    return True


def load_packages(repo: str) -> Dict[Tuple[str, int], Package]:
    """Load all available packages from repo."""
    with open(f"{repo}/packages.json", "r", newline="") as file:
        raw_packages = json.loads(file.read())["packages"]
    packages: Dict[Tuple[str, int], Package] = {}
    for raw_pkg in raw_packages:
        # check integrity of packages file
        # TODO: use json schema
        if (
            raw_pkg.get("name") is None
            or raw_pkg.get("version") is None
            or raw_pkg.get("pass_idx") is None
            or raw_pkg.get("src_urls") is None
            or raw_pkg.get("env") is None
        ):
            raise ValueError(f"package {raw_pkg} is faulty")

        package = Package(
            raw_pkg["name"],
            raw_pkg["version"],
            raw_pkg["pass_idx"],
            raw_pkg["src_urls"],
            raw_pkg["env"],
            repo,
            # using get() <- return None when not found
            raw_pkg.get("build_script"),
        )
        # TODO: work with versions
        if (package.name, package.pass_idx) in packages:
            raise ValueError(f"The repository '{repo}' contains the package '{package.name}' pass {package.pass_idx} twice")
        packages[(package.name, package.pass_idx)] = package

    return packages


def install_packages(
    package_idents: List[Tuple[str, int]],
    repo: str,
    env: str,
    lfs_dir: str,
    verbose: bool,
    jobs: int,
) -> bool:
    """Install all requested packages in order.
    A package is defined by a name and a pass index.
    """
    os.environ["MAKEFLAGS"] = f"-j{jobs}"
    index = get_index(lfs_dir)
    packages = load_packages(repo)

    print("attempting installation of the following packages:")
    print(", ".join([f"{package.name} pass {package.pass_idx}" for package in packages.values()]))
    start = time.time()
    for package_ident in package_idents:
        # go/no-go poll for installation
        if package_ident not in packages:
            print(f"package '{package_ident[0]}' for pass {package_ident[1]} couldn't be found")
            return False
        package = packages[package_ident]
        if package.env != env:
            print(f"package '{package.name}' for pass {package.pass_idx} couldn't be found for environment '{env}'")
            return False
        # check if pass is valid
        if package.name in index:
            package_idx = index[package.name]
            if package_idx.pass_idx >= package.pass_idx:
                print(f"installing '{package.name}' for pass {package.pass_idx}: already installed or replaced with later pass")
                continue
            if package_idx.pass_idx < package.pass_idx - 1:
                print(f"package '{package.name}' for pass {package.pass_idx} hasn't finished earlier passes")
                return False
            # only install when already installed pass is the to be installed one -1
        # TODO: check version

        if not install_package(lfs_dir, package, verbose=verbose):
            return False
    end = time.time()
    print("all packages installed time:", datetime.timedelta(seconds=(end - start)))
    return True
