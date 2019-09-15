#######
Testing
#######

``python-zfs`` uses **pytest** for testing. The test code can be found in the ``tests``-subdirectory of the source
tree.

Preparation
===========

Usually, when running the test suite locally in your shell, it is advised to use a virtual environment. Which one
to use is up to the reader. The authors use the ``venv`` module. The requirements can be found in the file
``requirements_develop.txt`` or by installing the module with tests.

.. code-block:: shell-session

   $ python3 -m venv venv
   $ source venv/bin/activate
   (venv) $ pip install -e .[tests]

Running the tests
=================
Then run the tests using pytest: ``pytest -v --cov``. The test suite will be expanded in the future.

Creating local pools and datasets
=================================

Pool with most vdev types
-------------------------
To have a pool with most of the supported vdev types, create a pool from a set of files. The following sequence
creates a set of 64MB files (the minimum size ZFS accepts). The new pool is not really usable for storing data,
mostly because it is based on sparse files and ZFS does not like that. But it should be usable for most of the actions
that one wants to perform on it for testing purposes.

.. code-block:: shell

   mkdir /tmp/z
   for i in {1..12}; do truncate -s 64M /tmp/z/vol$i; done
   sudo zpool create testpool \
        raidz /tmp/z/vol1 /tmp/z/vol2 /tmp/z/vol3 \
        raidz /tmp/z/vol4 /tmp/z/vol5 /tmp/z/vol6 \
        log mirror /tmp/z/vol7 /tmp/z/vol8 \
        cache /tmp/z/vol9 /tmp/z/vol10 \
        spare /tmp/z/vol11 /tmp/z/vol12

The new pool should now look like this:

.. code-block:: none

     pool: testpool
    state: ONLINE
     scan: none requested
   config:
   
   	NAME             STATE     READ WRITE CKSUM
   	testpool         ONLINE       0     0     0
   	  raidz1-0       ONLINE       0     0     0
   	    /tmp/z/vol1  ONLINE       0     0     0
   	    /tmp/z/vol2  ONLINE       0     0     0
   	    /tmp/z/vol3  ONLINE       0     0     0
   	  raidz1-1       ONLINE       0     0     0
   	    /tmp/z/vol4  ONLINE       0     0     0
   	    /tmp/z/vol5  ONLINE       0     0     0
   	    /tmp/z/vol6  ONLINE       0     0     0
   	logs
   	  mirror-2       ONLINE       0     0     0
   	    /tmp/z/vol7  ONLINE       0     0     0
   	    /tmp/z/vol8  ONLINE       0     0     0
   	cache
   	  /tmp/z/vol9    ONLINE       0     0     0
   	  /tmp/z/vol10   ONLINE       0     0     0
   	spares
   	  /tmp/z/vol11   AVAIL
   	  /tmp/z/vol12   AVAIL
   
   errors: No known data errors

For reference, when getting a listing of the pools content, the output should look like this (converted to json using
``json.dumps()`` and pretty-printed for readability:

.. code-block:: json

   {
     "testpool": {
       "drives": [
         {
           "type": "raidz1",
           "health": "ONLINE",
           "size": 184549376,
           "alloc": 88064,
           "free": 184461312,
           "frag": 0,
           "cap": 0,
           "members": [
             {
               "name": "/tmp/z/vol1",
               "health": "ONLINE"
             },
             {
               "name": "/tmp/z/vol2",
               "health": "ONLINE"
             },
             {
               "name": "/tmp/z/vol3",
               "health": "ONLINE"
             }
           ]
         },
         {
           "type": "raidz1",
           "health": "ONLINE",
           "size": 184549376,
           "alloc": 152576,
           "free": 184396800,
           "frag": 0,
           "cap": 0,
           "members": [
             {
               "name": "/tmp/z/vol4",
               "health": "ONLINE"
             },
             {
               "name": "/tmp/z/vol5",
               "health": "ONLINE"
             },
             {
               "name": "/tmp/z/vol6",
               "health": "ONLINE"
             }
           ]
         }
       ],
       "log": [
         {
           "type": "mirror",
           "size": 50331648,
           "alloc": 0,
           "free": 50331648,
           "frag": 0,
           "cap": 0,
           "members": [
             {
               "name": "/tmp/z/vol7",
               "health": "ONLINE"
             },
             {
               "name": "/tmp/z/vol8",
               "health": "ONLINE"
             }
           ]
         }
       ],
       "cache": [
         {
           "type": "none",
           "members": [
             {
               "name": "/tmp/z/vol9",
               "health": "ONLINE"
             },
             {
               "name": "/tmp/z/vol10",
               "health": "ONLINE"
             }
           ]
         }
       ],
       "spare": [
         {
           "type": "none",
           "members": [
             {
               "name": "/tmp/z/vol11",
               "health": "AVAIL"
             },
             {
               "name": "/tmp/z/vol12",
               "health": "AVAIL"
             }
           ]
         }
       ],
       "size": 369098752,
       "alloc": 240640,
       "free": 368858112,
       "chkpoint": null,
       "expandsz": null,
       "frag": 0,
       "cap": 0,
       "dedup": 1,
       "health": "ONLINE",
       "altroot": null
     }
   }
