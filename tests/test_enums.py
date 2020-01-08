
import pytest

from simplezfs.types import DatasetType, PropertySource


class TestDatasetType:

    @pytest.mark.parametrize('string,value', [('FiLeSet', DatasetType.FILESET), ('fileset', DatasetType.FILESET),
                                              ('vOlUMe', DatasetType.VOLUME), ('volume', DatasetType.VOLUME),
                                              ('SnapSHOT', DatasetType.SNAPSHOT), ('snapshot', DatasetType.SNAPSHOT),
                                              ('BOOKmark', DatasetType.BOOKMARK), ('bookmark', DatasetType.BOOKMARK)])
    def test_from_string_valid(self, string, value):
        '''
        Tests that the from_string helper works.
        '''
        v = DatasetType.from_string(string)
        assert isinstance(v, DatasetType)
        assert v.value == string.lower()

    @pytest.mark.parametrize('string', [' fileset', 'dateiset', 'file set', 'data\0set', '', ' '])
    def test_from_string_invalid(self, string):
        '''
        Tests if it raises an exception if the value is invalid.
        '''
        with pytest.raises(ValueError) as excinfo:
            DatasetType.from_string(string)
        assert 'not a valid DatasetType' in str(excinfo.value)

    def test_from_string_None(self):
        '''
        Tests that it properly fails with None as input.
        '''
        with pytest.raises(ValueError) as excinfo:
            DatasetType.from_string(None)
        assert 'only string' in str(excinfo.value)


class TestPropertySource:

    @pytest.mark.parametrize('string,value', [
        ('default', PropertySource.DEFAULT), ('DeFAULT', PropertySource.DEFAULT),
        ('inheriteD', PropertySource.INHERITED), ('inherited', PropertySource.INHERITED),
        ('TEMPORARY', PropertySource.TEMPORARY), ('temporary', PropertySource.TEMPORARY),
        ('rEcEiVeD', PropertySource.RECEIVED), ('received', PropertySource.RECEIVED),
        ('None', PropertySource.NONE), ('none', PropertySource.NONE)])
    def test_from_string_valid(self, string, value):
        '''
        Test that the from_string helper works.
        '''
        v = PropertySource.from_string(string)
        assert isinstance(v, PropertySource)
        assert v.value == string.lower()

    @pytest.mark.parametrize('string', ['asd', '', ' ', 'default\0', 'defaultdefault', 'Normal'])
    def test_from_string_invalid(self, string):
        '''
        Tests that it raises an exception if the value is invalid.
        '''
        with pytest.raises(ValueError) as excinfo:
            PropertySource.from_string(string)
        assert 'not a valid PropertySource' in str(excinfo.value)

    def test_from_string_None(self):
        '''
        Tests that it properly fails with None as input.
        '''
        with pytest.raises(ValueError) as excinfo:
            PropertySource.from_string(None)
        assert 'only string' in str(excinfo.value)
