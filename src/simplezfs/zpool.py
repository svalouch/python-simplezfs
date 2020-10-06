
import logging
import os
import stat
from typing import Optional


log = logging.getLogger('simplezfs.zpool')


class ZPool:
    '''
    ZPool interface class. This API generally covers only the zpool(8) tool, for zfs(8) please see class :class:`~ZFS`.

    **ZFS implementation**

    There are two ways how the API actually communicates with the ZFS filesystem:

    * Using the CLI tools
    * Using the native API

    When creating an instance of this class, select one or the other as the ``api`` argument.
    '''
    def __init__(self, *, metadata_namespace: Optional[str] = None, pe_helper: Optional[str] = None,
                 use_pe_helper: bool = False, **kwargs) -> None:
        self.metadata_namespace = metadata_namespace
        self.pe_helper = pe_helper
        self.use_pe_helper = use_pe_helper

    @property
    def metadata_namespace(self) -> Optional[str]:
        '''
        Returns the metadata namespace, which may be None if not set.
        '''
        return self._metadata_namespace

    @metadata_namespace.setter
    def metadata_namespace(self, namespace: str) -> None:
        '''
        Sets a new metadata namespace

        :todo: validate!
        '''
        self._metadata_namespace = namespace

    @property
    def pe_helper(self) -> Optional[str]:
        '''
        Returns the pe_helper, which may be None if not set.
        '''
        return self._pe_helper

    @pe_helper.setter
    def pe_helper(self, helper: Optional[str]) -> None:
        '''
        Sets the privilege escalation (PE) helper. Some basic checks for existance and executability are performed,
        but these are not sufficient for secure operation and are provided to aid the user in configuring the library.

        :note: This method does not follow symlinks.

        :raises FileNotFoundError: if the helper can't be found or is not executable.
        '''
        if helper is None:
            log.debug('PE helper is None')
            self._pe_helper = None
        else:
            candidate = helper.strip()

            mode = os.lstat(candidate).st_mode
            if not stat.S_ISREG(mode):
                raise FileNotFoundError('PE helper must be a file')
            if not os.access(candidate, os.X_OK):
                raise FileNotFoundError('PE helper must be executable')
            log.debug(f'Setting privilege escalation helper to "{candidate}"')
            self._pe_helper = candidate


def get_zpool(api: str = 'cli', metadata_namespace: Optional[str] = None, **kwargs) -> ZPool:
    '''
    Returns an instance of the desired ZPool API. Default is ``cli``.

    Using this function is an alternative to instantiating one of the implementations yourself and is the recommended
    way to get an instance.

    Example:

    >>> from zfs import get_zpool, ZPool
    >>> type(get_zpool('cli'))
    <class 'zfs.zpool_cli.ZPoolCli'>
    >>> type(get_zpool('native'))
    <class 'zfs.zpool_native.ZPoolNative'>
    >>> isinstance(get_zpool(), ZPool)
    True

    '''
    if api == 'cli':
        from .zpool_cli import ZPoolCli
        return ZPoolCli(metadata_namespace=metadata_namespace, **kwargs)
    if api == 'native':
        from .zpool_native import ZPoolNative
        return ZPoolNative(metadata_namespace=metadata_namespace, **kwargs)
    raise NotImplementedError(f'The api "{api}" has not been implemented.')
