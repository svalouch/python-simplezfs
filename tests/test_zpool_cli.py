
'''
Tests the ZPoolCli class, non destructive version.
'''

from unittest.mock import patch
import pytest

from simplezfs.zpool_cli import ZPoolCli


class TestZPoolCli:

    @patch('shutil.which')
    def test_init_noparam(self, which):
        which.return_value = '/bin/true'

        ZPoolCli()

    ##########################################################################

    @patch('shutil.which')
    def test_find_executable_parameter(self, which):
        which.return_value = None

        zpool = ZPoolCli(zpool_exe='asdf')
        assert zpool.executable == 'asdf'

    @patch('shutil.which')
    def test_find_executable_path(self, which):
        which.return_value = 'test_return'

        zpool = ZPoolCli()
        assert zpool.executable == 'test_return'

    @patch('shutil.which')
    def test_find_executable_path_fail(self, which):
        which.return_value = None

        with pytest.raises(OSError) as excinfo:
            ZPoolCli()
        assert 'not find executable' in str(excinfo.value)

    ##########################################################################

    @pytest.mark.parametrize('data,expected', [('-', None), (None, None), ('asdf', 'asdf')])
    def test_dash_to_none(self, data, expected):
        assert ZPoolCli.dash_to_none(data) == expected

    ##########################################################################
    ##########################################################################
    ##########################################################################
