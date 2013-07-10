XDE-WorldManager
===============

Module to wrap agents creation and initialization,
add, remove xde world data structure in the simulation graph.
This module import automatically the necessary xde modules.
See example in `./XDE-WorldManager/test`

If `prefix` is not defined, install in python USER_BASE directory (`~/.local` by default)

Install:
---------
Install module:

`python setup.py install [--prefix=PREFIX]`

Dev-mode:
----------------
Create a symlink to `./XDE-WorldManager/src` in `prefix` directory:

`python setup.py develop [--prefix=PREFIX] [--uninstall]`

Build documentation:
--------------------

`runxde.sh setup.py build_doc [--build-dir=BUILD_DIR] [-b TARGET_BUILD]`
