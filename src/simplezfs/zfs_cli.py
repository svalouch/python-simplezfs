
'''
CLI-based implementation.
'''

import logging
import os
import shutil
import subprocess
from typing import Dict, List, NoReturn, Optional, Union

from .exceptions import DatasetNotFound, PropertyNotFound
from .pe_helper import PEHelperBase
from .types import Dataset, PEHelperMode, Property, PropertySource
from .validation import (
    validate_dataset_path,
    validate_pool_name,
)
from .zfs import ZFS

log = logging.getLogger('simplezfs.zfs_cli')


class ZFSCli(ZFS):
    '''
    ZFS interface implementation using the zfs(8) command line utility. For documentation, please see the interface
    :class:`~zfs.zfs.ZFS`. It is recommended to use :func:`~zfs.zfs.get_zfs` to obtain an instance using ``cli`` as
    api.

    If ``zfs_exe`` is supplied, it is assumed that it points to the path of the ``zfs(8)`` executable.
    '''
    def __init__(self, *, metadata_namespace: Optional[str] = None, pe_helper: Optional[PEHelperBase] = None,
                 pe_helper_mode: PEHelperMode = PEHelperMode.DO_NOT_USE, zfs_exe: Optional[str] = None,
                 **kwargs) -> None:
        super().__init__(metadata_namespace=metadata_namespace, pe_helper=pe_helper, pe_helper_mode=pe_helper_mode,
                         **kwargs)
        self.find_executable(path=zfs_exe)

    def __repr__(self) -> str:
        return f'<ZFSCli(exe="{self.__exe}", pe_helper="{self._pe_helper}", pe_helper_mode="{self._pe_helper_mode}")>'

    def find_executable(self, path: str = None) -> None:
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
        Returns the zfs executable that was found by find_executable.
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

    def handle_command_error(self, proc: subprocess.CompletedProcess, dataset: str = None) -> NoReturn:
        '''
        Handles errors that occured while running a command.

        :param proc: The result of subprocess.run
        :param dataset: If the error was caused by working with a dataset, specify it to enhance the error message.
        :todo: propper exception!
        :raises DatasetNotFound: If zfs could not find the dataset it was requested to work with.
        :raises PropertyNotFound: If the could not find the property it was asked to work with.
        :raises PermissionError: If zfs denied the operation, or if only root is allowed to carry it out.
        :raises Exception: tmp
        '''
        if 'dataset does not exist' in proc.stderr:
            if dataset:
                raise DatasetNotFound(f'Dataset "{dataset}" not found')
            raise DatasetNotFound('Dataset not found')
        if 'bad property list: invalid property' in proc.stderr:
            if dataset:
                raise PropertyNotFound(f'invalid property on dataset {dataset}')
            raise PropertyNotFound('invalid property')
        if 'permission denied' in proc.stderr:
            raise PermissionError(proc.stderr)
        if 'filesystem successfully created, but it may only be mounted by root' in proc.stderr:
            raise PermissionError(proc.stderr)
        raise Exception(f'Command execution "{" ".join(proc.args)}" failed: {proc.stderr}')

    def _set_property(self, dataset: str, key: str, value: str, is_metadata: bool) -> None:
        '''
        Sets a property, basically using ``zfs set {key}={value} {dataset}```.

        :raises DatasetNotFound: If the dataset does not exist.
        '''
        args = [self.__exe, 'set', f'{key}={value}', dataset]
        log.debug('_set_property: about to run command: %s', args)
        proc = subprocess.run(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE, encoding='utf-8')
        if proc.returncode != 0 or len(proc.stderr) > 0:
            log.debug('_set_propery: command failed, code=%d, stderr="%s"', proc.returncode, proc.stderr.strip())
            self.handle_command_error(proc, dataset=dataset)

    def _get_property(self, dataset: str, key: str, is_metadata: bool) -> Property:
        '''
        Gets a property, basically using ``zfs get -H -p {key} {dataset}``.

        :raises DatasetNotFound: If the dataset does not exist.
        :raises PropertyNotFound: If the property does not exist or is invalid (for native ones).
        '''
        args = [self.__exe, 'get', '-H', '-p', key, dataset]
        log.debug('_get_property: about to run command: %s', args)
        proc = subprocess.run(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE, encoding='utf-8')
        if proc.returncode != 0 or len(proc.stderr) > 0:
            log.debug('_get_property: command failed, code=%d, stderr="%s"', proc.returncode, proc.stderr.strip())
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
        log.debug('_get_properties: about to run command: %s', args)
        proc = subprocess.run(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE, encoding='utf-8')
        if proc.returncode != 0 or len(proc.stderr) > 0:
            log.debug('_get_properties: command faild, code=%d, stderr="%s"', proc.returncode, proc.stderr.strip())
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

    def _create_fileset(self, name: str, properties: Dict[str, str] = None, metadata_properties: Dict[str, str] = None,
                        recursive: bool = False) -> Dataset:

        prop_args: List[str] = []
        if properties:
            for normalkey, normalvalue in properties.items():
                prop_args += ['-o', f'{normalkey}={normalvalue}']
        if metadata_properties:
            for metakey, metavalue in metadata_properties.items():
                prop_args += ['-o', f'{metakey}={metavalue}']

        args = [self.__exe, 'create']
        if recursive:
            args += ['-p']

        args += prop_args
        args += [name]

        log.debug('Executing: %s', args)
        proc = subprocess.run(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE, encoding='utf-8')
        if proc.returncode != 0 or len(proc.stderr) > 0:  # pylint: disable=too-many-nested-blocks
            # check if we tried something only root can do
            if 'filesystem successfully created, but it may only be mounted by root' in proc.stderr:
                log.debug('Command output indicates that we need to run the PE Helper')
                if self.pe_helper_mode != PEHelperMode.DO_NOT_USE:
                    # The mountpoint property may be set, in which case we can run the PE helper. if it is not set,
                    # we'd need to compute it based on the parent, but for now we simply error out.
                    if properties and 'mountpoint' in properties:
                        mopo = properties['mountpoint']
                        if self.pe_helper is not None:
                            test_prop = self.get_property(dataset=name, key='mountpoint', metadata=False)
                            if test_prop.value == mopo:
                                log.info('Fileset "%s" was created with mountpoint set', name)
                            else:
                                log.info('Fileset "%s" was created, using pe_helper to set the mountpoint', name)
                                self.pe_helper.zfs_set_mountpoint(name, mopo)
                            test_prop = self.get_property(dataset=name, key='mounted', metadata=False)
                            if test_prop.value == 'yes':
                                log.info('Fileset "%s" is mounted', name)  # shouldn't be the case with the error above
                            else:
                                log.info('Using pe_helper to mount fileset "%s"', name)
                                self.pe_helper.zfs_mount(name)
                            log.info('Fileset "%s" created successfully (using pe_helper)', name)
                            return self.get_dataset_info(name)

                        msg = 'Fileset created partially but no PE helper set'
                        log.error(msg)
                        raise PermissionError(msg)
                    msg = 'Mountpoint property not set, can\'t run pe_helper'
                    log.error(msg)
                    raise PermissionError(msg)

                log.error('Fileset "%s" was created, but could not be mounted due to lack of permissions. Please set a'
                          ' PE helper and set the mode accordingly, and call "set_mountpoint" with an explicit '
                          'mountpoint to complete the action', name)
                raise PermissionError(proc.stderr)
            try:
                self.handle_command_error(proc)
            except PermissionError:
                log.error('Permission denied, please use "zfs allow" and possibly set a PE Helper')
                raise
        log.info('Filesystem "%s" created successfully', name)
        return self.get_dataset_info(name)

    def _create_snapshot(self, name: str, properties: Dict[str, str] = None,
                         metadata_properties: Dict[str, str] = None, recursive: bool = False) -> Dataset:
        prop_args: List[str] = []
        if properties:
            for normalkey, normalvalue in properties.items():
                prop_args += ['-o', f'{normalkey}={normalvalue}']
        if metadata_properties:
            for metakey, metavalue in metadata_properties.items():
                prop_args += ['-o', f'{metakey}={metavalue}']

        args = [self.__exe, 'create']
        if recursive:
            args += ['-r']

        args += prop_args

        log.debug('Executing %s', args)
        proc = subprocess.run(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE, encoding='utf-8')
        if proc.returncode != 0 or len(proc.stderr) > 0:
            # TODO
            self.handle_command_error(proc)
        return self.get_dataset_info(name)

    def _create_volume(self, name: str, properties: Dict[str, str] = None, metadata_properties: Dict[str, str] = None,
                       sparse: bool = False, size: Optional[int] = None, recursive: bool = False) -> Dataset:
        prop_args: List[str] = []
        if properties:
            for normalkey, normalvalue in properties.items():
                prop_args += ['-o', f'{normalkey}={normalvalue}']
        if metadata_properties:
            for metakey, metavalue in metadata_properties.items():
                prop_args += ['-o', f'{metakey}={metavalue}']

        assert size is not None

        args = [self.__exe, 'create']
        if sparse:
            args += ['-s']
        if recursive:
            args += ['-p']
        # [-b blocksize] is set using properties

        args += prop_args

        args += ['-V', str(size), name]

        log.debug('Executing %s', args)
        proc = subprocess.run(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE, encoding='utf-8')
        if proc.returncode != 0 or len(proc.stderr) > 0:
            # TODO
            self.handle_command_error(proc)
        return self.get_dataset_info(name)

    def _create_bookmark(self, snapshot: str, name: str) -> Dataset:
        validate_dataset_path(snapshot)
        raise NotImplementedError()

    def _destroy_dataset(self, dataset: str, *, recursive: bool = False, force_umount: bool = False) -> None:
        args = [self.__exe, 'destroy', '-p']
        if recursive:
            args.append('-r')
        if force_umount:
            args.append('-f')
        args.append(dataset)

        log.debug(f'executing: {args}')
        if self.pe_helper is not None and self.pe_helper_mode == PEHelperMode.USE_PROACTIVE:
            test_prop = self.get_property(dataset, 'mounted')
            if test_prop.value == 'yes':
                log.info('Fileset is mounted, proactively unmounting using pe_helper')
                self.pe_helper.zfs_umount(dataset)

        proc = subprocess.run(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE, encoding='utf-8')
        if proc.returncode != 0 or len(proc.stderr) > 0:
            log.debug('destroy_dataset: command failed, code=%d, stderr="%s"', proc.returncode, proc.stderr.strip())
            if 'has children' in proc.stderr:
                if recursive:
                    log.error('Dataset "%s" has children and recursive was given, please report this', dataset)
                else:
                    log.warning('Dataset "%s" has children and thus cannot be destroyed without recursive=True',
                                dataset)
                    raise Exception
            # three possible messages: (zfs destroy -p -r [-f] $fileset_with_snapshots)
            # * 'cannot destroy snapshots: permission denied'
            # * 'umount: only root can use "--types" option'
            # The latter seems to originate from having `destroy` and `mount` via `zfs allow`.
            elif ('cannot destroy' in proc.stderr and 'permission denied' in proc.stderr) or \
                    'only root can' in proc.stderr:
                log.debug('Command output indicates that we need to run the PE Helper')
                if self.pe_helper_mode != PEHelperMode.DO_NOT_USE:
                    if self.pe_helper is not None:
                        log.info('Using pe_helper to remove %s', dataset)
                        self.pe_helper.zfs_destroy_dataset(dataset, recursive, force_umount)
                        log.info('Dataset "%s" destroyed (using pe_helper)', dataset)
                    else:
                        msg = 'Cannot destroy: No pe_helper set'
                        log.error(msg)
                        raise PermissionError(msg)
                else:
                    log.error('Dataset "%s" can\'t be destroyed due to lack of permissions. Please set a PE helper',
                              dataset)
                    raise PermissionError(proc.stderr)
            # Another one new with OpenZFS 2.0 that does not indicate what the problem is
            # * 'cannot unmount '${fileset}': unmount failed'
            elif 'cannot umount' in proc.stderr and 'umount failed' in proc.stderr:
                if self.pe_helper is not None and self.pe_helper_mode != PEHelperMode.DO_NOT_USE:
                    log.info('Destroy could not unmount, retrying using pe_helper')
                    self.pe_helper.zfs_umount(dataset)
                    self._destroy_dataset(dataset, recursive=recursive, force_umount=force_umount)
                else:
                    msg = 'Umounting failed and pe_helper is not allowed'
                    log.error(msg)
                    raise PermissionError(msg)

            else:
                try:
                    self.handle_command_error(proc)
                except PermissionError:
                    log.error('Permission denied, please use "zfs allow"')
                    raise
        else:
            log.info('Dataset destroyed successfully')

    # def _mount_umount_fileset(self, fileset: str, mount: bool) -> None:

    #     if '/' in fileset:
    #         validate_dataset_path(fileset)
    #     else:
    #         validate_pool_name(fileset)

    #     if not self.dataset_exists(fileset):
    #         raise DatasetNotFound('The fileset could not be found')

    #     test_prop = self.get_property(dataset=fileset, key='mounted')
    #     if mount:
    #         if test_prop.value == 'yes':
    #             log.warning('Fileset "%s" is already mounted', fileset)
    #         else:
    #             pass
    #     else:
    #         if test_prop.value != 'yes':
    #             log.warning('Fileset "%s" is not mounted', fileset)
    #         else:
    #             pass
