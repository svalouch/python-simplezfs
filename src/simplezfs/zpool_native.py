
'''
Native, ``libzfs_core``-based implementation.
'''

from typing import Optional
from .zpool import ZPool


class ZPoolNative(ZPool):

    def __init__(self, *, metadata_namespace: Optional[str] = None, **kwargs) -> None:
        super().__init__(metadata_namespace=metadata_namespace)
