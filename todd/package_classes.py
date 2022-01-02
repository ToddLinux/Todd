from typing import Any, Dict, List, Set


class PackageIndex:
    """Represents in index file."""

    def __init__(self, name: str, version: str, pass_idx: int, files: Set[str]):
        # name of package
        self.name = name
        # installed version
        self.version = version
        # passes are required for bootstrapping some tools
        self.pass_idx = pass_idx
        # files belonging to package -> to be deleted when uninstalling
        self.files = files

    def get_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "version": self.version,
            "pass_idx": self.pass_idx,
            "files": list(self.files),
        }


class PackageSource:
    """Represents package source."""

    def __init__(self, url: str, checksum: str):
        self.url = url
        self.checksum = checksum

    def __repr__(self):
        return f"url: {self.url}, checksum: {self.checksum}"


class Package:
    """Represents build and installation.

    Parameters:

    pass_idx:
        -1 results in only not being installed if package has already been installed with pass_idx = -1

    """

    def __init__(
        self,
        name: str,
        version: str,
        src_urls: List[PackageSource],
        env: str,
        repo: str,
        pass_idx: int = None,
        build_script_name: str = None,
    ):
        self.name = name
        self.version = version
        self.pass_idx = -1 if pass_idx is None else pass_idx
        self.src_urls = src_urls
        self.env = env
        # TODO: add version to default script path
        self.build_script = f"{repo}/{name}.sh" if build_script_name is None else f"{repo}/{build_script_name}"
