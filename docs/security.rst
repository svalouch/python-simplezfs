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

Whether the helper is installed **setuid root** or uses **sudo** internally or any other way is up to the user. Head
over to :ref:`privilege_escalation_helper` for more info.

