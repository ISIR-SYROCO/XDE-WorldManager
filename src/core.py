#!/xde

import clockTask
import physic
import graphic

import desc

import os



def createAllAgents(TIME_STEP):
    """
    """
    print "CREATE CLOCK..."
    import clockTask
    clock = clockTask.createClock()

    print "CREATE GRAPHIC..."
    import graphic
    graph = graphic.createTask()
    scene_name = graphic.init()
    graph.s.Connectors.IConnectorBody.new("icb", "body_state_H", scene_name)    #to show bodies
    graph.s.Connectors.IConnectorFrame.new("icf", "framePosition", scene_name)  #to lik with frames/markers
    graph.s.Connectors.IConnectorContacts.new("icc", "contacts", scene_name)    #to show contacts info
#    icc.setMaxProximity(.05)
#    icc.setGlyphScale(2)


    print "CREATE PHYSIC..."
    phy = physic.createTask()
    physic.init(TIME_STEP)
    phy.s.Connectors.OConnectorBodyStateList.new("ocb", "body_state")
    phy.s.Connectors.OConnectorContactBody.new("occ", "contacts")

    print "CREATE PORTS..."
    phy.addCreateInputPort("clock_trigger", "double")
    icps = phy.s.Connectors.IConnectorSynchro.new("icps")
    icps.addEvent("clock_trigger")
    clock.getPort("ticks").connectTo(phy.getPort("clock_trigger"))

    graph.getPort("body_state_H").connectTo(phy.getPort("body_state_H"))
    graph.getPort("framePosition").connectTo(phy.getPort("body_state_H"))
    graph.getPort("contacts").connectTo(phy.getPort("contacts"))



    phy.s.setPeriod(TIME_STEP)
    clock.s.setPeriod(TIME_STEP)

    graph.s.start()
    phy.s.start()
    clock.s.start()

    return clock, phy, graph



def addWorld(new_world, stop_simulation=False, deserialize_graphic=True):
    """
    """
    phy = physic.phy
    print "STOP PHYSIC..."
    phy.s.stop()
    old_T = phy.s.getPeriod()
    phy.s.setPeriod(0)

    print "CREATE WORLD..."
    scene = physic.ms
    Lmat = new_world.scene.physical_scene.contact_materials
    for mat in Lmat:
        if mat in scene.getContactMaterials():
            new_world.scene.physical_scene.contact_materials.remove(mat)

    physic.deserializeWorld(new_world)

    while len(new_world.scene.physical_scene.contact_materials):
        new_world.scene.physical_scene.contact_materials.remove(new_world.scene.physical_scene.contact_materials[-1])
    new_world.scene.physical_scene.contact_materials.extend(Lmat)


    print "RESTART PHYSIC..."
    phy.s.setPeriod(old_T)
    phy.s.start()
    if stop_simulation is True:
        phy.s.stopSimulation()


    if deserialize_graphic is True:
        graphic.deserializeWorld(new_world)

        print "CREATE CONNECTION PHY/GRAPH..."
        ocb = phy.s.Connectors.OConnectorBodyStateList("ocb")
        for b in new_world.scene.rigid_body_bindings:
            if len(b.graph_node) and len(b.rigid_body):
                ocb.addBody(str(b.rigid_body))




def removeWorld(old_world):
    """
    """
    print "REMOVE CONNECTION PHY/GRAPH..."
    ocb = physic.phy.s.Connectors.OConnectorBodyStateList("ocb")
    for b in old_world.scene.rigid_body_bindings:
        if len(b.graph_node) and len(b.rigid_body):
            ocb.removeBody(str(b.rigid_body))


    print "REMOVE GRAPHICAL WORLD..."
    #delete graphical scene
    def deleteNodeInGraphicalAgent(node):
        for child in node.children:
            deleteNodeInGraphicalAgent(child)
        nname = str(node.name)
        print 'deleting', nname
        if graphic.graph_scn.SceneInterface.nodeExists(nname):
            graphic.graph_scn.SceneInterface.removeNode(nname)

    deleteNodeInGraphicalAgent(old_world.scene.graphical_scene.root_node)


    print "REMOVE PHYSICAL WORLD..."
    phy = physic.phy
    print "STOP PHYSIC..."
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
        print "deleting", node.rigid_body.name
        rbname = str(node.rigid_body.name)

        if rbname in scene.getBodyNames(): #TODO: Body and rigidBody, the same???
            scene.removeRigidBody(rbname)

        for to_del in [rbname, str(rbname+".comp"), str(node.inner_joint.name)]:
            if to_del in physic.phy.s.getComponents():
                physic.phy.s.deleteComponent(to_del)

    for node in old_world.scene.physical_scene.nodes:
        removeRigidBodyChildren(node)

    print "REMOVE UNUSED MATERIAL..."
    scene.removeUnusedContactMaterials()

    print "RESTART PHYSIC..."
    phy.s.setPeriod(old_T)
    phy.s.start()



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
    """
    allNodeNames = []
    def getNodeName(node):
        allNodeNames.append(node.rigid_body.name)

    if bodies_to_display is None:
        for child in world.scene.physical_scene.nodes:
            desc.core.visitDepthFirst(getNodeName, child)
        bodies_to_display = allNodeNames

    ocb = physic.phy.s.Connectors.OConnectorBodyStateList("ocb")
    for body_name in bodies_to_display:
        if body_name not in graphic.graph_scn.MarkersInterface.getMarkerLabels():
            graphic.graph_scn.MarkersInterface.addMarker(str(body_name), thin_markers)
        else:
            print "Warning: "+body_name+" marker already exists. Nothing to do."


def removeMarkers(world, bodies_to_hide=None):
    """
    """
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
            print "Warning: "+body_name+" marker does not exist. Nothing to do."




