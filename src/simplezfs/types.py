
'''
Type declarations
'''

from enum import Enum, unique
from typing import NamedTuple, Optional


@unique
class DatasetType(str, Enum):
    '''
    Enumeration of dataset types that ZFS supports.
    '''
    #: Dataset is an ordinary fileset
    FILESET = 'fileset'
    #: Dataset is a ZVOL
    VOLUME = 'volume'
    #: Dataset is a snapshot
    SNAPSHOT = 'snapshot'
    #: Dataset is a bookmark
    BOOKMARK = 'bookmark'

    @staticmethod
    def from_string(value: str) -> 'DatasetType':
        '''
        Helper to convert a string to an instance.

        :param value: The string to converts.
        :returns: The enum value
        :raises ValueError: If the supplied value is not found in the enumeration.
        '''
        if not isinstance(value, str):
            raise ValueError('only string types allowed')
        val = value.lower()
        if val == 'fileset':
            return DatasetType.FILESET
        elif val == 'volume':
            return DatasetType.VOLUME
        elif val == 'snapshot':
            return DatasetType.SNAPSHOT
        elif val == 'bookmark':
            return DatasetType.BOOKMARK
        else:
            raise ValueError(f'Value {value} is not a valid DatasetType')


class Dataset(NamedTuple):
    '''
    Container describing a single dataset.
    '''
    #: Name of the dataset (excluding the path)
    name: str
    #: Full path to and including the dataset itself
    full_path: str
    #: Pool name
    pool: str
    #: Parent dataset, or None for the topmost dataset (pool)
    parent: Optional[str]
    #: Dataset type
    type: DatasetType


@unique
class PropertySource(str, Enum):
    '''
    Enumeration of the valid property sources in ZFS.
    '''
    #: Property is at default
    DEFAULT = 'default'
    #: Property was inerited
    INHERITED = 'inherited'
    #: Property is temporary
    TEMPORARY = 'temporary'
    #: Property is set to the value that it had due to the sender of a "zfs send/receive" operation having it set this way.
    RECEIVED = 'received'
    #: Property is set on the dataset in question
    NONE = 'none'

    @staticmethod
    def from_string(value: str) -> 'PropertySource':
        '''
        Helper to convert a string to an instance.

        :param value: The string to convert.
        :returns: The enum value.
        :raises ValueError: If the supplied value is not found in the enumeration.
        '''
        if not isinstance(value, str):
            raise ValueError('only string types allowed')
        val = value.lower()
        if val == 'default':
            return PropertySource.DEFAULT
        elif val == 'inherited':
            return PropertySource.INHERITED
        elif val == 'temporary':
            return PropertySource.TEMPORARY
        elif val == 'received':
            return PropertySource.RECEIVED
        elif val == 'none':
            return PropertySource.NONE
        else:
            raise ValueError(f'Value {value} is not a valid PropertySource')


class Property(NamedTuple):
    '''
    Container for a single ZFS property.
    '''
    #: Key or name of the property (excluding namespace for non-native properties)
    key: str
    #: Value of the property
    value: str
    #: Source of the property value
    source: PropertySource = PropertySource.NONE
    #: Namespace name of the property, None for native properties
    namespace: Optional[str] = None


class VDevType(str, Enum):
    '''
    Type of a vdev. vdevs are either one of two storages (disk or file) or one of the special parts (mirror, raidz*,
    spare, log, dedup, special and cache).
    When reading zpool output, it is not always clear what type a vdev is when it comes to "disk" vs. "file", so a
    special type "DISK_OR_FILE" is used. This type is invalid when setting values.
    '''
    DISK = 'disk'
    FILE = 'file'
    DISK_OR_FILE = 'disk_or_file'
    MIRROR = 'mirror'
    RAIDZ1 = 'raidz1'
    RAIDZ2 = 'raidz2'
    RAIDZ3 = 'raidz3'
    SPARE = 'spare'
    LOG = 'log'
    DEDUP = 'dedup'
    SPECIAL = 'special'
    CACHE = 'cache'


class ZPoolHealth(str, Enum):
    '''

    '''
    ONLINE = 'ONLINE'
    DEGRADED = 'DEGRADED'
    FAULTED = 'FAULTED'
    OFFLINE = 'OFFLINE'
    UNAVAIL = 'UNAVAIL'
    REMOVED = 'REMOVED'
    #: This one is used for spares
    AVAIL = 'AVAIL'

    @staticmethod
    def from_string(value: str) -> 'ZPoolHealth':
        '''
        Helper to convert a string to an instance.

        :param value: The string to convert.
        :returns: The enum value.
        :raises ValueError: If the supplied value is not found in the enumeration.
        '''
        if not isinstance(value, str):
            raise ValueError('only string types are allowed')
        val = value.lower()
        if val == 'online':
            return ZPoolHealth.ONLINE
        elif val == 'degraded':
            return ZPoolHealth.DEGRADED
        elif val == 'faulted':
            return ZPoolHealth.FAULTED
        elif val == 'offline':
            return ZPoolHealth.OFFLINE
        elif val == 'unavail':
            return ZPoolHealth.UNAVAIL
        elif val == 'removed':
            return ZPoolHealth.REMOVED
        elif val == 'avail':
            return ZPoolHealth.AVAIL
        else:
            raise ValueError(f'Value {value} is not a valid ZPoolHealth')
