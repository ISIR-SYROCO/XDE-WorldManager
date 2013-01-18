import agents.physic.core
import agents.physic.builder

phy = None
ms = None
xcd = None


def createTask():
    phy = agents.physic.core.createAgent("physic", 0)
    setProxy(phy);
    return phy

def setProxy(_phy):
    global phy
    phy = _phy

def init(_timestep):
    global ms, xcd, phy

    ms = agents.physic.core.createGVMScene(phy, "main", time_step=_timestep, uc_relaxation_factor=.1)
    xcd = agents.physic.core.createXCDScene(phy, "xcd", "LMD", lmd_max=0.01)
    ms.setGeometricalScene(xcd)


def deserializeWorld(world):
    agents.physic.builder.deserializeWorld(phy, ms, xcd, world)

def startTask():
    phy.s.start()

