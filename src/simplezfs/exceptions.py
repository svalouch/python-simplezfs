
'''
Exceptions
'''

from typing import Optional


class ZFSException(Exception):
    '''
    Base for the exception tree used by this library.

    :note: Some functions throw ordinary python base exceptions as well.
    '''


class DatasetNotFound(ZFSException):
    '''
    A dataset was not found.
    '''


class PermissionError(ZFSException):
    '''
    Permissions are not sufficient to carry out the task.
    '''


class PoolNotFound(ZFSException):
    '''
    A pool was not found.
    '''


class PropertyNotFound(ZFSException):
    '''
    A property was not found.
    '''


class ValidationError(ZFSException):
    '''
    Indicates that a value failed validation.
    '''


class PEHelperException(ZFSException):
    '''
    Indicates a problem when running the PE helper.
    '''


class ExternalPEHelperException(PEHelperException):
    '''
    Indicates a problem when running the external helper script.
    '''
    def __init__(self, message: str, returncode: Optional[int], stdout: Optional[str] = None,
                 stderr: Optional[str] = None) -> None:
        '''
        :param message: The message to carry.
        :param returncode: The programs return code.
        :param stdout: The programs standard output, if any.
        :param stderr: The programs standard error, if any.
        '''
        super().__init__(message)
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr
