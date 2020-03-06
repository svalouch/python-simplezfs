.. _privilege_escalation_helper:

###########################
Privilege Escalation Helper
###########################

The Privilege Escalation Helper (**PE Helper**) mechanism works around the problem that only `root` is allowed to
manipulate the global namespace on Linux hosts, which means that only `root` can mount and unmount filesystems /
filesets. In normal operation, users can be granted permission to do almost anything with a ZFS, except for mounting.

Thus, elevated privileges are required for these actions, which in particular revolves around:
* Creating a fileset with the ``mountpoint`` property set
* Mounting or unmounting a fileset
* Destroying a mounted fileset

While the PE Helper may be useful in other areas, such as acting as a ``sudo(8)`` wrapper, its use is limited to the
bare minimum. All other actions can be performed by using ``zfs allow`` to allow low-privilege-users to perform them.

There are two implementations of PE Helpers provided:

* :class:`~simplezfs.pe_helper.ExternalPEHelper` which runs a user-specified script or program to perform the actions,
  one is provided as an example in the `scripts` folder. This is the most flexible and possibly the most dangerous way
  to handle things.
* :class:`~simplezfs.pe_helper.SudoPEHelper` simply runs the commands through ``sudo(8)``, so the user needs to set up
  their ``/etc/sudoers`` accordingly.

Additonal implementations need only to inherit from :class:`~simplezfs.pe_helper.PEHelperBase`.

When to use
***********
The helper is generally only required on Linux, where, according to the ``zfs(8)`` manpage on ``zfs allow``, the
``mount(8)`` "command restricts modifications of the global namespace to the root user".

The permissions that require ``root`` are:

* ``mount``
* ``unmount``
* ``canmount``
* ``rename``
* ``share``

As some commands manipulate the namespace, the following actions require root permission:

* ``clone``
* ``create`` (:func:`~simplezfs.ZFS.create_fileset` because it mounts it right away)
* ``destroy`` (:func:`~simplezfs.ZFS.destroy_dataset`)
* ``mount``
* ``promote``
* ``receive``
* ``rename``
* ``rollback``
* ``share``
* ``snapshot`` (:func:`~simplezfs.ZFS.create_snapshot`)

Additionally, changing the ``mountpoint`` property on filesets (:func:`~simplezfs.ZFS.set_mountpoint`)

When not to use
***************
The privilege escalation helper implements only the absolute minimum that is required. For everything else, the user
is expected to use ``zfs allow`` to delegate the permissions to the user. For example, it does not implement volume
creation, only filesets are handled.

Delegation (``zfs allow``)
**************************
Using ``zfs allow``, a lot of the required permissions can be delegated to the user. For example, to create volumes,
one needs the following permissions:

* ``create``
* ``volsize``
* ``refreservation``

``create`` is the command, and ``volsize`` and ``refreservation`` are properties set by ``zfs create -V <size>
<dataset>``. Some more may be required with other options (such as ``volblocksize`` etc.) Since it does not mount the
volume (as opposed to a fileset), the privilege escalation helper is not required and the permissions are expected to
be delegated to the user running the program using ``zfs allow``.

Implementations
***************
This section is about the PE Helper implementation provided, from a user point of view.

SudoPEHelper
============
The helper probably used most uses standard ``sudo(0)`` to escalate privileges. It basically prefixes the commands to
run with ``sudo -n``. It is the most straight-forward way to go, and relies on the ``sudoers(5)`` file to allow
passwordless sudo for the ZFS commands. Entering a password is not supported. As the only account that is allowed to
mount, the user used is not configurable.

Example
-------

.. code-block:: python

   from simplezfs.zfs import get_zfs
   from simplezfs.pe_helper import SudoPEHelper
   z = get_zfs(pe_helper=SudoPEHelper(), use_pe_helper=True)
   z.create_fileset('rpool/test/test', mountpoint='/tmp/test')

ExternalPEHelper
================
This helper uses an external script that carries out the work. A script is provided as an example (`scripts`
subfolder).

Calling convention
------------------
The `first` parameter denotes the ``action``, followed by one or two parameters:

* ``create`` is used when creating a fileset. It receives the ``fileset`` name, and the ``mountpoint``. The PE helper
  should then issue the equivalent to ``zfs create -o mountpoint=$mountpoint $fileset``.
* ``set_mountpoint`` sets or changes the mountpoint property of filesets, which usually results in remounting to the
  new location. It receives the ``fileset`` name and the new ``mountpoint``.
* ``import``/``export`` imports or exports a pool. It takes a ``pool`` name as parameter.

Reporting
---------
If all went well, the helper shall return ``0`` as exit code. Otherwise, the exit code denotes the nature of the
problem. Text output to stdout/stderr is captured and logged as info (if the exit code is ``0``) or error (otherwise).
The logger is either called ``simplezfs.zfs.pe_helper`` or ``simplezfs.zpool.pe_helper``, depending on the usage.

+-------+------------------------------------------------------------------------+
| Exit  | Meaning                                                                |
+-------+------------------------------------------------------------------------+
| ``0`` | Everything went well                                                   |
+-------+------------------------------------------------------------------------+
| ``1`` | Parameter or general error, such as missing utilities                  |
+-------+------------------------------------------------------------------------+
| ``2`` | The parent directory does not exist or is not a directory              |
+-------+------------------------------------------------------------------------+
| ``3`` | The parent dataset does not exist                                      |
+-------+------------------------------------------------------------------------+
| ``4`` | The target fileset is not in the hierarchy of the parent dataset       |
+-------+------------------------------------------------------------------------+
| ``5`` | The mountpoint is not inside the parent directory or otherwise invalid |
+-------+------------------------------------------------------------------------+
| ``6`` | Calling the zfs utilities failed (when carrying out the command)       |
+-------+------------------------------------------------------------------------+

