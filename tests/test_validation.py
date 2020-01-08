
'''
Tests the validation functions.
'''

import pytest
from simplezfs.exceptions import ValidationError
from simplezfs.validation import (
    validate_dataset_name,
    validate_dataset_path,
    validate_metadata_property_name,
    validate_native_property_name,
    validate_pool_name,
    validate_property_value,
)


class TestPoolName:
    '''
    Tests the function ``validate_pool_name``.
    '''
    @pytest.mark.parametrize('name', ['a', 'aa', 'aaa', 'a' * 20, 'a123', 'a ', 'a 1 2 _ : .. ::', 'a:a'])
    def test_valid_name(self, name):
        '''
        Tests a set of known good combinations.
        '''
        validate_pool_name(name)

    @pytest.mark.parametrize('name', [' ', ' a', 'ä', 'aä', 'aaaaaa→', '\0', '\n', '\t'])
    def test_invalid_name(self, name):
        '''
        Tests a set of known bad combinations.
        '''
        with pytest.raises(ValidationError) as excinfo:
            validate_pool_name(name)
        assert 'malformed name' in str(excinfo.value)

    @pytest.mark.parametrize('name', ['mirror', 'raidz', 'spare', 'log'])
    def test_invalid_reserved_keyword(self, name):
        '''
        Tests with reserved keywords.
        '''
        with pytest.raises(ValidationError) as excinfo:
            validate_pool_name(name)
        assert 'reserved name' in str(excinfo.value)

    @pytest.mark.parametrize('name', ['mirrored', 'mirror:ed', 'spared', 'spare:d', 'raidzfun', 'raidz fun'])
    def test_invalid_begins_with_reserved_keyword(self, name):
        '''
        Tests with strings that are known to be reserved starts of the name.
        '''
        with pytest.raises(ValidationError) as excinfo:
            validate_pool_name(name)
        assert 'starts with invalid token' in str(excinfo.value)

    def test_valid_keyword_begin_extra(self):
        '''
        Of the reserved keywords, 'log' is allowed as beginning of the pool name, check that it is allowed.
        '''
        validate_pool_name('logger')

    @pytest.mark.parametrize('name', ['c0', 'c1', 'c0 ', 'c0d0', 'c0t0', 'c999', 'c9 9asd .-:'])
    def test_invalid_solaris_disk_names_begin(self, name):
        '''
        Test with solaris disk names and similar names.
        '''
        with pytest.raises(ValidationError) as excinfo:
            validate_pool_name(name)
        assert 'begins with reserved sequence' in str(excinfo.value)

    def test_too_short(self):
        '''
        Tests with a name that we know is too short.
        '''
        with pytest.raises(ValidationError) as excinfo:
            validate_pool_name('')
        assert 'too short' in str(excinfo.value)

    # TODO test too long


class TestDatasetName:
    '''
    Tests the function ``validate_dataset_name``.
    '''

    @pytest.mark.parametrize('name', [
        'a', 'aa', '0', '0a', 'A', 'A0', 'qwertzuiop', 'a-', '-a', 'a.a', '.', 'a:', ':a', 'a:a', 'a::a',
        '842bf5a29bd55c12c20a8d1e73bdb5790e8ab804d857885e35e55be025acb6b2',
        '842bf5a29bd55c12c20a8d1e73bdb5790e8ab804d857885e35e55be025acb6b2-init', 'towel@20190525', 'page#42'])
    def test_valid_name(self, name):
        '''
        Tests a set of known good combinations.
        '''
        validate_dataset_name(name)

    @pytest.mark.parametrize('name', ['/a', '/', 'a/a', 'a/', 'a+', 'ä', '→', '\0', '\n', 'towel@@20190525',
                                      'towel@#42', 'page##42', 'page#@20190525'])
    def test_invalid_name(self, name):
        '''
        Tests a set of known invalid combinations.
        '''
        with pytest.raises(ValidationError) as excinfo:
            validate_dataset_name(name)
        assert 'disallowed characters' in str(excinfo.value)

    @pytest.mark.parametrize('name', ['a@a', 'aasdf@1234', 'a#a', 'a#123'])
    def test_invalid_name_strict(self, name):
        '''
        Tests with strict=True, which disallows snapshot or bookmark identifiers.
        '''
        with pytest.raises(ValidationError) as excinfo:
            validate_dataset_name(name, strict=True)
        assert 'not allowed in strict' in str(excinfo.value)

    # TODO trigger UnicodeEncodeError!

    def test_invalid_name_length_short(self):
        '''
        Tests the behaviour if the name is too short
        '''
        with pytest.raises(ValidationError) as excinfo:
            validate_dataset_name('')
        assert 'too short' in str(excinfo.value)

    def test_invalid_length_long(self):
        '''
        Providing a very long name, it should bail out.
        '''
        with pytest.raises(ValidationError) as excinfo:
            validate_dataset_name('a' * 1024)
        assert 'length >' in str(excinfo.value)


class TestDatasetPath:
    '''
    Tests the function ``validate_dataset_path``.
    '''

    @pytest.mark.parametrize('path', ['a/a', 'a/a/a', 'a/b/c', 'asdf/qwer/yxcv', 'a/a@a', 'a/a#a'])
    def test_valid_path(self, path):
        '''
        Tests a set of known good combinations.
        '''
        validate_dataset_path(path)

    @pytest.mark.parametrize('path', ['a', '/a', 'a/', '/a/', '/aaaaa/', 'a/a a', 'a@a/a', 'a/a#a/a', 'a/a@a/a#a'])
    def test_invalid_path(self, path):
        '''
        Tests a set of known bad combinations.
        '''
        with pytest.raises(ValidationError):
            validate_dataset_path(path)

    @pytest.mark.parametrize('path', ['asdf', 'asdf@yesterday', 'asdf#tomorrow'])
    def test_invalid_path_no_slash(self, path):
        '''
        Tests the behaviour if no slash is found, making it a dataset name.
        '''
        with pytest.raises(ValidationError) as excinfo:
            validate_dataset_path(path)
        assert 'Not a path' in str(excinfo.value)

    # TODO tests for specific errors passed from the validation functions for pool and dataset name


class TestNativePropertyName:
    '''
    Tests the function ``validate_native_property_name``.
    '''

    @pytest.mark.parametrize('name', ['a', 'aa', 'a0', 'a0a', 'asdfghjkl'])
    def test_valid_name(self, name):
        '''
        Tests a set of known good combinations.
        '''
        validate_native_property_name(name)

    @pytest.mark.parametrize('name', ['0', '0a', 'A', 'AA', '-', 'a-', 'a-a', '-a', '_', 'a_', 'a_a', '_a', ':', 'a:',
                                      'a:a', ':a', '\0'])
    def test_invalid_name(self, name):
        '''
        Tests a set of known invalid combinations.
        '''
        with pytest.raises(ValidationError) as excinfo:
            validate_native_property_name(name)
        assert 'does not match' in str(excinfo.value)

    # TODO trigger UnicodeEncodeError!

    def test_invalid_length_short(self):
        '''
        Tests the behaviour if the name is too short.
        '''
        with pytest.raises(ValidationError) as excinfo:
            validate_native_property_name('')
        assert 'too short' in str(excinfo.value)

    def test_invalid_length_long(self):
        '''
        Provided a very long name, it should bail out.
        '''
        with pytest.raises(ValidationError) as excinfo:
            validate_native_property_name('a' * 1024)
        assert 'length >' in str(excinfo.value)


class TestMetadataPropertyName:
    '''
    Tests the function ``validate_metadata_property_name``.
    '''
    @pytest.mark.parametrize('name', [':a', 'a:a', 'a:0', 'a:0:a', ':a:s:d:f:g:h:j:k::l', ':-', 'a-:-a'])
    def test_valid_name(self, name):
        '''
        Tests a set of known good combinations.
        '''
        validate_metadata_property_name(name)

    @pytest.mark.parametrize('name', ['0', '0a', 'A', 'AA', '-', 'a-', 'a-a', '-a', '_', 'a_', 'a_a', '_a', ':', 'a:',
                                      '\0', 'a+:a'])
    def test_invalid_name(self, name):
        '''
        Tests a set of known invalid combinations.
        '''
        with pytest.raises(ValidationError) as excinfo:
            validate_metadata_property_name(name)
        assert 'does not match' in str(excinfo.value)

    # TODO trigger UnicodeEncodeError!

    def test_invalid_length_short(self):
        '''
        Tests the behaviour if the name is too short.
        '''
        with pytest.raises(ValidationError) as excinfo:
            validate_metadata_property_name('')
        assert 'too short' in str(excinfo.value)

    def test_invalid_length_long(self):
        '''
        Provided a very long name, it should bail out.
        '''
        with pytest.raises(ValidationError) as excinfo:
            validate_metadata_property_name('a' * 1024)
        assert 'length >' in str(excinfo.value)


class TestPropertyValue:
    '''
    Tests the function ``validate_property_value``.
    '''
    @pytest.mark.parametrize('value', ['a', '1', '1TB', '1ZB', '99 red baloons', 'asd 123'])
    def test_value_valid(self, value):
        '''
        Tests a set of known good combinations.
        '''
        validate_property_value(value)

    def test_value_valid_long(self):
        '''
        Tests with a value that is long, but still valid.
        '''
        validate_property_value('x' * 8191)

    def test_value_too_long(self):
        '''
        Tests with a value that is too long
        '''
        with pytest.raises(ValidationError) as excinfo:
            validate_property_value('x' * 8192)
        assert 'length >' in str(excinfo.value)
