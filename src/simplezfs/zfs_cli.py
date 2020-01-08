
'''
CLI-based implementation.
'''

from typing import Dict, List, Optional, Union
import logging
import os
import shutil
import subprocess

from .exceptions import DatasetNotFound, PEHelperException, PropertyNotFound, ValidationError
from .types import Dataset, DatasetType, Property, PropertySource
from .validation import (
    validate_dataset_path,
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
    def __init__(self, *, metadata_namespace: Optional[str] = None, pe_helper: Optional[str] = None,
                 use_pe_helper: bool = False, zfs_exe: Optional[str] = None, **kwargs) -> None:
        super().__init__(metadata_namespace=metadata_namespace)
        self.find_executable(path=zfs_exe)

    def __repr__(self) -> str:
        return f'<ZFSCli(exe="{self.__exe}", pe_helper="{self._pe_helper}", use_pe_helper="{self._use_pe_helper}")>'

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

    def get_dataset_info(self, name: str) -> Dataset:
        if '/' not in name:
            validate_pool_name(name)
        else:
            validate_dataset_path(name)
        args = [self.__exe, 'list', '-H', '-t', 'all', name]
        proc = subprocess.run(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE, encoding='utf-8')
        if proc.returncode != 0 or len(proc.stderr) > 0:
            self.handle_command_error(proc)
        return Dataset.from_string(proc.stdout.split('\t')[0].strip())

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
            res.append(Dataset.from_string(name.strip()))
        return res

    def set_mountpoint(self, fileset: str, mountpoint: str, *, use_pe_helper: Optional[bool] = False) -> None:
        real_use_pe_helper = use_pe_helper if use_pe_helper is not None else self.use_pe_helper
        ds_type = self.get_property(fileset, 'type')
        if ds_type != 'filesystem':
            raise ValidationError('Given fileset is not a filesystem, can\'t set mountpoint')

        if not real_use_pe_helper:
            self.set_property(fileset, 'mountpoint', mountpoint)
        else:
            if not self.pe_helper:
                raise ValidationError('PE helper should be used, but is not defined')

            args = [self.pe_helper, 'set_mountpoint', fileset, mountpoint]
            log.debug(f'set_mountpoint: executing {args}')
            proc = subprocess.run(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE, encoding='utf-8')
            log.debug(f'set_mountpoint returncode: {proc.returncode}')
            log.debug(f'set_mountpoint stdout: {proc.stdout}')
            log.debug(f'set_mountpoint stderr: {proc.stderr}')
            # TODO log output
            if proc.returncode != 0 or len(proc.stderr) > 0:
                self.handle_command_error(proc, fileset)

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
        elif 'permission denied' in proc.stderr:
            raise PermissionError(proc.stderr)
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

        property_source = PropertySource.from_string(prop_source)

        return Property(key=prop_name, value=prop_value, source=property_source, namespace=namespace)

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
                property_source = PropertySource.from_string(prop_source)
                if ':' in prop_name:
                    if include_metadata:
                        namespace = prop_name.split(':')[0]
                        prop_name = prop_name.lstrip(f'{namespace}:')
                        res.append(Property(key=prop_name, value=prop_value, source=property_source,
                                            namespace=namespace))
                else:
                    res.append(Property(key=prop_name, value=prop_value, source=property_source, namespace=None))
        return res

    def _create_dataset(
        self,
        name: str,
        *,
        dataset_type: DatasetType,
        properties: Dict[str, str] = None,
        metadata_properties: Dict[str, str] = None,
        sparse: bool = False,
        size: Optional[int] = None,
        recursive: bool = False,
    ) -> Dataset:

        if dataset_type == DatasetType.BOOKMARK:
            raise ValidationError('Bookmarks can\'t be created by this function')

        # assemble the options list for properties
        prop_args: List[str] = []
        if properties:
            for nk, nv in properties.items():
                prop_args += ['-o', f'{nk}={nv}']
        if metadata_properties:
            for mk, mv in metadata_properties.items():
                prop_args += ['-o', f'{mk}={mv}']

        if dataset_type == DatasetType.FILESET:
            assert size is None, 'Filesets have no size'
            assert sparse is False, 'Filesets cannot be sparse'

            # try on our own first, then depending on settings use the pe helper
            args = [self.__exe, 'create']
            if recursive:
                args += ['-p']

            args += prop_args
            args += [name]

            log.debug(f'executing: {args}')
            proc = subprocess.run(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE, encoding='utf-8')
            if proc.returncode != 0 or len(proc.stderr) > 0:
                # check if we tried something only root can do
                if 'filesystem successfully created, but it may only be mounted by root' in proc.stderr:
                    if self.use_pe_helper:
                        # The mountpoint property may be set, in which case we can run the PE helper. If it is not
                        # set, we'd need to compute it based on the parent, but for now we simply error out.
                        try:
                            mp = properties['mountpoint']
                        except KeyError:
                            msg = 'Mountpoint property not set, can\'t run pe_helper'
                            log.error(msg)
                            raise PermissionError(msg)

                        log.info(f'Fileset {name} was created, using pe_helper to set the mountpoint')
                    else:
                        log.info(f'Fileset {name} was created, but could not be mounted due to not running as root')
                        raise PermissionError(proc.stderr)

            if self.use_pe_helper:
                try:
                    mp = properties['mountpoint']
                except KeyError:
                    raise ValidationError('Mountpoint not found in properties')
                self._execute_pe_helper('create', recursive=recursive, mountpoint=properties['mountpoint'], name=name)
            else:
                args = [self.__exe, 'create']

                if recursive:
                    args += ['-p']

                args += [name]
                print(f'Executing {args}')

        elif dataset_type == DatasetType.VOLUME:
            assert size is not None

            args = [self.__exe, 'create']
            if sparse:
                args += ['-s']
            if recursive:
                args += ['-p']
            # [-b blocksize] is set using properties

            args += prop_args

            args += ['-V', str(size), name]

            print(f'Executing {args}')

        elif dataset_type == DatasetType.SNAPSHOT:
            assert size is None, 'Snapshots have no size'
            assert sparse is False, 'Snapshots can\'t be sparse'

            args = [self.__exe, 'snapshot', *prop_args, name]
            print(f'Executing {args}')

        raise NotImplementedError()

    def create_bookmark(self, snapshot: str, name: str) -> Dataset:
        validate_dataset_path(snapshot)
        raise NotImplementedError()
