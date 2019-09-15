
'''
CLI-based implementation.
'''

from typing import List, Optional, Union
import logging
import os
import shutil
import subprocess

from .exceptions import DatasetNotFound, PropertyNotFound, ValidationError
from .types import Property, Dataset, DatasetType
from .validation import (
    validate_dataset_path,
    validate_metadata_property_name,
    validate_native_property_name,
    validate_pool_name,
)
from .zfs import ZFS

log = logging.getLogger('zfs.zfs_cli')


class ZFSCli(ZFS):
    '''
    ZFS interface implementation using the zfs(8) command line utility. For documentation, please see the interface
    :class:`~zfs.zfs.ZFS`. It is recommended to use :func:`~zfs.zfs.get_zfs` to obtain an instance using ``cli`` as
    api.

    If ``zfs_exe`` is supplied, it is assumed that it points to the path of the ``zfs(8)`` executable.
    '''
    def __init__(self, *, metadata_namespace: Optional[str] = None, zfs_exe: Optional[str] = None, **kwargs) -> None:
        super().__init__(metadata_namespace=metadata_namespace)
        self.find_executable(path=zfs_exe)

    def find_executable(self, path: str = None):
        '''
        Tries to find the executable ``zfs(8)``. If ``path`` points to an executable, it is used instead of relying on
        the PATH to find it. It does not fall back to searching in $PATH of ``path`` does not point to an executable.
        An exception is raised if no executable could be found.

        :param path: Path to the executable, used blindly if supplied.
        :raises OSError: If the executable could not be found.
        '''
        exe_path = path
        if not exe_path:
            exe_path = shutil.which('zfs')

        if not exe_path:
            raise OSError('Could not find executable')

        self.__exe = exe_path

    @property
    def executable(self) -> str:
        '''
        Returns the zfs executable that was found by find_executable
        '''
        return self.__exe

    @staticmethod
    def parse_dataset_identifier(name: str) -> Dataset:
        '''
        Parses a dataset identifier like ``pool/system/root@initial`` to a :class:`~simplezfs.types.Dataset`.

        :param name: The name to parse.
        :return: The dataset.
        :raises ValidationError: If the argument is not valid or the argument was a pool.
        '''
        if '/' in name:
            validate_dataset_path(name)
            tokens = name.split('/')
            ds_name = tokens[-1]
            ds_parent = '/'.join(tokens[:-1])  # type: Optional[str]
            ds_pool = tokens[0]
        else:
            validate_pool_name(name)
            ds_name = name
            ds_parent = None
            ds_pool = name

        if '@' in ds_name:
            ds_type = DatasetType.SNAPSHOT
        elif '#' in ds_name:
            ds_type = DatasetType.BOOKMARK
        elif ZFSCli.is_zvol(name):
            ds_type = DatasetType.VOLUME
        else:
            ds_type = DatasetType.FILESET
        return Dataset(name=ds_name, parent=ds_parent, type=ds_type, full_path=name, pool=ds_pool)

    @staticmethod
    def is_zvol(name: str) -> bool:
        '''
        Resolves the given name in the dev filesystem. If it is found beneath ``/dev/zvol``, **True** is returned.

        :param name: The name of the suspected volume
        :return: Whether the name represents a volume rather than a fileset.
        :raises ValidationError: If validation fails.
        '''
        if '/' in name:
            validate_dataset_path(name)
        else:
            validate_pool_name(name)
        return os.path.exists(os.path.join('/dev/zvol', name))

    def list_datasets(self, *, parent: Union[str, Dataset] = None) -> List[Dataset]:
        '''
        :todo: ability to limit to a pool (path validator discards pool-only arguments)
        :todo: find a way to tell the user to use ZPool for pools if only a pool is given
        '''
        # zfs list -H -r -t all
        args = [self.__exe, 'list', '-H', '-r', '-t', 'all']
        if parent:
            # zfs list -H -r -t all $parent
            if isinstance(parent, Dataset):
                parent_path = parent.full_path
            else:
                parent_path = parent
            # as the upmost parent is a dataset as well, but not a path, we need to handle this case
            if '/' not in parent_path:
                validate_pool_name(parent_path)
            else:
                validate_dataset_path(parent_path)
            args.append(parent_path)
        # python 3.7 can use capture_output=True
        proc = subprocess.run(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE, encoding='utf-8')
        if proc.returncode != 0 or len(proc.stderr) > 0:
            if parent:
                self.handle_command_error(proc, dataset=args[-1])
            else:
                self.handle_command_error(proc)
        res = list()
        for line in proc.stdout.strip().split('\n'):
            # format is NAME, USED, AVAIL, REFER, MOUNTPOINT, we only care for the name here
            name = line.split('\t')[0]
            res.append(ZFSCli.parse_dataset_identifier(name.strip()))
        return res

    def handle_command_error(self, proc: subprocess.CompletedProcess, dataset: str = None) -> None:
        '''
        Handles errors that occured while running a command.

        :param proc: The result of subprocess.run
        :param dataset: If the error was caused by working with a dataset, specify it to enhance the error message.
        :todo: propper exception!
        :raises DatasetNotFound: If zfs could not find the dataset it was requested to work with.
        :raises PropertyNotFound: If the could not find the property it was asked to work with.
        :raises Exception: tmp
        '''
        if 'dataset does not exist' in proc.stderr:
            if dataset:
                raise DatasetNotFound(f'Dataset "{dataset}" not found')
            raise DatasetNotFound('Dataset not found')
        elif 'bad property list: invalid property' in proc.stderr:
            if dataset:
                raise PropertyNotFound(f'invalid property on dataset {dataset}')
            else:
                raise PropertyNotFound('invalid property')
        raise Exception(f'Command execution "{" ".join(proc.args)}" failed: {proc.stderr}')

    def _set_property(self, dataset: str, key: str, value: str, is_metadata: bool) -> None:
        '''
        Sets a property, basically using ``zfs set {key}={value} {dataset}```.

        :raises DatasetNotFound: If the dataset does not exist.
        '''
        args = [self.__exe, 'set', f'{key}={value}', dataset]
        log.debug(f'_set_property: about to run command: {args}')
        proc = subprocess.run(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE, encoding='utf-8')
        if proc.returncode != 0 or len(proc.stderr) > 0:
            log.debug(f'_set_propery: command failed, code={proc.returncode}, stderr="{proc.stderr}"')
            self.handle_command_error(proc, dataset=dataset)

    def _get_property(self, dataset: str, key: str, is_metadata: bool) -> Property:
        '''
        Gets a property, basically using ``zfs get -H -p {key} {dataset}``.

        :raises DatasetNotFound: If the dataset does not exist.
        :raises PropertyNotFound: If the property does not exist or is invalid (for native ones).
        '''
        args = [self.__exe, 'get', '-H', '-p', key, dataset]
        log.debug(f'_get_property: about to run command: {args}')
        proc = subprocess.run(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE, encoding='utf-8')
        if proc.returncode != 0 or len(proc.stderr) > 0:
            log.debug(f'_get_property: command failed, code={proc.returncode}, stderr="{proc.stderr}"')
            self.handle_command_error(proc, dataset=dataset)
        name, prop_name, prop_value, prop_source = proc.stdout.strip().split('\t')
        if name != dataset:
            raise Exception(f'expected name "{dataset}", but got {name}')

        if is_metadata and prop_value == '-' and prop_source == '-':
            raise PropertyNotFound(f'Property {key} was not found')

        namespace = None
        if is_metadata:
            namespace = prop_name.split(':')[0]

        return Property(key=prop_name, value=prop_value, source=prop_source, namespace=namespace)
        
    def _get_properties(self, dataset: str, include_metadata: bool = False) -> List[Property]:
        '''
        Gets all properties from a dataset, basically running ``zfs get -H -p all {dataset}``.
        
        :raises DatasetNotFound: If the dataset does not exist.
        '''
        args = [self.__exe, 'get', '-H', '-p', 'all', dataset]
        log.debug(f'_get_properties: about to run command: {args}')
        proc = subprocess.run(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE, encoding='utf-8')
        if proc.returncode != 0 or len(proc.stderr) > 0:
            log.debug(f'_get_properties: command faild, code={proc.returncode}, stderr="{proc.stderr}"')
            self.handle_command_error(proc, dataset=dataset)
        res = list()
        for line in proc.stdout.split('\n'):
            if line:
                _, prop_name, prop_value, prop_source = line.strip().split('\t')
                if ':' in prop_name:
                    if include_metadata:
                        namespace = prop_name.split(':')[0]
                        prop_name = prop_name.lstrip(f'{namespace}:')
                        res.append(Property(key=prop_name, value=prop_value, source=prop_source, namespace=namespace))
                else:
                    res.append(Property(key=prop_name, value=prop_value, source=prop_source, namespace=None))
        return res
