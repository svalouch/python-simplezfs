
'''
Tests the main ZFS class, non-destructive version.
'''

from unittest.mock import patch
import pytest  # type: ignore

from simplezfs.exceptions import ValidationError
from simplezfs.types import Dataset, DatasetType
from simplezfs.zfs import ZFS, get_zfs
from simplezfs.zfs_cli import ZFSCli
from simplezfs.zfs_native import ZFSNative


class TestZFS:

    def test_init_noparam(self):
        assert ZFS()

    def test_get_metadata_namespace(self):
        zfs = ZFS(metadata_namespace='pytest')
        assert zfs.metadata_namespace == 'pytest'

    def test_set_metadata_namespace(self):
        zfs = ZFS(metadata_namespace='prod')
        zfs.metadata_namespace = 'pytest'
        assert zfs.metadata_namespace == 'pytest'

    ##########################################################################

    def test_get_property_notimplemented(self):
        zfs = ZFS()
        with pytest.raises(NotImplementedError):
            zfs.get_property('tank/test1', 'compression')

    def test_get_property_all(self):
        '''
        Uses "all" and expects a ValidationError.
        '''
        zfs = ZFS()
        with pytest.raises(ValidationError) as excinfo:
            zfs.get_property('tank/test', 'all')
        assert 'get_properties' in str(excinfo.value)

    def test_get_property_all_meta(self):
        '''
        Tests that <namespace>:all is allowed.
        '''
        def mock_get_property(myself, dataset, key, is_metadata):
            assert dataset == 'tank/test'
            assert key == 'testns:all'
            assert is_metadata is True

        with patch.object(ZFS, '_get_property', new=mock_get_property):
            zfs = ZFS(metadata_namespace='testns')
            zfs.get_property('tank/test', 'all', metadata=True)

    def test_property_dataset_validation_unhappy(self):
        def mock_get_property(myself, dataset, key, is_metadata):
            assert False, 'this should not have been called'

        with patch.object(ZFS, '_get_property', new=mock_get_property):
            zfs = ZFS()
            with pytest.raises(ValidationError):
                zfs.get_property('tan#k/test', 'compression')

    def test_get_property_meta_nooverwrite_invalidns_unhappy(self):
        '''
        Tests the validation of the metadata namespace, coming from the ctor.
        '''
        def mock_get_property(myself, dataset, key, is_metadata):
            assert False, 'This should not have been called'

        with patch.object(ZFS, '_get_property', new=mock_get_property):
            zfs = ZFS(metadata_namespace=' ')
            with pytest.raises(ValidationError) as excinfo:
                zfs.get_property('tank/test', 'test', metadata=True)
            assert 'not match' in str(excinfo.value)

    def test_get_property_meta_overwrite_invalidns_unhappy(self):
        '''
        Tests the validation of the metadata namespace, coming from overwrite parameter.
        '''
        def mock_get_property(myself, dataset, key, is_metadata):
            assert False, 'This should not have been called'

        with patch.object(ZFS, '_get_property', new=mock_get_property):
            zfs = ZFS(metadata_namespace='pytest')
            with pytest.raises(ValidationError) as excinfo:
                zfs.get_property('tank/test', 'test', metadata=True, overwrite_metadata_namespace=' ')
            assert 'not match' in str(excinfo.value)

    def test_get_property_poolname_nometa_happy(self):
        '''
        Tests that the name of the pool (first or root dataset) can be queried.
        '''
        def mock_get_property(myself, dataset, key, is_metadata):
            assert dataset == 'tank'
            assert key == 'compression'
            assert is_metadata is False

        with patch.object(ZFS, '_get_property', new=mock_get_property):
            zfs = ZFS()
            zfs.get_property('tank', 'compression')

    def test_get_property_poolname_invalid_nometa_unhappy(self):
        '''
        Tests the pool name validation.
        '''
        def mock_get_property(myself, dataset, key, is_meta):
            assert False, 'This should not have been called'

        with patch.object(ZFS, '_get_property', new=mock_get_property):
            zfs = ZFS()
            with pytest.raises(ValidationError) as excinfo:
                zfs.get_property(' ', 'compression')
            assert 'malformed' in str(excinfo.value)

    def test_get_property_nometa_happy(self):
        def mock_get_property(myself, dataset: str, key: str, is_metadata: bool):
            assert dataset == 'tank/test'
            assert key == 'compression'
            assert is_metadata is False

        with patch.object(ZFS, '_get_property', new=mock_get_property):
            zfs = ZFS()
            zfs.get_property('tank/test', 'compression')

    def test_get_property_meta_ns_happy(self):
        def mock_get_property(myself, dataset, key, is_metadata):
            assert dataset == 'tank/test'
            assert key == 'testns:testprop'
            assert is_metadata is True

        with patch.object(ZFS, '_get_property', new=mock_get_property):
            zfs = ZFS(metadata_namespace='testns')
            zfs.get_property('tank/test', 'testprop', metadata=True)

    def test_get_property_meta_nsoverwrite_happy(self):
        def mock_get_property(myself, dataset, key, is_metadata):
            assert dataset == 'tank/test'
            assert key == 'testns:testprop'
            assert is_metadata is True

        with patch.object(ZFS, '_get_property', new=mock_get_property):
            zfs = ZFS(metadata_namespace='pytest')
            zfs.get_property('tank/test', 'testprop', metadata=True, overwrite_metadata_namespace='testns')

    def test_get_property_nometa_nons_unhappy(self):
        '''
        Tests that it bails out if no metadata namespace has been set and none is given.
        '''
        def mock_get_property(myself, dataset, key, is_metadata):
            assert False, 'This should not have been called'

        with patch.object(ZFS, '_get_property', new=mock_get_property):
            zfs = ZFS()
            assert zfs.metadata_namespace is None
            with pytest.raises(ValidationError) as excinfo:
                zfs.get_property('tank/test', 'testprop', metadata=True)
            assert 'no metadata namespace set' == str(excinfo.value)

    def test_get_property_meta_ns_noflag_invalid(self):
        '''
        Tests that it bails out if the syntax indicates a metadata property is requested but metadata flag is false.
        '''
        def mock_get_property(myself, dataset, key, is_metadata):
            assert False, 'This should not have been called'

        with patch.object(ZFS, '_get_property', new=mock_get_property):
            zfs = ZFS(metadata_namespace='testns')
            with pytest.raises(ValidationError):
                zfs.get_property('tank/test', 'testns:testprop', metadata=False)

    ##########################################################################

    def test_get_properties_notimplemented(self):
        zfs = ZFS()
        with pytest.raises(NotImplementedError):
            zfs.get_properties('tank/test')

    def test_get_properties_poolname_nometa_happy(self):
        def mock_get_properties(myself, dataset, include_metadata):
            assert dataset == 'tank'
            assert include_metadata is False

        with patch.object(ZFS, '_get_properties', new=mock_get_properties):
            zfs = ZFS()
            zfs.get_properties('tank')

    def test_get_properties_dataset_unhappy(self):
        '''
        Tests that it validates the dataset name
        '''
        def mock_get_properties(myself, dataset, include_metadata):
            assert False, 'this should not have been called'

        with patch.object(ZFS, '_get_properties', new=mock_get_properties):
            zfs = ZFS()
            with pytest.raises(ValidationError):
                zfs.get_properties('as#df/tank')

    ##########################################################################

    def test_set_property_notimplemented(self):
        zfs = ZFS()
        with pytest.raises(NotImplementedError):
            zfs.set_property('tank/test1', 'compression', 'lz4')

    def test_set_property_all_nometa_unhappy(self):
        zfs = ZFS()
        with pytest.raises(ValidationError) as excinfo:
            zfs.set_property('tank/test', 'all', 'test')
        assert 'valid property name' in str(excinfo.value)

    def test_set_property_all_meta_happy(self):
        def mock_set_property(myself, dataset, key, value, is_metadata):
            assert 'tank/test' == dataset
            assert 'testns:all' == key
            assert 'test' == value
            assert is_metadata

        with patch.object(ZFS, '_set_property', new=mock_set_property):
            zfs = ZFS(metadata_namespace='testns')
            zfs.set_property('tank/test', 'all', 'test', metadata=True)

    def test_set_property_dataset_validation_unhappy(self):
        def mock_set_property(myself, dataset, key, value, is_metadata):
            assert False, 'This should not have been called'

        with patch.object(ZFS, '_set_property', new=mock_set_property):
            zfs = ZFS()
            with pytest.raises(ValidationError):
                zfs.set_property('ta#nk/test', 'compression', 'lz4')

    def test_set_property_meta_nooverwrite_invalidns_unhappy(self):
        '''
        Tests the validation of the metadata namespace, coming from the ctor.
        '''
        def mock_set_property(myself, dataset, key, value, is_metadata):
            assert False, 'This should not have been called'

        with patch.object(ZFS, '_set_property', new=mock_set_property):
            zfs = ZFS(metadata_namespace=' ')
            with pytest.raises(ValidationError) as excinfo:
                zfs.set_property('tank/test', 'test', 'test', metadata=True)
            assert 'not match' in str(excinfo.value)

    def test_set_property_meta_overwrite_invalidns_unhappy(self):
        def mock_set_property(myself, dataset, key, value, is_metadata):
            assert False, 'This should not have been called'

        with patch.object(ZFS, '_set_property', new=mock_set_property):
            zfs = ZFS(metadata_namespace='pytest')
            with pytest.raises(ValidationError) as excinfo:
                zfs.set_property('tank/test', 'test', 'test', metadata=True, overwrite_metadata_namespace=' ')
            assert 'not match' in str(excinfo.value)

    def test_set_property_poolname_nometa_happy(self):
        def mock_set_property(myself, dataset, key, value, is_metadata):
            assert dataset == 'tank'
            assert key == 'compression'
            assert value == 'lz4'
            assert not is_metadata

        with patch.object(ZFS, '_set_property', new=mock_set_property):
            zfs = ZFS()
            zfs.set_property('tank', 'compression', 'lz4')

    def test_set_property_poolname_invalid_nometa_unhappy(self):
        def mock_set_property(myself, dataset, key, value, is_metadata):
            assert False, 'This should not have been called'

        with patch.object(ZFS, '_set_property', new=mock_set_property):
            zfs = ZFS()
            with pytest.raises(ValidationError) as excinfo:
                zfs.set_property(' ', 'compression', 'lz4')
            assert 'malformed' in str(excinfo.value)

    def test_set_property_nometa_happy(self):
        def mock_set_property(myself, dataset, key, value, is_metadata):
            assert dataset == 'tank/test'
            assert key == 'compression'
            assert value == 'lz4'
            assert not is_metadata

        with patch.object(ZFS, '_set_property', new=mock_set_property):
            zfs = ZFS()
            zfs.set_property('tank/test', 'compression', 'lz4')

    def test_set_property_meta_ns_happy(self):
        def mock_set_property(myself, dataset, key, value, is_metadata):
            assert dataset == 'tank/test'
            assert key == 'testns:testprop'
            assert value == 'testval'
            assert is_metadata

        with patch.object(ZFS, '_set_property', new=mock_set_property):
            zfs = ZFS(metadata_namespace='testns')
            zfs.set_property('tank/test', 'testprop', 'testval', metadata=True)

    def test_set_property_meta_nsoverwrite_happy(self):
        def mock_set_property(myself, dataset, key, value, is_metadata):
            assert dataset == 'tank/test'
            assert key == 'testns:testprop'
            assert value == 'testval'
            assert is_metadata

        with patch.object(ZFS, '_set_property', new=mock_set_property):
            zfs = ZFS(metadata_namespace='pytest')
            zfs.set_property('tank/test', 'testprop', 'testval', metadata=True, overwrite_metadata_namespace='testns')

    def test_set_property_nometa_nons_unhappy(self):
        def mock_set_property(myself, dataset, key, value, is_metadata):
            assert False, 'This should not have been called'

        with patch.object(ZFS, '_set_property', new=mock_set_property):
            zfs = ZFS()
            assert zfs.metadata_namespace is None
            with pytest.raises(ValidationError) as excinfo:
                zfs.set_property('tank/test', 'testprop', 'testval', metadata=True)
            assert 'no metadata namespace set' in str(excinfo.value)

    def test_set_property_meta_ns_noflag_inalid(self):
        def mock_set_property(myself, dataset, key, value, is_metadata):
            assert False, 'This should not have been called'

        with patch.object(ZFS, '_set_property', new=mock_set_property):
            zfs = ZFS(metadata_namespace='testns')
            with pytest.raises(ValidationError):
                zfs.set_property('tank/test', 'testns:testprop', 'testval', metadata=False)

    ##########################################################################

    def test_create_snapshot_call(self):
        '''
        Tests the call parameters with which create_snapshot calls create_dataset
        '''
        def mock_create_dataset(myself, name, dataset_type=DatasetType.FILESET, properties=None,
                                metadata_properties=None, mount_helper=None, sparse=False, size=None, recursive=False):
            assert name == 'test/test@testsnap'
            assert dataset_type == DatasetType.SNAPSHOT
            assert properties == {'test': 'test'}
            assert metadata_properties is None
            assert mount_helper is None
            assert sparse is False
            assert size is None
            assert recursive is False
            return Dataset(name='test@testsnap', full_path='test/test@testsnap', pool='test',
                           parent='test', type=dataset_type)

        with patch.object(ZFS, 'create_dataset', new=mock_create_dataset):
            zfs = ZFS()
            ds = zfs.create_snapshot('test/test', 'testsnap', properties=dict(test='test'))
            assert ds.name == 'test@testsnap'

    def test_create_bookmark_call(self):
        '''
        Tests the call parameters with which create_bookmark calls create_dataset
        '''
        def mock_create_dataset(myself, name, dataset_type=DatasetType.FILESET, properties=None,
                                metadata_properties=None, mount_helper=None, sparse=False, size=None, recursive=False):
            assert name == 'test/test#testmark'
            assert dataset_type == DatasetType.BOOKMARK
            assert properties == {'test': 'test'}
            assert metadata_properties is None
            assert mount_helper is None
            assert sparse is False
            assert size is None
            assert recursive is False
            return Dataset(name='test#testmark', full_path='test/test#testmark', pool='test',
                           parent='test', type=dataset_type)

        with patch.object(ZFS, 'create_dataset', new=mock_create_dataset):
            zfs = ZFS()
            ds = zfs.create_bookmark('test/test', 'testmark', properties=dict(test='test'))
            assert ds.name == 'test#testmark'

    def test_create_fileset_call(self):
        '''
        Tests the call parameters with which create_fileset calls create_dataset
        '''
        def mock_create_dataset(myself, name, dataset_type=DatasetType.FILESET, properties=None,
                                metadata_properties=None, mount_helper=None, sparse=False, size=None, recursive=False):
            assert name == 'test/testfs'
            assert dataset_type == DatasetType.FILESET
            assert properties == {'test': 'test', 'mountpoint': '/test/testfs'}
            assert metadata_properties is None
            assert mount_helper == 'mounthelper'
            assert sparse is False
            assert size is None
            assert recursive is False
            return Dataset(name='testfs', full_path='test/testfs', pool='test', parent='test', type=dataset_type)

        with patch.object(ZFS, 'create_dataset', new=mock_create_dataset):
            zfs = ZFS()
            ds = zfs.create_fileset('test/testfs', mountpoint='/test/testfs', properties=dict(test='test'),
                                    mount_helper='mounthelper', recursive=False)
            assert ds.name == 'testfs'

    def test_create_volume_call(self):
        '''
        Tests the call parameters with which create_volume calls create_dataset
        '''
        def mock_create_dataset(myself, name, dataset_type=DatasetType.FILESET, properties=None,
                                metadata_properties=None, mount_helper=None, sparse=False, size=None, recursive=False):
            assert name == 'test/testvol'
            assert dataset_type == DatasetType.VOLUME
            assert properties == {'test': 'test', 'blocksize': str(64 * 1024)}
            assert metadata_properties is None
            assert mount_helper is None
            assert sparse is True
            assert size == 1024 * 1024 * 1024
            assert recursive is False
            return Dataset(name='testvol', full_path='test/testvol', pool='test', parent='test', type=dataset_type)

        with patch.object(ZFS, 'create_dataset', new=mock_create_dataset):
            zfs = ZFS()
            ds = zfs.create_volume('test/testvol', size=1024 * 1024 * 1024, sparse=True, blocksize=64 * 1024,
                                   properties=dict(test='test'), recursive=False)
            assert ds.name == 'testvol'

    def test_notimplemented(self):
        zfs = ZFS()
        with pytest.raises(NotImplementedError):
            zfs.list_datasets()
        with pytest.raises(NotImplementedError):
            zfs.create_dataset('tank/test5')
        with pytest.raises(NotImplementedError):
            zfs.destroy_dataset('tank/test6')

    ##########################################################################


class TestZFSGetZFS:

    @patch('shutil.which')
    def test_get_zfs_default(self, which):
        which.return_value = '/bin/true'
        zfs = get_zfs()
        assert type(zfs) == ZFSCli
        assert zfs.metadata_namespace is None
        assert zfs.executable == '/bin/true'
        which.assert_called_once_with('zfs')

    @patch('shutil.which')
    def test_get_zfs_cli(self, which):
        which.return_value = '/bin/true'
        zfs = get_zfs('cli')
        assert type(zfs) == ZFSCli
        assert zfs.executable == '/bin/true'
        which.assert_called_once_with('zfs')

    def test_get_zfs_cli_args(self):
        zfs = get_zfs('cli', metadata_namespace='asdf', zfs_exe='/bin/true')
        assert type(zfs) == ZFSCli
        assert zfs.metadata_namespace == 'asdf'
        assert zfs.executable == '/bin/true'

    def test_get_zfs_native(self):
        zfs = get_zfs('native')
        assert type(zfs) == ZFSNative

    def test_get_zfs_invalid(self):
        with pytest.raises(NotImplementedError):
            get_zfs('testing')
