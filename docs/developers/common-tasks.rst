Common coding tasks
===================

Adding a new permission
-----------------------

To add a new permission, you first need to get the new permisison accepted into `the subuser standard <https://github.com/subuser-security/subuser-standard>`_ via pull request.

Once it is accepted:

 1. Set the permission's default value, description, and level in the `permissions module <https://github.com/subuser-security/subuser/blob/master/logic/subuserlib/permissions.py>`_

 2. Tell subuser how to apply the permission in the `run module <https://github.com/subuser-security/subuser/blob/master/logic/subuserlib/run.py>`_

Profiling
---------

Running most commands: ``subuser``, ``update``, ``repair`` and ``run`` with the ``SUBUSER_RUN_PROFILER`` environment variable set will run those commands and print profiler output once the command has finnished.
