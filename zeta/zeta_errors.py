EZTFILE = 1  # Error related a file and directory name
EZTFIELD = 2
EZTUNEXP = 10


class ZetaCLIError(Exception):
    """Base class for exceptions in ZetaCLI
    """
    def __init__(self, message, errcode):
        super().__init__(message)
        self.errcode = errcode
        self.message = message

    def handle(self):
        print(self)
        exit(self.errcode)

    def __str__(self):
        return f"[Err Code: {self.errcode}]: {self.message}"
