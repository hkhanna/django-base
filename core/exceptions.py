class ApplicationException(Exception):
    def __init__(self, message: str, **kwargs: object) -> None:
        self.__dict__.update(kwargs)
        super().__init__(message)


class ApplicationError(ApplicationException):
    pass


class ApplicationWarning(ApplicationException):
    pass
