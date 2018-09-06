class PysmError(Exception):
    '''All |Machine| exceptions are of this type. '''
    pass


class InvalidState(PysmError):
    pass


class NoState(PysmError):
    pass


class AlreadyHasState(PysmError):
    pass


class AlreadyHasInitialState(PysmError):
    pass


class InvalidTransition(PysmError):
    pass
