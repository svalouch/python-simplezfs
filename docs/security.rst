########
Security
########

The authors of this library tried their best to make sure that nothing bad happens, but they are only human. Thus:

.. warning:: Use this library at your own risk.

Running as root
***************

The library goes to great length to make sure everything passed to the operating system is safe. Due to the nature of
operating systems, many tasks can only be carried out with elevated privileges, commonly running with the privileges
of the user ``root``. This means that care must be taken when using it with elevated privileges!

Thankfully, ZFS allows to delegate permission to some extend, allowing a user or a group on the local system to carry
out administrative tasks. One exception is mounting, which is handled in the next paragraph.

It is suggested to take a look at the ``zfs(8)`` manpage, especially the part that covers ``zfs allow``.

.. _the_mount_problem:

The mount problem
*****************
On Linux, only root is allowed to manipulate the global namespace. This means that no amount of ``zfs allow`` will
allow any other user to mount a fileset. They can be created with the ``mountpoint`` property set, but can't be
mounted. One workaround is to specify ``legacy``, and using ``/etc/fstab`` to mount it, the other is to install and use
a special privilege escalation (PE) helper.

Elevated privileges are required for the following tasks:

* ``mount`` or ``unmount`` a fileset without the use of ``/etc/fstab`` and ``legacy`` mountpoints
* set or change the ``mountpoint`` property, which results in changing the mountpoint
* ZPool ``import`` or ``export``

Whether the helper is installed **setuid root** or uses **sudo** internally or any other way is up to the user. An
example helper script is provided that will allow creating and moving filesets in a subtree of the ZFS hierarchy and
local filesystem hierarchy.

.. note::

    The helper is provided as an example, use at your own risk.

PE Helper protocol
******************
The PE helper will be called with different sets of parameters, depending on the action to perform. Its exit code
communicates the basic problem or success and output is captured and fed to the logger.

Calling convention
==================
The `first` parameter denotes the ``action``, followed by one or two parameters:

* ``create`` is used when creating a fileset. It receives the ``fileset`` name, and the ``mountpoint``. The PE helper
  should then issue the equivalent to ``zfs create -o mountpoint=$mountpoint $fileset``.
* ``set_mountpoint`` sets or changes the mountpoint property of filesets, which usually results in remounting to the
  new location. It receives the ``fileset`` name and the new ``mountpoint``.
* ``import``/``export`` imports or exports a pool. It takes a ``pool`` name as parameter.

Reporting
=========
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

When to use
===========
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
===============
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
