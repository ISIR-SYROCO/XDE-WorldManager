

import loader
import deploy
deploy.loadTypekitsAndPlugins()

import sys
import os
import inspect
cpath = os.path.dirname(os.path.abspath(inspect.getfile( inspect.currentframe()))) + "/"
sys.path.append(cpath)



from core import WorldManager
