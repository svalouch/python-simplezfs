
'''
Exceptions
'''


class ZFSException(Exception):
    '''
    Base for the exception tree used by this library.

    :note: Some functions throw ordinary python base exceptions as well.
    '''
    pass


class DatasetNotFound(ZFSException):
    '''
    A dataset was not found.
    '''
    pass


class PermissionError(ZFSException):
    '''
    Permissions are not sufficient to carry out the task.
    '''
    pass


class PoolNotFound(ZFSException):
    '''
    A pool was not found.
    '''
    pass


class PropertyNotFound(ZFSException):
    '''
    A property was not found.
    '''
    pass


class ValidationError(ZFSException):
    '''
    Indicates that a value failed validation.
    '''
    pass
