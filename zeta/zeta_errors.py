EZTFILE = 1  # Error related a file and directory name
EZTFIELD = 2
EZTUNEXP = 10


class ZetaCliError(Exception):
    """Base class for exceptions in ZetaCLI
    """
    def __init__(self, message, errcode):
        super().__init__(message)
        self.errcode = errcode
        self.message = message
        self.pre_message = ""

    def handle(self):
        print(self)
        exit(self.errcode)

    def throw(self):
        raise self

    def __str__(self):
        return f"{self.pre_message} [Code: {self.errcode}]: {self.message}"


class ZetaCliInitError(ZetaCliError):
    def __init__(self, message, errcode):
        super().__init__(message, errcode)
        self.pre_message = "[ZetaCLI Init Error]"


class ZetaCliCheckError(ZetaCliError):
    def __init__(self, message, errcode):
        super().__init__(message, errcode)
        self.pre_message = "[ZetaCLI Check Error]"


class ZetaCliServicesError(ZetaCliError):
    def __init__(self, message, errcode):
        super().__init__(message, errcode)
        self.pre_message = "[ZetaCLI Services Error]"


class ZetaCliGenError(ZetaCliError):
    def __init__(self, message, errcode):
        super().__init__(message, errcode)
        self.pre_message = "[ZetaCLI Gen Error]"
