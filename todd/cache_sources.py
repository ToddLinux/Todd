"""Download, track and delete cache package sources for later use."""
import os
import shutil
import sys
import subprocess

import requests

from .package_classes import Package, PackageSource

__all__ = [
    "get_pkg_cache_dir",
    "get_local_file_name",
    "fetch_package_sources",
    "is_cached",
    "clear_cache",
]

PKG_CACHE_DIRECTORY = "/var/cache/todd"


def get_pkg_cache_dir(lfs_dir: str, package: Package) -> str:
    """Get path to caching directory for package."""
    return f"{lfs_dir}/{PKG_CACHE_DIRECTORY}/{package.name}/{package.version}"


def dwn_file(url: str, file_path: str, source_pretty_name: str) -> bool:
    """
    Download file

    :param url: source URL
    :param file_path: file to which the downloaded content will be written to
    :param source_pretty_name: name of the source, for logging purposes
    :return: True if successfully downloaded all package sources False otherwise
    """
    print(f"downloading {source_pretty_name}: ...")
    with requests.get(url, stream=True) as r:
        if r.status_code != 200:
            print(f"downloading {source_pretty_name}: failure", file=sys.stderr)
            return False
        with open(file_path, "wb") as f:
            for chunk in r.iter_content(chunk_size=8192):
                f.write(chunk)
    print(f"downloading {source_pretty_name}: ok")
    return True


def get_local_file_name(url: str) -> str:
    """
    Get package source local file name from it's url

    :param url: source of the file
    :return: filename
    """
    return url.split("/")[-1]


def fetch_package_sources(lfs_dir: str, package: Package) -> bool:
    """
    Download all package sources for package

    :param lfs_dir: package management system root directory
    :param package: package for which the sources are being downloaded
    :return: True if successfully downloaded all package sources False otherwise
    """
    pkg_cache_dir = get_pkg_cache_dir(lfs_dir, package)
    if not os.path.isdir(pkg_cache_dir):
        os.makedirs(pkg_cache_dir)

    for src in package.src_urls:
        local_file_name = get_local_file_name(src.url)
        dest_file = f"{pkg_cache_dir}/{local_file_name}"

        if not is_cached_package_source(pkg_cache_dir, src):
            if not dwn_file(src.url, dest_file, local_file_name):
                return False
        else:
            print(f"Source: '{local_file_name}' for package {package.name} already downloaded")

    return True


def checksum(path: str) -> str:
    return subprocess.run(
        ["md5sum", path],
        check=True,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
    ).stdout.decode().split()[0]


def is_cached_package_source(pkg_cache_dir, package: PackageSource) -> bool:
    path = f"{pkg_cache_dir}/{get_local_file_name(package.url)}"
    if not os.path.isfile(path):
        return False
    if not (checksum(path) == package.checksum):
        return False

    return True


def is_cached(lfs_dir: str, package: Package) -> bool:
    """
    Check if all package sources for specified package have been downloaded

    :param lfs_dir: package management system root directory
    :param package: package for which sources are being checked
    :return: True if all satisfied False otherwise
    """
    pkg_cache_dir = get_pkg_cache_dir(lfs_dir, package)
    
    for src in package.src_urls:
        if not is_cached_package_source(pkg_cache_dir, src):
            return False

    return True


def clear_cache(lfs_dir: str) -> None:
    """
    Delete downloaded package sources

    :param lfs_dir: package management system root directory
    """
    shutil.rmtree(f"{lfs_dir}/{PKG_CACHE_DIRECTORY}")
