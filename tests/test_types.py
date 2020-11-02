
from unittest.mock import patch
import pytest

from simplezfs.exceptions import ValidationError
from simplezfs.types import Dataset, DatasetType, PropertySource
from simplezfs.validation import validate_dataset_path


class TestTypesDataset:

    @patch('os.path.exists')
    @pytest.mark.parametrize('identifier,name,parent,dstype,pool', [
        ('pool/test', 'test', 'pool', DatasetType.FILESET, 'pool'),
        ('pool/test@st', 'test@st', 'pool', DatasetType.SNAPSHOT, 'pool'),
        ('pool/test1/test@snap-12', 'test@snap-12', 'pool/test1', DatasetType.SNAPSHOT, 'pool'),
        ('tank/test#bm1', 'test#bm1', 'tank', DatasetType.BOOKMARK, 'tank'),
        ('tank/test1/test#bmark-12', 'test#bmark-12', 'tank/test1', DatasetType.BOOKMARK, 'tank'),
        ('pool/test2', 'test2', 'pool', DatasetType.VOLUME, 'pool'),
        ('pool/test2/test', 'test', 'pool/test2', DatasetType.VOLUME, 'pool'),
    ])
    def test_from_string_valid(self, exists, identifier, name, parent, dstype, pool):
        '''
        Tests the happy path.
        '''
        validate_dataset_path(identifier)

        exists.return_value = dstype == DatasetType.VOLUME

        ds = Dataset.from_string(identifier)
        assert isinstance(ds, Dataset)
        assert ds.name == name
        assert ds.parent == parent
        assert ds.type == dstype
        assert ds.full_path == identifier
        assert ds.pool == pool

    @pytest.mark.parametrize('identifier', [' /asd', ' /asd', '\0/asd', 'mirrored/asd', 'raidz fun/asd'])
    def test_from_string_invalid(self, identifier):
        with pytest.raises(ValidationError):
            Dataset.from_string(identifier)


class TestTypesPropertySource:
    '''
    Tests for simplezfs.types.PropertySource.
    '''

    @pytest.mark.parametrize('value,sourcetype', [
        ('default', PropertySource.DEFAULT),
        ('DEFault', PropertySource.DEFAULT),
        ('local', PropertySource.LOCAL),
        ('LOCAL', PropertySource.LOCAL),
        ('inherited', PropertySource.INHERITED),
        ('INHERITED', PropertySource.INHERITED),
        ('inherited from somesource', PropertySource.INHERITED),
        ('INHERITED FROM somesource', PropertySource.INHERITED),
        ('temporary', PropertySource.TEMPORARY),
        ('TEMPORARY', PropertySource.TEMPORARY),
        (b'TEMPORARY', PropertySource.TEMPORARY),
        ('received', PropertySource.RECEIVED),
        ('RECEIVED', PropertySource.RECEIVED),
        ('none', PropertySource.NONE),
        ('NONE', PropertySource.NONE),
        ('-', PropertySource.NONE),
    ])
    def test_from_string_valid(self, value: str, sourcetype: PropertySource) -> None:
        '''
        Happy path, test that it accepts known-good values.
        '''
        assert PropertySource.from_string(value) == sourcetype

    @pytest.mark.parametrize('value', [' default', 'DEFAULT ', 'asdf', '', 'DEFAULT FROM asdf', 'inherited somesrc',
                                       123])
    def test_from_string_invalid(self, value: str) -> None:
        '''
        Test that it successfully reports an error when receiving invalid input.
        '''
        with pytest.raises(ValueError):
            PropertySource.from_string(value)
