
'''
CLI-based implementation of ZPOOL.
'''

import logging
import shutil

from typing import Any, Dict, Optional
from .types import ZPoolHealth
from .zpool import ZPool

log = logging.getLogger('simplezfs.zpool_cli')


class ZPoolCli(ZPool):
    '''
    ZPOOL interface implementation using the zpool(8) command line utility. For documentation, please see the interface
    :class:`~zfs.zpool.ZPool`. It is recommended to use :func:`~zfs.zfs.get_zpool` to obtain an instance using ``cli``
    as api.

    If ``zpool_exe`` is supplied, it is assumed that it points to the path to the ``zpool(8)`` executable.
    '''
    def __init__(self, *, metadata_namespace: Optional[str] = None, pe_helper: Optional[str] = None,
                 use_pe_helper: bool = False, zpool_exe: Optional[str] = None, **kwargs) -> None:
        super().__init__(metadata_namespace=metadata_namespace, pe_helper=pe_helper, use_pe_helper=use_pe_helper)
        self.find_executable(path=zpool_exe)

    def find_executable(self, path: str = None) -> None:
        '''
        Tries to find the executable ``zpool``. If ``path`` points to an executable, it is used instead of relying on
        the PATH to find it. It does not fall back to searching in PATH if ``path`` does not point to an exeuctable.
        An exception is raised if no executable could be found.

        :param path: Path to an executable to use instead of searching through $PATH.
        :raises OSError: If the executable could not be found.
        '''
        exe_path = path
        if not exe_path:
            exe_path = shutil.which('zpool')

        if not exe_path:
            raise OSError('Could not find the executable')

        self.__exe = exe_path

    @property
    def executable(self) -> str:
        '''
        Returns the executable found by find_executable.
        '''
        return self.__exe

    def parse_pool_structure(self, zpool_list_output: str) -> Dict:
        '''
        Parses the output of ``zpool list -vPHp`` and emits a list of pool structures.
        '''

        plog = logging.getLogger('simplezfs.zpool_cli.zpool_list_parser')

        output = dict()  # type: Dict[str, Dict]
        # holds the current pool name
        pool_name = ''
        # section we're parsing
        state = ''
        vdev_drives = list()
        vdevs = dict()  # type: Dict[str, Any]

        # offset is 0 for zfs 0.7 and 1 for 0.8, due to the added "CKPOINT" field
        # This gets set when we encounter a pool in the output, i.e. the very first line. We don't cate that we set it
        # for every pool we encounter, the value does not change during output.
        offset = 0

        for line in [x.split('\t') for x in zpool_list_output.split('\n')]:
            print(line)
            if len(line) == 1 and not line[0]:
                # caught the last line ending
                plog.debug('ignoring empty line')
                continue
            if not line[0]:
                plog.debug(f'token 0 not set, token 1: {line[1]}')
                # empty first token: parse the members. $state defines what part of the pool we're parsing
                if line[1].startswith('/'):
                    # paths always define either disk or file vdevs
                    plog.debug(f'+ drive {line[1]}')
                    vdev_drives.append(dict(name=line[1], health=ZPoolHealth.from_string(line[9 + offset].strip())))
                else:
                    # everything else defines a combination of disks (aka raidz, mirror etc)
                    if vdev_drives:
                        # if we have pending drives in the list, append them to previous segment as we're starting a
                        # new one, then clear the states
                        plog.debug('end section, save data')
                        print('end section')
                        vdevs['members'] = vdev_drives
                        output[pool_name][state].append(vdevs)
                        vdevs = dict(type='none')
                        vdev_drives = list()
                    vdevs['type'] = line[1]
                    if state not in ('log', 'cache', 'spare'):
                        vdevs['health'] = ZPoolHealth.from_string(line[9 + offset].strip())
                    vdevs['size'] = int(line[2])
                    vdevs['alloc'] = int(line[3])
                    vdevs['free'] = int(line[4])
                    vdevs['frag'] = int(line[6 + offset])
                    vdevs['cap'] = float(line[7 + offset])
                    plog.debug(f'new type: {line[1]}')

            else:
                plog.debug(f'token 0: {line[0]}')
                # A token in the first place defines a new pool or section (log, cache, spare) in the current pool.
                # Append the pending elements to the current pool and state and clear them.
                if vdev_drives:
                    plog.debug(f'have {len(vdev_drives)} vdev_drives, save data')
                    vdevs['members'] = vdev_drives
                    output[pool_name][state].append(vdevs)

                    vdevs = dict(type='none')
                    vdev_drives = list()

                # The first element is either a pool name or a section within the pool
                # these break the format and are not tab separated
                if line[0].startswith('cache'):
                    plog.debug('new section: cache')
                    state = 'cache'
                elif line[0].startswith('log'):
                    plog.debug('new section: log')
                    state = 'log'
                elif line[0].startswith('spare'):
                    plog.debug('new section: spare')
                    state = 'spare'
                else:
                    # new pool name
                    plog.debug(f'new section: drives. new pool: {line[0]}')
                    state = 'drives'
                    pool_name = line[0]

                    # NOTE ZoL v0.7 has 10 fields, v0.8 has 11 (chkpoint)
                    if len(line) == 10:
                        offset = 0
                    else:
                        offset = 1
                    output[pool_name] = {
                        'drives': [],
                        'log': [],
                        'cache': [],
                        'spare': [],
                        'size': int(line[1]),
                        'alloc': int(line[2]),
                        'free': int(line[3]),
                        'chkpoint': ZPoolCli.dash_to_none(line[4]) if len(line) == 11 else None,
                        'expandsz': ZPoolCli.dash_to_none(line[4 + offset].strip()),
                        'frag': int(line[5 + offset]),
                        'cap': float(line[6 + offset]),
                        'dedup': float(line[7 + offset]),
                        'health': ZPoolHealth.from_string(line[8 + offset].strip()),
                        'altroot': ZPoolCli.dash_to_none(line[9 + offset]),
                    }

        if vdev_drives:
            vdevs['members'] = vdev_drives
            output[pool_name][state].append(vdevs)
        return output

    @staticmethod
    def dash_to_none(data: str) -> Optional[str]:
        if data and data != '-':
            return data
        return None
