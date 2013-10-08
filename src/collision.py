import xdefw
import rtt_interface
import lgsm
import numpy as np
import math

def alignz(vector):
    """
    Return the rotation matrix necessary to align the z axis of the 0-frame with a vector

    :param vector: lgsm.vectord of size 3
    :return : lgsm.Rotation3
    """
    angle = np.arccos(vector[2]) #angle vec/Z
    axe = np.cross([0,0,1],vector.transpose()) #find rotation axis from Z to vec

    if lgsm.norm(axe) < 0.001: #Check if Z and vec are parallel
        if vector[2] < 0: #use X axis as rotation axis for Z to vec and 0/pi given vec_z direction
            R = lgsm.Rotation3.fromAxisAngle(lgsm.vectord([1,0,0]), math.pi)
        else:
            R = lgsm.Rotation3.fromAxisAngle(lgsm.vectord([1,0,0]), 0)

    else:
        R = lgsm.Rotation3.fromAxisAngle(axe.transpose(), angle)

    return R

class Collision(object):
    def __init__(self, wm):
        self._wm = wm

    def createCompositePairDescriptor(self, body1_name, body2_name):
        xcd_scene = "xcd"
        body1_comp = self._wm.phy.s.GVM.Body(body1_name).getComposite()
        body2_comp = self._wm.phy.s.GVM.Body(body2_name).getComposite()

        cpd_str = xcd_scene+"/"+body1_comp+"/"+body2_comp
        cpd = self._wm.phy.s.XCD.CompositePairDescriptor(cpd_str)

        return cpd

    def getCompositePairLocalDisplacement(self, *args):
        """
        Return a pair of displacement that represent the position of the closest point that belongs
        to a pair of body in the body frame

        :param body1_name: string
        :param body2_name: string
        :return: ai_displacement, aj_displacement

        :param composite_pair_desc: a composite pair descriptor
        """
        if len(args) == 2: #arguments are body_name string
            if type(args[0]) == str:
                body1_name = args[0]
            else:
                raise TypeError("First argument is a string(body1_name)")
            if type(args[1]) == str:
                body2_name = args[1]
            else:
                raise TypeError("Second argument is a string(body2_name)")
            compPairDesc = self.createCompositePairDescriptor(body1_name, body2_name)
        elif len(args) == 1: #argument is a composite_pair_desc
            if str(type(args[0])) == "<class 'xdefw.rtt.CompositePairDescriptor'>":
                compPairDesc = args[0]
            else:
                raise TypeError("Argument is a xdefw.rtt.CompositePairDescriptor")
        else:
            raise TypeError("Wrong number of arguments, usage: getCompositePairLocalDisplacement(body1_name, body2_name) getCompositePairLocalDisplacement(composite_pair_desc)")

        ai = compPairDesc.getGlobalMinDist().ai
        ni = compPairDesc.getGlobalMinDist().ni
        ai_displacement = lgsm.Displacementd()
        ai_displacement.setTranslation(lgsm.vectord(ai[0], ai[1], ai[2]))
        ai_displacement.setRotation(alignz(lgsm.vectord(ni[0], ni[1], ni[2])))

        aj = compPairDesc.getGlobalMinDist().aj
        nj = compPairDesc.getGlobalMinDist().nj
        aj_displacement = lgsm.Displacementd()
        aj_displacement.setTranslation(lgsm.vectord(aj[0], aj[1], aj[2]))
        aj_displacement.setRotation(alignz(lgsm.vectord(nj[0], nj[1], nj[2])))

        return ai_displacement, aj_displacement

class GlobalDistanceVisualizer(xdefw.rtt.Task):
    def __init__(self, name, time_step, wm):
        super(GlobalDistanceVisualizer, self).__init__(rtt_interface.PyTaskFactory.CreateTask(name))
        self._wm = wm
        self.composite_pair_desc_dict = {} #{"body1_body2": (cpd, body1_name, body2_name)}
        self.s.setPeriod(time_step)

    def addCompositePair(self, body1_name, body2_name, thin_marker=False):
        frame_name = body1_name+"_"+body2_name
        cp = self._wm.collision.createCompositePairDescriptor(body1_name, body2_name)

        self.composite_pair_desc_dict[frame_name] = (cp, body1_name, body2_name)
        self._wm.markers.addFixedMarker(frame_name+"ai", thin_marker)
        self._wm.markers.addFixedMarker(frame_name+"aj", thin_marker)

    def listCompositePair(self):
        for cpl in self.composite_pair_desc_dict.items():
            print cpl

    def removeCompositePair(self, name):
        self.composite_pair_desc_dict.pop(name)

    def updateHook(self):
        for cpl in self.composite_pair_desc_dict.items():
            framename_ai = cpl[0]+"ai"
            framename_aj = cpl[0]+"aj"
            Tbodyi_ai, Tbodyj_aj = self._wm.collision.getCompositePairLocalDisplacement(cpl[1][0])

            ai = self._wm.phy.s.GVM.RigidBody(cpl[1][1]).getPosition() * Tbodyi_ai
            aj = self._wm.phy.s.GVM.RigidBody(cpl[1][2]).getPosition() * Tbodyj_aj

            self._wm.markers.setFixedMarkerPosition6D(framename_ai, ai)
            self._wm.markers.setFixedMarkerPosition6D(framename_aj, aj)


