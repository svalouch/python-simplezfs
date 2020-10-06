
'''
Privilege escalation helpers
'''

import logging
import os
import shutil
import stat
import subprocess
from typing import List

from .exceptions import PEHelperException, ExternalPEHelperException, ValidationError
from .validation import validate_dataset_path, validate_pool_name


class PEHelperBase:
    '''
    Base class for Privilege Escalation (PE) helper implementations.
    '''
    def __init__(self) -> None:
        pass

    def __repr__(self) -> str:
        return '<PEHelperBase>'

    def zfs_mount(self, fileset: str) -> None:
        '''
        Tries to mount ``fileset`` to the location its ``mountpoint`` property points to. It does **not** check if the
        fileset has a valid mountpoint property.

        :raises ValidationError: If parameters do not validate.
        :raises PEHelperException: If errors are encountered when running the helper.
        '''
        raise NotImplementedError(f'{self} has not implemented this function')

    def zfs_set_mountpoint(self, fileset: str, mountpoint: str) -> None:
        '''
        Sets the ``mountpoint`` property of the given ``fileset``.

        :raises ValidationError: If parameters do not validate.
        :raises PEHelperException: If errors are encountered when running the helper.
        '''
        raise NotImplementedError(f'{self} has not implemented this function')

    def zfs_destroy_dataset(self, dataset: str, recursive: bool, force_umount: bool):
        '''
        Destroy the given ``dataset``.

        :raises ValidationError: If parameters do not validate.
        :raises PEHelperException: If errors are encountered when running the helper.
        '''
        raise NotImplementedError(f'{self} has not implemented this function')


class ExternalPEHelper(PEHelperBase):
    '''
    Implementation using an external script to safeguard the operations.
    '''
    def __init__(self, executable: str) -> None:
        super().__init__()

        self.log = logging.getLogger('simplezfs.pe_helper.external')
        self.executable = executable

    def __repr__(self) -> str:
        return f'<ExternalPEHelper(executable={self.executable})>'

    @property
    def executable(self) -> str:
        return self.__exe

    @executable.setter
    def executable(self, new_exe: str) -> None:
        candidate = new_exe.strip()

        mode = os.lstat(candidate).st_mode
        if not stat.S_ISREG(mode):
            raise FileNotFoundError('PE helper must be a file')
        if not os.access(candidate, os.X_OK):
            raise FileNotFoundError('PE helper must be executable')
        self.log.debug(f'Setting privilege escalation helper to "{candidate}"')
        self.__exe = candidate

    def _execute_cmd(self, cmd: List[str]) -> None:

        proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, encoding='utf-8')
        if proc.returncode != 0 or len(proc.stderr) > 0:

            if proc.returncode == 1:
                self.log.error('General error in PE executable: Wrong parameters or configuration problem')
                msg = 'General error'
            elif proc.returncode == 2:
                msg = 'Parent directory does not exist or is not a directory'
                self.log.error(msg)
            elif proc.returncode == 3:
                msg = 'Parent dataset does not exist'
                self.log.error(msg)
            elif proc.returncode == 4:
                msg = 'Target fileset is not a (grand)child of parent or parent does not exist'
                self.log.error(msg)
            elif proc.returncode == 5:
                msg = 'Mountpoint is not inside the parent directory or otherwise invalid'
                self.log.error(msg)
            elif proc.returncode == 6:
                msg = 'Calling the zfs utility failed'
                self.log.error(msg)
            else:
                msg = f'Unknown / Unhandled error with returncode {proc.returncode}'
                self.log.error(msg)

            raise ExternalPEHelperException(msg, proc.returncode, proc.stdout, proc.stderr)
        else:
            self.log.info('PE Helper successful')
            self.log.debug(f'Return code: {proc.returncode}')
            self.log.debug(f'Stdout: {proc.stdout}')

    def zfs_set_mountpoint(self, fileset: str, mountpoint: str) -> None:
        cmd = [self.__exe, 'set_mountpoint', fileset, mountpoint]
        self._execute_cmd(cmd)


class SudoPEHelper(PEHelperBase):
    '''
    Implementation using ``sudo(8)``.
    '''
    def __init__(self) -> None:
        super().__init__()

        self.log = logging.getLogger('simplezfs.pe_helper.sudo')

        self._find_executable()

    def __repr__(self) -> str:
        return f'<SudoPEHelper(executable={self.__exe})>'

    def _find_executable(self) -> None:
        '''
        Tries to find an executable named ``sudo``.

        :raises FileNotFoundError: if no executable can be found.
        '''
        name = 'sudo'

        candidate = shutil.which(cmd=name)
        if not candidate:
            raise FileNotFoundError('Could not find sudo executable')
        self.__exe = candidate

    def _execute_cmd(self, cmd: List[str]) -> None:
        '''
        Executes the given command through sudo. The call to sudo must not be included in ``cmd``.
        '''
        args = [self.__exe, '-n'] + cmd
        if len(args) < 4:  # "sudo -n zfs mount fileset" is the shortest that makes sense to use with sudo
            raise PEHelperException('Command suspicously short')
        self.log.debug(f'About to run: {args}')

        proc = subprocess.run(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE, encoding='utf-8')
        if proc.returncode != 0 or len(proc.stderr) > 0:
            raise PEHelperException(f'Error running command {" ".join(args)}: {proc.stderr}')
        self.log.debug(f'pe helper command successful. stout: {proc.stdout}')

    def zfs_mount(self, fileset: str) -> None:
        if '/' in fileset:
            validate_dataset_path(fileset)
        else:
            validate_pool_name(fileset)

        self._execute_cmd(['zfs', 'mount', fileset])

    def zfs_set_mountpoint(self, fileset: str, mountpoint: str) -> None:
        if '/' in fileset:
            validate_dataset_path(fileset)
        else:
            validate_pool_name(fileset)
        # TODO validate mountpoint fs

        self._execute_cmd(['zfs', 'set', f'mountpoint={mountpoint}', fileset])

    def zfs_destroy_dataset(self, dataset: str, recursive: bool, force_umount: bool) -> None:
        if '/' not in dataset:
            raise ValidationError('Can\'t remove the pool itself')
        validate_dataset_path(dataset)

        args = ['zfs', 'destroy', '-p']
        if recursive:
            args.append('-r')
        if force_umount:
            args.append('-f')
        args.append(dataset)

        self._execute_cmd(args)
