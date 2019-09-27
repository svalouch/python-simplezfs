
#############
Configuration
#############
As the word ``simple`` in the package name implies, there is not much configuration neccessary or possible.

Binaries
********
For the CLI implementation, the binaries ``zfs(8)`` and ``zpool(8)`` are being searched in ``$PATH``, but they may be
specified when creating an instance, in which case the library trusts you and does not perform further checks. To
overwrite, you can:

* specify the ``zfs_exe`` or ``zpool_exe`` `kwarg` when using :func:`~simplezfs.zfs.get_zfs` or
  :func:`~simplezfs.zpool.get_zpool`.
* specify the same `kwarg` when creating :class:`simplezfs.zfs_cli.ZFSCli` or
  :func:`~simplezfs.zpool_cli.ZPoolCli` directly.

Logging
*******
The library makes use of Pythons own `logging` functions. It defines a tree starting with ``simplezfs``:

* ``simplezfs`` (used as a common root only)

  * ``simplezfs.zfs`` used by the :class:`~simplezfs.ZFS` parent class

    * ``simplezfs.zfs.cli`` used by :class:`~simplezfs.zfs_cli.ZFSCli`
    * ``simplezfs.zfs.native`` used by :class:`~simplezfs.zfs_native.ZFSNative`

  * ``simplezfs.zpool`` used by the :class:`~simplezfs.ZPool` parent class

    * ``simplezfs.zpool.cli`` used by :class:`~simplezfs.zpool_cli.ZPoolCli`
    * ``simplezfs.zpool.native`` used by :class:`~simplezfs.zpool_native.ZPoolNative`
