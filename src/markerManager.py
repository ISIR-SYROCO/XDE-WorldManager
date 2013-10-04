import xdefw.rtt
import rtt_interface

class MarkerManager(xdefw.rtt.Task):
    def __init__(self, name, time_step, wm):
        super(MarkerManager, self).__init__(rtt_interface.PyTaskFactory.CreateTask(name))
        self._wm = wm
        self.s.setPeriod(time_step)
        self.fixedMarkers = [] #list of string
        self.bodyMarkers = [] #list of string

        self.markersPositionPort = self.addCreateOutputPort("markerPositionPort_out", "vector_pair_Displacementd_string")

    def startHook(self):
        pass

    def stopHook(self):
        pass

    def updateHook(self):
        markers_msg = []
        for body_name in self.bodyMarkers:
            if body_name in  self._wm.ms.getBodyNames():
                markers_msg.append((self._wm.phy.s.GVM.RigidBody(body_name).getPosition(), body_name))
            else: #the body has been removed
                print "Body "+body_name+" has been removed"
                self.removeMarker(body_name)

        self.markersPositionPort.write(markers_msg)

    def addBodyMarker(self, body_name, thin_marker=False):
        if body_name in self._wm.ms.getBodyNames():
            if body_name in self.bodyMarkers:
                print "Marker "+body_name+" already exists"
            else:
                self.bodyMarkers.append(body_name)
                self._wm.graph_scn.MarkersInterface.addMarker(body_name, thin_marker)
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

