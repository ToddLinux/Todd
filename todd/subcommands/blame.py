from typing import List
import os.path

from ..index import get_index


def blame_args_validator(args: List[str]) -> bool:
    if len(args) != 1:
        print("Invalid number of subarguments. Required 1: filename")
        return False
    
    return True


def blame_handler(args: List[str]) -> None:
    filename = os.path.abspath(args[0])
    
    index = get_index("/")
    found = False

    for pkg, pkg_index in index.items():
        if filename in pkg_index.files:
            print("Found in package:", pkg)
            found = True
            break  # files may not overlap between packages

    if not found:
        print("No such file in file index")
    