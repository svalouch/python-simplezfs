
'''
Python ZFS API.
'''

__version__ = '0.0.1'

from .zfs import ZFS, get_zfs
from .zpool import ZPool, get_zpool

__all__ = [
    'ZFS',
    'get_zfs',
    'ZPool',
    'get_zpool',
]
