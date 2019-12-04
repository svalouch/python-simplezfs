
'''
Native, ``libzfs_core``-based implementation.
'''

from typing import Optional
from .zpool import ZPool


class ZPoolNative(ZPool):

    def __init__(self, *, metadata_namespace: Optional[str] = None, pe_helper: Optional[str] = None,
            use_pe_helper: bool = False, **kwargs) -> None:
        super().__init__(metadata_namespace=metadata_namespace, pe_helper=pe_helper, use_pe_helper=use_pe_helper)
