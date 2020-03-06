
'''
Native, ``libzfs_core``-based implementation.
'''

from typing import List, Optional
import logging

from .types import Property
from .zfs import ZFS

log = logging.getLogger('simplezfs.zfs_native')


class ZFSNative(ZFS):
    '''
    ZFS interface implementation using the libzfs_core python bindings. For documentation, please see the interface
    :class:`~zfs.zfs.ZFS`. It is recommended to use :func:`~zfs.zfs.get_zfs` to obtain an instance, using ``native``
    as api.
    '''
    def __init__(self, *, metadata_namespace: Optional[str] = None, pe_helper: Optional[str] = None,
                 use_pe_helper: bool = False, **kwargs) -> None:
        super().__init__(metadata_namespace=metadata_namespace)

    def __repr__(self) -> str:
        return f'<ZFSNative(pe_helper="{self._pe_helper}", use_pe_helper="{self._use_pe_helper}")>'

    def set_property(self, dataset: str, key: str, value: str, *, metadata: bool = False,
                     overwrite_metadata_namespace: Optional[str] = None) -> None:
        raise NotImplementedError

    def get_property(self, dataset: str, key: str, *, metadata: bool = False,
                     overwrite_metadata_namespace: Optional[str] = None) -> Property:
        raise NotImplementedError

    def get_properties(self, dataset: str, *, include_metadata: bool = False) -> List[Property]:
        raise NotImplementedError
