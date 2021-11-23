from typing import List, Callable

class Subcommand:
    def __init__(self, args_validator: Callable[[List[str]], bool], handler: Callable[[List[str]], None]):
        self.validate_args = args_validator
        self.handle = handler
