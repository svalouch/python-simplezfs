
'''
Native, ``libzfs_core``-based implementation.
'''

from typing import Optional
from .zpool import ZPool


class ZPoolNative(ZPool):
    '''
    ZPool interface implementation using the libzfs_core python bindings. For documentation, please see the interface
    :class:`~zfs.zpool.ZPool`. It is recommended to use :func:`~zfs.zpool.get_zpool` to obtain an instance, using
    ``native`` as api.
    '''
    def __init__(self, *, metadata_namespace: Optional[str] = None, pe_helper: Optional[str] = None,
                 use_pe_helper: bool = False, **kwargs) -> None:
        super().__init__(metadata_namespace=metadata_namespace, pe_helper=pe_helper, use_pe_helper=use_pe_helper)
