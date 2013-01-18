#!/usr/bin/env python

####################################
#                                  #
# Import all modules: configure... #
#                                  #
####################################
import xde_world_manager as xwm


TIME_STEP = .01

clock, phy, graph = xwm.createAllAgents(TIME_STEP)


import dsimi.interactive
dsimi.interactive.shell()()



