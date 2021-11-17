
'''
ZPOOL frontend API
'''

import logging
import os
import stat
from typing import Optional

from .pe_helper import PEHelperBase
from .types import PEHelperMode

log = logging.getLogger('simplezfs.zpool')


class ZPool:
    '''
    ZPool interface class. This API generally covers only the zpool(8) tool, for zfs(8) please see class :class:`~ZFS`.

    **ZFS implementation**

    There are two ways how the API actually communicates with the ZFS filesystem:

    * Using the CLI tools
    * Using the native API

    When creating an instance of this class, select one or the other as the ``api`` argument.


    **Properties and Metadata**

    Please see the documentation for :class:`~simplezfs.zfs.ZFS` for native and metadata properties.

    :param metadata_namespace: Default namespace
    :param pe_helper: Privilege escalation (PE) helper to use for actions that require elevated privileges (root).
    :param pe_helper_mode: How and when to use the PEHelper. Defaults to not using it at all.
    :param kwargs: Extra arguments, ignored
    '''
    def __init__(self, *, metadata_namespace: Optional[str] = None, pe_helper: Optional[PEHelperBase] = None,
                 pe_helper_mode: PEHelperMode = PEHelperMode.DO_NOT_USE, **kwargs) -> None:
        self.metadata_namespace = metadata_namespace
        self.pe_helper = pe_helper
        self.pe_helper_mode = pe_helper_mode

    def __repr__(self) -> str:
        return f'<ZPool(pe_helper="{self._pe_helper}", pe_helper_mode="{self._pe_helper_mode}")>'

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
    def pe_helper(self) -> Optional[PEHelperBase]:
        '''
        Returns the pe_helper, which may be None if not set.
        '''
        return self._pe_helper

    @pe_helper.setter
    def pe_helper(self, helper: Optional[PEHelperBase]) -> None:
        '''
        Sets the privilege escalation (PE) helper. Supply ``None`` to unset it.
        '''
        if helper is None:
            log.debug('PE helper is None')
        self._pe_helper = helper

    @property
    def pe_helper_mode(self) -> PEHelperMode:
        '''
        Returns whether the privilege escalation (PE) helper should be used and when. If the helper has not been set,
        this property evaluates to ``False``.
        '''
        if self._pe_helper is None:
            return PEHelperMode.DO_NOT_USE
        return self._pe_helper_mode

    @pe_helper_mode.setter
    def pe_helper_mode(self, mode: PEHelperMode) -> None:
        '''
        Sets the privilege escalation (PE) helper mode.
        '''
        self._pe_helper_mode = mode

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
