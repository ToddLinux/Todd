from typing import List


class PackageIndex:
    """Represents in index file."""

    def __init__(self, name: str, version: str, files: List[str]):
        # name of package
        self.name = name
        # installed version
        self.version = version
        # files belonging to package -> to be deleted when uninstalling
        self.files = files


class Package:
    """Represents build and installation."""

    def __init__(
        self,
        name: str,
        version: str,
        src_urls: List[str],
        env: str,
        repo: str,
        build_script_name: str = None,
    ):
        self.name = name
        self.version = version
        self.src_urls = src_urls
        self.env = env
        # TODO: add version to default script path
        self.build_script = (
            f"{repo}/{name}.sh" if build_script_name is None else f"{repo}/{build_script_name}"
        )
