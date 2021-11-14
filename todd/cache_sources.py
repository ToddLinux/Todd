"""Download, track and delete cache package sources for later use."""
import requests
import sys
import os
import shutil

from .package_classes import Package

__all__ = ["get_pkg_cache_dir", "get_local_file_name", "fetch_package_sources", "is_cached", "clear_cache"]

PKG_CACHE_DIRECTORY = "/var/cache/todd"


def get_pkg_cache_dir(lfs_dir: str, package: Package) -> str:
    """Get path to caching directory for package."""
    cache_dir = f"{lfs_dir}/{PKG_CACHE_DIRECTORY}"
    return f"{cache_dir}/{package.name}/{package.version}"


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

    for url in package.src_urls:
        local_file_name = get_local_file_name(url)
        dest_file = f"{pkg_cache_dir}/{local_file_name}"
        # TODO: checksum
        if not os.path.isfile(dest_file):
            if not dwn_file(url, dest_file, local_file_name):
                return False
        else:
            print(f"Source: '{local_file_name}' for package {package.name} already downloaded")

    return True


def is_cached(lfs_dir: str, package: Package) -> bool:
    """
    Check if all package sources for specified package have been downloaded

    :param lfs_dir: package management system root directory
    :param package: package for which sources are being checked
    :return: True if all satisfied False otherwise
    """
    pkg_cache_dir = get_pkg_cache_dir(lfs_dir, package)
    return all([
        os.path.isfile(f"{pkg_cache_dir}/{get_local_file_name(url)}")
        for url
        in package.src_urls
    ])


def clear_cache(lfs_dir: str) -> None:
    """
    Delete downloaded package sources

    :param lfs_dir: package management system root directory
    """
    shutil.rmtree(f"{lfs_dir}/{PKG_CACHE_DIRECTORY}")
