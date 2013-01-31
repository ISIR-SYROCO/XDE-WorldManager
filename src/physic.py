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

def init(_timestep, lmd_max, uc_relaxation_factor):
    global ms, xcd, phy

    ms = agents.physic.core.createGVMScene(phy, "main", time_step=_timestep, uc_relaxation_factor=uc_relaxation_factor)
    xcd = agents.physic.core.createXCDScene(phy, "xcd", "LMD", lmd_max=lmd_max)
    ms.setGeometricalScene(xcd)


def deserializeWorld(world):
    agents.physic.builder.deserializeWorld(phy, ms, xcd, world)

def startTask():
    phy.s.start()

