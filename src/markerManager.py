import xdefw.rtt
import rtt_interface
import lgsm

class MarkerManager(xdefw.rtt.Task):
    def __init__(self, name, time_step, wm):
        super(MarkerManager, self).__init__(rtt_interface.PyTaskFactory.CreateTask(name))
        self._wm = wm
        self.s.setPeriod(time_step)
        self.fixedMarkers = [] #list of string
        self.bodyMarkers = [] #list of string
        self.bodyMarkersOffset = {} #Dictionnary body_name:offset
        self.bodyMarkersMap = {} #Dictionnary marker_name:body_name

        self.markersPositionPort = self.addCreateOutputPort("markerPositionPort_out", "vector_pair_Displacementd_string")

    def startHook(self):
        pass

    def stopHook(self):
        pass

    def updateHook(self):
        markers_msg = []
        for marker_name in self.bodyMarkers:
            body_name = self.bodyMarkersMap[marker_name]
            if body_name in  self._wm.ms.getBodyNames():
                marker_pos = self._wm.phy.s.GVM.RigidBody(body_name).getPosition()*self.bodyMarkersOffset[marker_name]
                markers_msg.append((marker_pos, marker_name))
            else: #the body has been removed
                print "Body "+body_name+" has been removed"
                self.removeMarker(marker_name)

        self.markersPositionPort.write(markers_msg)

    def addBodyMarker(self, body_name, marker_name=None, offset=lgsm.Displacementd(), thin_marker=False):
        if body_name in self._wm.ms.getBodyNames():
            if marker_name is None:
                marker_name = body_name
            if marker_name in self.bodyMarkers:
                print "Marker "+marker_name+" already exists, resetting offset"
                self.bodyMarkersOffset[marker_name] = offset
            else:
                self.bodyMarkers.append(marker_name)
                self.bodyMarkersOffset[marker_name] = offset
                self.bodyMarkersMap[marker_name] = body_name
                self._wm.graph_scn.MarkersInterface.addMarker(marker_name, thin_marker)
        else:
            print "Body not found"

    def addFixedMarker(self, name, thin_marker=False):
        if name in self.fixedMarkers:
            print "Marker "+name+" already exists"
        else:
            self.fixedMarkers.append(name)
            self._wm.graph_scn.MarkersInterface.addMarker(name, thin_marker)

    def removeMarker(self, name):
        if name in self._wm.graph_scn.MarkersInterface.getMarkerLabels():
            self._wm.graph_scn.MarkersInterface.removeMarker(name)
        else:
            print "Marker "+name+" doesn't exist"
            return

        if name in self.bodyMarkers:
            self.bodyMarkers.remove(name)
        elif name in self.fixedMarkers:
            self.fixedMarkers.remove(name)

    def setFixedMarkerPosition6D(self, name, position_H):
        self._wm.graph_scn.MarkersInterface.setMarker6DPosition(name, position_H)

