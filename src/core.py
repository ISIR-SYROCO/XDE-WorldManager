#!/xde

import clockTask
import physic
import graphic
import contact

import desc
import desc.scene

import sys
import dsimi

import rtt_interface_corba
rtt_interface_corba.Init(sys.argv)

def getAllAgents():
	import clockTask
	clock = dsimi.rtt.Task(rtt_interface_corba.GetProxy("dio/component/clock", False))
	clockTask.clock = clock

	import physic
	phy_p = rtt_interface_corba.GetProxy("physic", False)
	phy = dsimi.rtt.Task(phy_p, binding_class = dsimi.rtt.ObjectStringBinding, static_classes=['agent'])

	physic.setProxy(phy)
	physic.ms = phy.s.GVM.Scene("main")
	physic.xcd = phy.s.XCD.Scene("main")

	import graphic
	graph_p = rtt_interface_corba.GetProxy("graphic", False)
	graph = dsimi.rtt.Task(graph_p, binding_class = dsimi.rtt.ObjectStringBinding, static_classes=['agent'])
	graphic.setProxy(graph)
	graphic.graph_scn=graph.s.Interface("mainScene")

	return clock, phy, graph

verbose = False

def verbose_print(msg):
    if verbose is True:
        print(msg)

def createAllAgents(TIME_STEP, create_graphic=True, lmd_max=.01, uc_relaxation_factor=.1):
    """
    Create and configure graphic, physic agent and a clock task.
    Basic connectors are created in the graph agent:
    icb     Body state
    icf     Frame position
    icc     Contact information
    Physic is sync-ed with the clock
    """
    verbose_print("CREATE CLOCK...")
    clock = clockTask.createClock()


    verbose_print("CREATE PHYSIC...")
    phy = physic.createTask()
    physic.init(TIME_STEP, lmd_max=lmd_max, uc_relaxation_factor=uc_relaxation_factor)
    phy.s.Connectors.OConnectorBodyStateList.new("ocb", "body_state")
    phy.s.Connectors.OConnectorContactBody.new("occ", "contacts")

    verbose_print("CREATE PORTS...")
    phy.addCreateInputPort("clock_trigger", "double")
    icps = phy.s.Connectors.IConnectorSynchro.new("icps")
    icps.addEvent("clock_trigger")
    clock.getPort("ticks").connectTo(phy.getPort("clock_trigger"))


    if create_graphic is True:
        verbose_print("CREATE GRAPHIC...")
        import graphic
        graph = graphic.createTask()
        scene_name = graphic.init()
        graph.s.Connectors.IConnectorBody.new("icb", "body_state_H", scene_name)    #to show bodies
        graph.s.Connectors.IConnectorFrame.new("icf", "framePosition", scene_name)  #to lik with frames/markers
        graph.s.Connectors.IConnectorContacts.new("icc", "contacts", scene_name)    #to show contacts info
    #    icc.setMaxProximity(.05)
    #    icc.setGlyphScale(2)

        graph.getPort("body_state_H").connectTo(phy.getPort("body_state_H"))
        graph.getPort("framePosition").connectTo(phy.getPort("body_state_H"))
        graph.getPort("contacts").connectTo(phy.getPort("contacts"))

        graph.s.start()
    else:
        graph = None


    phy.s.setPeriod(TIME_STEP)
    clock.s.setPeriod(TIME_STEP)

    phy.s.start()
    clock.s.start()

    return clock, phy, graph

def createOConnectorContactBody(connector_name, port_name, body1_name, body2_name):
    """
    Create the OConnectorContactBody and define the interaction for the pair (body1, body2).
    Return the ContactInfo data structure associated.
    """
    phy = physic.phy

    connector = phy.s.Connectors.OConnectorContactBody.new(connector_name, port_name)
    connector.addInteraction(body1_name, body2_name)

    contact_info = contact.ContactInfo()
    contact_info.body1 = body1_name
    contact_info.body2 = body2_name
    contact_info.connector = connector
    contact_info.port = phy.getPort(port_name)

    return contact_info


def addWorld(new_world, stop_simulation=False, deserialize_graphic=True):
    """
    Add the world description into the simulation:
    Deserialize physic, graphic removing redundant material description
    and adding the body state to the OConnectorBodyStateList.

    stop_simulation     if True, the simulation is paused after the deserialization
                        it can be useful to initialize other things.
    """
    phy = physic.phy
    verbose_print("STOP PHYSIC...")
    phy.s.stop()
    old_T = phy.s.getPeriod()
    phy.s.setPeriod(0)

    verbose_print("CREATE WORLD...")
    scene = physic.ms
    Lmat = new_world.scene.physical_scene.contact_materials
    for mat in Lmat:
        if mat in scene.getContactMaterials():
            new_world.scene.physical_scene.contact_materials.remove(mat)

    physic.deserializeWorld(new_world)

    while len(new_world.scene.physical_scene.contact_materials):
        new_world.scene.physical_scene.contact_materials.remove(new_world.scene.physical_scene.contact_materials[-1])
    new_world.scene.physical_scene.contact_materials.extend(Lmat)


    verbose_print("RESTART PHYSIC...")
    phy.s.setPeriod(old_T)
    phy.s.start()
    if stop_simulation is True:
        phy.s.stopSimulation()


    if (deserialize_graphic is True) and (graphic.graph is not None):
        graphic.deserializeWorld(new_world)

        verbose_print("CREATE CONNECTION PHY/GRAPH...")
        ocb = phy.s.Connectors.OConnectorBodyStateList("ocb")
        for b in new_world.scene.rigid_body_bindings:
            if len(b.graph_node) and len(b.rigid_body):
                ocb.addBody(str(b.rigid_body))




def removeWorld(old_world, stop_simulation=False):
    """
    Remove everything included in old_world from the simulation.
    """
    verbose_print("REMOVE CONNECTION PHY/GRAPH...")
    ocb = physic.phy.s.Connectors.OConnectorBodyStateList("ocb")
    for b in old_world.scene.rigid_body_bindings:
        if len(b.graph_node) and len(b.rigid_body):
            ocb.removeBody(str(b.rigid_body))


    if (graphic.graph is not None):
        verbose_print("REMOVE GRAPHICAL WORLD...")
        #delete graphical scene
        def deleteNodeInGraphicalAgent(node):
            for child in node.children:
                deleteNodeInGraphicalAgent(child)
            nname = str(node.name)
            verbose_print('deleting '+nname)
            if graphic.graph_scn.SceneInterface.nodeExists(nname):
                graphic.graph_scn.SceneInterface.removeNode(nname)

        deleteNodeInGraphicalAgent(old_world.scene.graphical_scene.root_node)


    verbose_print("REMOVE PHYSICAL WORLD...")
    phy = physic.phy
    verbose_print("STOP PHYSIC...")
    phy.s.stop()
    old_T = phy.s.getPeriod()
    phy.s.setPeriod(0)

    #delete physical scene
    for mechanism in old_world.scene.physical_scene.mechanisms:
        mname = str(mechanism.name)
        physic.phy.s.deleteComponent(mname)

    scene = physic.ms
    def removeRigidBodyChildren(node):
        for child in node.children:
            removeRigidBodyChildren(child)
        verbose_print("deleting "+node.rigid_body.name)
        rbname = str(node.rigid_body.name)

        if rbname in scene.getBodyNames(): #TODO: Body and rigidBody, the same???
            scene.removeRigidBody(rbname)

        for to_del in [rbname, str(rbname+".comp"), str(node.inner_joint.name)]:
            if to_del in physic.phy.s.getComponents():
                physic.phy.s.deleteComponent(to_del)

    for node in old_world.scene.physical_scene.nodes:
        removeRigidBodyChildren(node)

    verbose_print("REMOVE UNUSED MATERIAL...")
    scene.removeUnusedContactMaterials()

    verbose_print("REMOVE MARKERS...")
    markers = old_world.scene.graphical_scene.markers

    if not len(markers) == 0:
        for marker in markers:
            if marker.name in graphic.graph_scn.MarkersInterface.getMarkerLabels():
                verbose_print("Remove "+marker.name)
                graphic.graph_scn.MarkersInterface.removeMarker(str(marker.name))


    verbose_print("RESTART PHYSIC...")
    phy.s.setPeriod(old_T)
    phy.s.start()
    if stop_simulation is True:
        phy.s.stopSimulation()



def stopSimulation():
    physic.phy.s.stopSimulation()

def startSimulation():
    physic.phy.s.startSimulation()




def addInteraction(pairs_of_contact):
    occ = physic.phy.s.Connectors.OConnectorContactBody("occ")
    for b1, b2 in pairs_of_contact:
        occ.addInteraction(b1, b2)


def removeInteraction(pairs_of_contact):
    occ = physic.phy.s.Connectors.OConnectorContactBody("occ")
    for b1, b2 in pairs_of_contact:
        occ.removeInteraction(b1, b2)


def removeAllInteractions():
    occ = physic.phy.s.Connectors.OConnectorContactBody("occ")
    occ.removeAllInteractions()



def addMarkers(world, bodies_to_display=None, thin_markers=True):
    """
    Add a visual frame to each body of bodies_to_display list.
    If the list is empty, a visual frame is added for all body in world.
    This must be call before addWorld
    """
    if (graphic.graph is None):
        verbose_print("No graphic agent. Nothing to do.")
        return

    allNodeNames = []
    def getNodeName(node):
        allNodeNames.append(node.rigid_body.name)

    if bodies_to_display is None:
        for child in world.scene.physical_scene.nodes:
            desc.core.visitDepthFirst(getNodeName, child)
        bodies_to_display = allNodeNames

    for body_name in bodies_to_display:
        if body_name not in graphic.graph_scn.MarkersInterface.getMarkerLabels():
            addFreeMarkers(world, str(body_name))
        else:
            verbose_print("Warning: "+body_name+" marker already exists. Nothing to do.")

def createMarkerWorld(world_name, marker_name_list):
    marker_world = desc.scene.createWorld(name = world_name)
    addFreeMarkers(marker_world, marker_name_list)

    return marker_world

def addMarkerToSimulation(name, thin_markers=True):
    graphic.graph_scn.MarkersInterface.addMarker(str(name), thin_markers)

def removeMarkerFromSimulation(name):
    graphic.graph_scn.MarkersInterface.removeMarker(str(name))

def addFreeMarkers(world, marker_name_list):
    """
    Add a free marker, in order to update its position,
    write [(Hxdes, marker_name)] in a output port (name, "vector_pair_Displacementd_string")
    connected to graph.getPort("framePosition")
    """
    if not hasattr(marker_name_list, '__iter__'):
        marker_name_list = [marker_name_list]

    for marker_name in marker_name_list:
        marker = world.scene.graphical_scene.markers.add()
        marker.name = marker_name


def removeMarkers(world, bodies_to_hide=None):
    """
    Remove the visual frame attached to each body of bodies_to_display list.
    If the list is empty, a visual frame is removed for all body in world.
    """
    if (graphic.graph is None):
        verbose_print("No graphic agent. Nothing to do.")
        return

    allNodeNames = []
    def getNodeName(node):
        allNodeNames.append(node.rigid_body.name)

    if bodies_to_hide is None:
        for child in world.scene.physical_scene.nodes:
            desc.core.visitDepthFirst(getNodeName, child)
        bodies_to_hide = allNodeNames

    ocb = physic.phy.s.Connectors.OConnectorBodyStateList("ocb")
    for body_name in bodies_to_hide:
        if body_name in graphic.graph_scn.MarkersInterface.getMarkerLabels():
            graphic.graph_scn.MarkersInterface.removeMarker(str(body_name))
        else:
            verbose_print("Warning: "+body_name+" marker does not exist. Nothing to do.")




