from typing import Set, List, Dict, Any


class PackageIndex:
    """Represents in index file."""

    def __init__(
        self,
        name: str,
        version: str,
        pass_idx: int,
        files: Set[str]
    ):
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


class Package:
    """Represents build and installation."""

    def __init__(
        self,
        name: str,
        version: str,
        pass_idx: int,
        src_urls: List[str],
        env: str,
        repo: str,
        build_script_name: str = None,
    ):
        self.name = name
        self.version = version
        self.pass_idx = pass_idx
        self.src_urls = src_urls
        self.env = env
        # TODO: add version to default script path
        self.build_script = (
            f"{repo}/{name}.sh" if build_script_name is None else f"{repo}/{build_script_name}"
        )
