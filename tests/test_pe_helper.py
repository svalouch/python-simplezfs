

import pytest
from simplezfs.pe_helper import ExternalPEHelper, PEHelperBase, SudoPEHelper


class TestPEHelperBase:

    def test_repr(self):
        pehb = PEHelperBase()
        assert 'PEHelperBase' in str(pehb)

    def test_not_implemented(self):
        pehb = PEHelperBase()

        with pytest.raises(NotImplementedError):
            pehb.zfs_mount('test')
        with pytest.raises(NotImplementedError):
            pehb.zfs_set_mountpoint('test', '/test')


class TestExternalPEHelper:

    def test_repr(self):
        eph = ExternalPEHelper('/bin/true')
        assert 'ExternalPEHelper' in str(eph)
        assert '/bin/true' in str(eph)

    # ########################################################################
    def test_get_executable(self):
        eph = ExternalPEHelper('/bin/true')
        assert eph.executable == '/bin/true'

    def test_set_executable(self):
        eph = ExternalPEHelper('/bin/false')
        assert eph.executable == '/bin/false'

        eph.executable = '/bin/true'
        assert eph.executable == '/bin/true'

    def test_set_executable_not_found_ctor(self):
        with pytest.raises(FileNotFoundError) as e:
            ExternalPEHelper('/file/does/not/exist')
        assert 'No such file or directory' in str(e.value)

    def test_set_executable_not_found_property(self):
        eph = ExternalPEHelper('/bin/true')
        with pytest.raises(FileNotFoundError) as e:
            eph.executable = '/file/does/not/exist'
        assert 'No such file or directory' in str(e.value)

    def test_set_executable_directory_ctor(self):
        with pytest.raises(FileNotFoundError) as e:
            ExternalPEHelper('/')
        assert 'must be a file' in str(e.value)

    def test_set_executable_directory_property(self):
        eph = ExternalPEHelper('/bin/true')
        with pytest.raises(FileNotFoundError) as e:
            eph.executable = '/'
        assert 'must be a file' in str(e.value)

    def test_set_executable_nonexecutable_ctor(self):
        with pytest.raises(FileNotFoundError) as e:
            ExternalPEHelper('/etc/hosts')
        assert 'must be executable' in str(e.value)

    def test_set_executable_nonexecutable_property(self):
        eph = ExternalPEHelper('/bin/true')
        with pytest.raises(FileNotFoundError) as e:
            eph.executable = '/etc/hosts'
        assert 'must be executable' in str(e.value)


class TestSudoPEHelper:

    def test_repr(self):
        sph = SudoPEHelper()
        assert 'SudoPEHelper' in str(sph)
        assert 'sudo' in str(sph)
