"""Track installed packages."""
import json
import os
import pathlib
from typing import Dict, Set

from .package_classes import Package, PackageIndex

__all__ = ["create_pkg_index", "add_to_index", "get_index", "pkg_index_exists"]

BASE_DIR = pathlib.Path(__file__).parent.resolve()
INDEX_FILE_PATH = "/var/lib/todd/status.json"
INDEX_FILE_DIR_PATH = "/var/lib/todd"


def pkg_index_exists(lfs_dir: str) -> bool:
    return os.path.isfile(f"{lfs_dir}/{INDEX_FILE_PATH}")


def create_pkg_index(fake_root: str, package: Package) -> PackageIndex:
    """Index files created for this package in the fake root."""
    index_files: Set[str] = set()
    for root, _, files in os.walk(fake_root):
        for file in files:
            index_files.add(f"/{os.path.relpath(os.path.join(root, file), fake_root)}")
    return PackageIndex(
        package.name,
        package.version,
        package.pass_idx,
        index_files,
    )


def add_to_index(lfs_dir: str, new_pkg: PackageIndex) -> None:
    index = get_index(lfs_dir)
    if new_pkg.name in index:
        raise ValueError(f"Can't add already installed package {new_pkg.name} to index.")
    index[new_pkg.name] = new_pkg
    update_index(lfs_dir, index)


def augment_to_index(lfs_dir: str, pkg: PackageIndex) -> None:
    """Used for multiple passes of the same package."""
    index = get_index(lfs_dir)
    if pkg.name not in index:
        raise ValueError(f"Can't augment not installed package {pkg.name} to index.")
    index[pkg.name].files.update(pkg.files)
    index[pkg.name].pass_idx = pkg.pass_idx
    update_index(lfs_dir, index)


def remove_from_index(lfs_dir: str, del_pkg_name: str) -> None:
    index = get_index(lfs_dir)
    if del_pkg_name not in index:
        raise ValueError(f"Can't remove package {del_pkg_name}, which hasn't been installed")
    del index[del_pkg_name]
    update_index(lfs_dir, index)


def get_index(lfs_dir: str) -> Dict[str, PackageIndex]:
    index: Dict[str, PackageIndex] = {}
    # hasn't been created yet?
    if not os.path.isfile(f"{lfs_dir}/{INDEX_FILE_PATH}"):
        os.makedirs(f"{lfs_dir}/{INDEX_FILE_DIR_PATH}", exist_ok=True)
        update_index(lfs_dir, index)
        return index

    with open(f"{lfs_dir}/{INDEX_FILE_PATH}", "r") as file:
        pkgs_json = json.load(file)
        for pkg_json in pkgs_json.values():
            index[pkg_json["name"]] = PackageIndex(
                pkg_json["name"],
                pkg_json["version"],
                pkg_json["pass_idx"],
                pkg_json["files"],
            )
    return index


def update_index(lfs_dir: str, index: Dict[str, PackageIndex]) -> None:
    with open(f"{lfs_dir}/{INDEX_FILE_PATH}", "w") as file:
        json.dump({pkg.name: pkg.get_dict() for pkg in index.values()}, file, indent=4)
