
from typing import Optional


class ZPool:
    '''
    ZPool interface class. This API generally covers only the zpool(8) tool, for zfs(8) please see class :class:`~ZFS`.

    **ZFS implementation**

    There are two ways how the API actually communicates with the ZFS filesystem:

    * Using the CLI tools
    * Using the native API

    When creating an instance of this class, select one or the other as the ``api`` argument.
    '''
    def __init__(self, *, metadata_namespace: Optional[str] = None, **kwargs) -> None:
        self.metadata_namespace = metadata_namespace

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
    elif api == 'native':
        from .zpool_native import ZPoolNative
        return ZPoolNative(metadata_namespace=metadata_namespace, **kwargs)
    raise NotImplementedError(f'The api "{api}" has not been implemented.')
