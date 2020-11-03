################
Python-SimpleZFS
################

A thin wrapper around ZFS from the OpenZFS_ project.

The library aims at providing a simple, low-level interface for working with ZFS, either by wrapping the ``zfs(8)`` and
``zpool(8)`` CLI utilities or by accessing the native python API.

It does not provide a high-level interface, however, and does not aim to. It also tries to keep as little state as
possible.

Two interface classes make up the API, ``ZFS`` and ``ZPool``, which are wrappers around the functionality of the CLI
tools of the same name. They come with two implementations:

* The CLI implementation wraps the executables
* The Native implementation uses the native API released with OpenZFS 0.8.

In this early stage, the native implementation has not been written.

Status
******
The table gives a rough overview over features and their implementation state. For the PE Helper, functions where it is
of no use are left empty (use ``zfs allow`` for those). Recursive is used to denote if it can destroy the dataset with
dependent datasets, for example a fileset with its associated snapshots.

+-------+------------+------------------+-----+--------+-----------+-------------+
| API   | Topic      | Feature          | CLI | Native | PE Helper | Recursive   |
+=======+============+==================+=====+========+===========+=============+
| ZFS   | Properties | Read native      | Yes | No     |           |             |
|       |            +------------------+-----+--------+-----------+-------------+
|       |            | Write native     | Yes | No     |           |             |
|       |            +------------------+-----+--------+-----------+-------------+
|       |            | Read metadata    | Yes | No     |           |             |
|       |            +------------------+-----+--------+-----------+-------------+
|       |            | Write metadata   | Yes | No     |           |             |
|       +------------+------------------+-----+--------+-----------+-------------+
|       | Datasets   | List datasets    | Yes | No     |           |             |
|       |            +------------------+-----+--------+-----------+-------------+
|       |            | Check existance  | Yes | No     |           |             |
|       |            +------------------+-----+--------+-----------+-------------+
|       |            | Create Fileset   | Yes | No     | Yes       |             |
|       |            +------------------+-----+--------+-----------+-------------+
|       |            | Create Volume    | No  | No     |           |             |
|       |            +------------------+-----+--------+-----------+-------------+
|       |            | Create Snapshot  | No  | No     | No        |             |
|       |            +------------------+-----+--------+-----------+-------------+
|       |            | Create Bookmark  | No  | No     |           |             |
|       |            +------------------+-----+--------+-----------+-------------+
|       |            | Destroy Fileset  | Yes | No     | Yes       | Yes (Snaps) |
|       |            +------------------+-----+--------+-----------+-------------+
|       |            | Destroy Volume   | No  | No     | No        |             |
|       |            +------------------+-----+--------+-----------+-------------+
|       |            | Destroy Snapshot | No  | No     | No        |             |
|       |            +------------------+-----+--------+-----------+-------------+
|       |            | Destroy Bookmark | No  | No     | No        |             |
+-------+------------+------------------+-----+--------+-----------+-------------+
| ZPool | Storage    | List pools       | No  | No     |           |             |
|       |            +------------------+-----+--------+-----------+-------------+
|       |            | Read structure   | Yes | No     |           |             |
|       |            +------------------+-----+--------+-----------+-------------+
|       |            | Replace disk     | No  | No     | No        |             |
|       |            +------------------+-----+--------+-----------+-------------+
|       |            | Destroy          | No  | No     | No        |             |
|       |            +------------------+-----+--------+-----------+-------------+
|       |            | Create           | No  | No     | No        |             |
|       +------------+------------------+-----+--------+-----------+-------------+
|       | Properties | Read native      | No  | No     |           |             |
|       |            +------------------+-----+--------+-----------+-------------+
|       |            | Write native     | No  | No     | No        |             |
|       |            +------------------+-----+--------+-----------+-------------+
|       |            | Read metadata    | No  | No     |           |             |
|       |            +------------------+-----+--------+-----------+-------------+
|       |            | Write metadata   | No  | No     |           |             |
+-------+------------+------------------+-----+--------+-----------+-------------+

Usage
*****

One can either get a concrete implementation by calling ``ZFSCli``/``ZFSNative`` or ``ZPoolCli``/``ZPoolNative``, or
more conveniently use the functions ``get_zfs(implementation_name)`` or ``get_zpool(implementation_name)``.
First, get an instance:

.. code-block:: pycon

    >>> from simplezfs import get_zfs
    >>> zfs = get_zfs('cli')  # or "native" for the native API
    >>> zfs
    <simplezfs.zfs_cli.ZFSCli object at 0x7ffbca7fb9e8>
    >>>
    >>> for ds in zfs.list_datasets():
    ...     print(ds.name)
    ...
    tank
    tank/system
    tank/system/rootfs

Compatibility
*************
The library is written with `Python` 3.6 or higher in mind, which was in a stable release in a few of the major Linux
distributions we care about (Debian Buster, Ubuntu 18.04 LTS, RHEL 8, Gentoo).

On the OpenZFS_ side, the code is developed on version ``0.8`` and newer, and takes some validation values from that
release. The library doesn't make a lot of assumptions, the code should work on ``0.7``, too. If you spot an
incompatibility, please let us know via the issue tracker.

Testing
*******
An extensive set of tests are in the ``tests/`` subfolder, it can be run using ``pytest`` from the source of the
repository. At this time, only the validation functions and the ZFS Cli API are tested, the tests are non-destructive
and won't run the actual commands but instead mock away the ``subprocess`` invocations and supply dummy commands to run
(usually ``/bin/true``) should the code be changed in a way that isn't caught by the test framework. Nevertheless, keep
in mind that if commands are run for whatever reason, they most likely result in unrecoverable data loss.

It is planned to add a separate set of `destructive` tests that need to be specially activated for testing if the code
works when run against an actual Linux system. This can't be done using most of the CI providers, as the nature of ZFS
requires having a operating system with loaded modules that may be destroyed during the test run.

.. _OpenZFS: https://openzfs.org/
