
'''
Tests the ZFSCli class, non-distructive version.
'''

from unittest.mock import patch
import pytest
import subprocess

from simplezfs.types import Dataset, DatasetType
from simplezfs.zfs_cli import ZFSCli


class TestZFSCli:

    @patch('shutil.which')
    def test_init_noparam(self, which):
        '''
        This should result in a ZFSCli instance. It does, however, search a ZFS binary and will fail if there is none.
        To remedy this, we patch ``shutil.which``.
        '''
        which.return_value = '/bin/true'
        assert ZFSCli()
        which.assert_called_once_with('zfs')

    ########################

    @patch('os.path.exists')
    def test_is_zvol_ok_exists(self, exists):

        exists.return_value = True
        assert ZFSCli.is_zvol('newpool/newvol')

    @patch('os.path.exists')
    def test_is_zvol_ok_not_exists(self, exists):

        exists.return_value = False
        assert not ZFSCli.is_zvol('newpool/newfileset')

    @patch('os.path.exists')
    def test_is_zvol_ok_not_exists_pool(self, exists):
        '''
        Tests that is_zvol can cope with pool-level filesets
        '''

        exists.return_value = False
        assert not ZFSCli.is_zvol('newpool')

    ##########################################################################

    @patch('shutil.which')
    def test_find_executable_parameter(self, which):
        which.return_value = None

        zfs = ZFSCli(zfs_exe='asdf')
        assert zfs.executable == 'asdf'

    @patch('shutil.which')
    def test_find_executable_path(self, which):
        which.return_value = 'test_return'

        zfs = ZFSCli()
        assert zfs.executable == 'test_return'

    @patch('shutil.which')
    def test_find_executable_path_fail(self, which):
        which.return_value = None

        with pytest.raises(OSError) as excinfo:
            ZFSCli()
        assert 'not find executable' in str(excinfo.value)

    ##########################################################################

    @patch('subprocess.run')
    def test_get_dataset_info_happy_dataset(self, subproc):
        test_stdout = 'rpool/test	105M	142G	192K	none'
        subproc.return_value = subprocess.CompletedProcess(args=[], returncode=0, stdout=test_stdout, stderr='')

        zfs = ZFSCli(zfs_exe='/bin/true')
        data = zfs.get_dataset_info('rpool/test')
        subproc.assert_called_once()
        assert ['/bin/true', 'list', '-H', '-t', 'all', 'rpool/test'] == subproc.call_args[0][0]
        assert data.pool == 'rpool'
        assert data.parent == 'rpool'
        assert data.name == 'test'
        assert data.type == DatasetType.VOLUME
        assert data.full_path == 'rpool/test'

    @patch('subprocess.run')
    def test_get_dataset_info_happy_pool(self, subproc):
        test_stdout = 'rpool	105M	142G	192K	none'
        subproc.return_value = subprocess.CompletedProcess(args=[], returncode=0, stdout=test_stdout, stderr='')

        zfs = ZFSCli(zfs_exe='/bin/true')
        data = zfs.get_dataset_info('rpool')
        subproc.assert_called_once()
        assert ['/bin/true', 'list', '-H', '-t', 'all', 'rpool'] == subproc.call_args[0][0]
        assert data.pool == 'rpool'
        assert data.parent is None
        assert data.name == 'rpool'
        assert data.type == DatasetType.VOLUME
        assert data.full_path == 'rpool'

    ##########################################################################

    @patch('subprocess.run')
    def test_list_dataset_noparent_happy(self, subproc):
        test_stdout = '''tank	213G	13.3G	96K	none
tank/system	128G	13.3G	96K	none
tank/system/home	86.6G	13.3G	86.6G	/home
tank/system/root	14.9G	13.3G	14.9G	/'''
        subproc.return_value = subprocess.CompletedProcess(args=[], returncode=0, stdout=test_stdout, stderr='')

        zfs = ZFSCli(zfs_exe='/bin/true')
        lst = zfs.list_datasets()
        subproc.assert_called_once()
        assert ['/bin/true', 'list', '-H', '-r', '-t', 'all'] == subproc.call_args[0][0]
        assert len(lst) == 4
        assert lst[0].pool == 'tank'
        assert lst[0].parent is None
        assert lst[1].name == 'system'
        assert lst[1].parent == 'tank'
        assert lst[1].type == DatasetType.FILESET
        assert lst[3].name == 'root'
        assert lst[3].full_path == 'tank/system/root'

    @patch('subprocess.run')
    def test_list_dataset_parent_pool_str_happy(self, subproc):
        test_stdout = '''tank	213G	13.3G	96K	none
tank/system	128G	13.3G	96K	none
tank/system/home	86.6G	13.3G	86.6G	/home
tank/system/root	14.9G	13.3G	14.9G	/'''
        subproc.return_value = subprocess.CompletedProcess(args=[], returncode=0, stdout=test_stdout, stderr='')

        zfs = ZFSCli(zfs_exe='/bin/true')
        lst = zfs.list_datasets(parent='tank')
        subproc.assert_called_once()
        assert ['/bin/true', 'list', '-H', '-r', '-t', 'all', 'tank'] == subproc.call_args[0][0]
        assert len(lst) == 4
        assert lst[0].pool == 'tank'
        assert lst[0].parent is None
        assert lst[1].name == 'system'
        assert lst[1].parent == 'tank'
        assert lst[1].type == DatasetType.FILESET
        assert lst[3].name == 'root'
        assert lst[3].full_path == 'tank/system/root'

    @patch('subprocess.run')
    def test_list_dataset_parent_pool_dataset_happy(self, subproc):
        '''
        Supplies a dataset as parent.
        '''
        test_stdout = '''tank	213G	13.3G	96K	none
tank/system	128G	13.3G	96K	none
tank/system/home	86.6G	13.3G	86.6G	/home
tank/system/root	14.9G	13.3G	14.9G	/'''
        subproc.return_value = subprocess.CompletedProcess(args=[], returncode=0, stdout=test_stdout, stderr='')

        zfs = ZFSCli(zfs_exe='/bin/true')
        lst = zfs.list_datasets(parent=Dataset(pool='tank', name='system', full_path='tank', parent='tank',
                                               type=DatasetType.FILESET))
        subproc.assert_called_once()
        assert ['/bin/true', 'list', '-H', '-r', '-t', 'all', 'tank'] == subproc.call_args[0][0]
        assert len(lst) == 4
        assert lst[0].pool == 'tank'
        assert lst[0].parent is None
        assert lst[1].name == 'system'
        assert lst[1].parent == 'tank'
        assert lst[1].type == DatasetType.FILESET
        assert lst[3].name == 'root'
        assert lst[3].full_path == 'tank/system/root'

    @patch('subprocess.run')
    def test_list_dataset_parent_fileset_str_happy(self, subproc):
        '''
        Specifies a parent as a string.
        '''
        test_stdout = '''tank/system	128G	13.3G	96K	none
tank/system/home	86.6G	13.3G	86.6G	/home
tank/system/root	14.9G	13.3G	14.9G	/'''
        subproc.return_value = subprocess.CompletedProcess(args=[], returncode=0, stdout=test_stdout, stderr='')

        zfs = ZFSCli(zfs_exe='/bin/true')
        lst = zfs.list_datasets(parent='tank/system')
        subproc.assert_called_once()
        assert ['/bin/true', 'list', '-H', '-r', '-t', 'all', 'tank/system'] == subproc.call_args[0][0]
        assert len(lst) == 3
        assert lst[0].name == 'system'
        assert lst[0].parent == 'tank'
        assert lst[0].type == DatasetType.FILESET
        assert lst[2].name == 'root'
        assert lst[2].full_path == 'tank/system/root'

    @patch('subprocess.run')
    def test_list_dataset_parent_fileset_dataset_happy(self, subproc):
        '''
        Specifies a parent as a dataset.
        '''
        test_stdout = '''tank/system	128G	13.3G	96K	none
tank/system/home	86.6G	13.3G	86.6G	/home
tank/system/root	14.9G	13.3G	14.9G	/'''
        subproc.return_value = subprocess.CompletedProcess(args=[], returncode=0, stdout=test_stdout, stderr='')

        zfs = ZFSCli(zfs_exe='/bin/true')
        lst = zfs.list_datasets(parent=Dataset(pool='tank', full_path='tank/system', name='system', parent='tank',
                                               type=DatasetType.FILESET))
        subproc.assert_called_once()
        assert ['/bin/true', 'list', '-H', '-r', '-t', 'all', 'tank/system'] == subproc.call_args[0][0]
        assert len(lst) == 3
        assert lst[0].name == 'system'
        assert lst[0].parent == 'tank'
        assert lst[0].type == DatasetType.FILESET
        assert lst[2].name == 'root'
        assert lst[2].full_path == 'tank/system/root'

    @patch('subprocess.run')
    def test_list_dataset_cmd_error_noparent(self, subproc):
        def mock_handle_command_error(myself, proc, dataset=None):
            assert type(proc) == subprocess.CompletedProcess
            assert proc.returncode == 42
            assert proc.stderr == 'test'
            assert dataset is None
            raise Exception('test')

        subproc.return_value = subprocess.CompletedProcess(args=[], returncode=42, stdout='', stderr='test')

        with patch.object(ZFSCli, 'handle_command_error', new=mock_handle_command_error):
            zfs = ZFSCli(zfs_exe='/bin/true')
            with pytest.raises(Exception) as excinfo:
                zfs.list_datasets()
            assert 'test' == str(excinfo.value)

    @patch('subprocess.run')
    def test_list_dataset_cmd_error_parent(self, subproc):
        def mock_handle_command_error(myself, proc, dataset):
            assert type(proc) == subprocess.CompletedProcess
            assert proc.returncode == 42
            assert proc.stderr == 'test'
            assert dataset == 'tank/test'
            raise Exception('test')

        subproc.return_value = subprocess.CompletedProcess(args=[], returncode=42, stdout='', stderr='test')

        with patch.object(ZFSCli, 'handle_command_error', new=mock_handle_command_error):
            zfs = ZFSCli(zfs_exe='/bin/true')
            with pytest.raises(Exception) as excinfo:
                zfs.list_datasets(parent='tank/test')
            assert 'test' == str(excinfo.value)

    ##########################################################################
    ##########################################################################
