
import deploy.deployer as ddeployer

# to create basic rtt tasks
import rtt_interface as rtt
import dsimi.rtt


clock = None


def createClock():
    global clock
    clock = dsimi.rtt.Task(ddeployer.load("clock", "dio::Clock", "dio-cpn-clock", "dio/component/"))
    return clock
