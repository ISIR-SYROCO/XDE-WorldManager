#!/xde

import contact

import desc
import desc.scene

import sys
import dsimi
import deploy.deployer as ddeployer

import dsimi.rtt
import rtt_interface_corba
rtt_interface_corba.Init(sys.argv)

import agents.graphic.simple
import agents.graphic.proto
import agents.graphic.builder
import agents.physic.core
import agents.physic.builder

verbose = False

def verbose_print(msg):
    if verbose is True:
        print(msg)

class WorldManager():
	"""
	"""
	def __init__(self):
		self.phy = None
		self.graph = None
		self.clock = None
		self.ms = None
		self.xcd = None
		self.graph_scn = None
		self.phy_worlds = {}
		self.worlds = []

	def createClockAgent(self, time_step):
		verbose_print("CREATE CLOCK...")
		self.clock = dsimi.rtt.Task(ddeployer.load("clock", "dio::Clock", "dio-cpn-clock", "dio/component/"))
		self.clock.s.setPeriod(time_step)

	def createPhysicAgent(self, time_step, phy_name, lmd_max=0.01, uc_relaxation_factor=0.1):
		verbose_print("CREATE PHYSIC...")
		self.phy = agents.physic.core.createAgent(phy_name, 0)
		self.phy.s.setPeriod(time_step)

		#Init physic
		self.ms = agents.physic.core.createGVMScene(self.phy, "main", time_step=time_step, uc_relaxation_factor=uc_relaxation_factor)
		self.xcd = agents.physic.core.createXCDScene(self.phy, "xcd", "LMD", lmd_max=lmd_max)
		self.ms.setGeometricalScene(self.xcd)

		self.phy.s.Connectors.OConnectorBodyStateList.new("ocb", "body_state")
		self.phy.s.Connectors.OConnectorContactBody.new("occ", "contacts")

		verbose_print("CREATE PORTS...")
		self.phy.addCreateInputPort("clock_trigger", "double")
		icps = self.phy.s.Connectors.IConnectorSynchro.new("icps")
		icps.addEvent("clock_trigger")

	def createGraphicAgent(self, graph_name):
		verbose_print("CREATE GRAPHIC...")
		self.graph = agents.graphic.simple.createAgent(graph_name, 0)

		#Init graphic
		self.graph_scn,scene_name,window_name,viewport_name = agents.graphic.simple.setupSingleGLView(self.graph)
		print scene_name, window_name

		agents.graphic.proto.configureBasicLights(self.graph_scn)
		agents.graphic.proto.configureBasicCamera(self.graph_scn)
		self.graph.s.Viewer.enableNavigation(True)
		self.graph_scn.SceneryInterface.showGround(True)

		self.graph.s.Connectors.IConnectorBody.new("icb", "body_state_H", scene_name)    #to show bodies
		self.graph.s.Connectors.IConnectorFrame.new("icf", "framePosition", scene_name)  #to lik with frames/markers
		self.graph.s.Connectors.IConnectorContacts.new("icc", "contacts", scene_name)    #to show contacts info

	def connectGraphToPhysic(self):
		assert(self.graph is not None)
		assert(self.phy is not None)
		self.graph.getPort("body_state_H").connectTo(self.phy.getPort("body_state_H"))
		self.graph.getPort("framePosition").connectTo(self.phy.getPort("body_state_H"))
		self.graph.getPort("contacts").connectTo(self.phy.getPort("contacts"))

	def disconnectGraphFromPhysic(self):
		assert(self.graph is not None)
		assert(self.phy is not None)

		self.graph.getPort("body_state_H").disconnect()
		self.graph.getPort("framePosition").disconnect()
		self.graph.getPort("contacts").disconnect()


	def changePhy(self, phy_name):
		self.disconnectGraphFromPhysic()
		self.cleanGraph()
		self.getPhysicAgentFromCorba(phy_name)
		if phy_name in self.phy_worlds:
			for world in self.phy_worlds[phy_name]:
				self.addWorldToGraphic(world)
		self.connectGraphToPhysic()

	def connectClockToPhysic(self):
		assert(self.clock is not None)
		assert(self.phy is not None)
		self.clock.getPort("ticks").connectTo(self.phy.getPort("clock_trigger"))

	def startAgents(self):
		if (self.clock is not None):
			self.clock.s.start()

		if (self.phy is not None):
			self.phy.s.start()

		if (self.graph is not None):
			self.graph.s.start()

	def createAllAgents(self, time_step, phy_name="physic", lmd_max=0.01, uc_relaxation_factor=0.1, create_graphic=True, graph_name = "graphic"):
		"""
		Create and configure graphic, physic agent and a clock task.
		Basic connectors are created in the graph agent:
		icb     Body state
		icf     Frame position
		icc     Contact information
		Physic is sync-ed with the clock
		"""
		self.createClockAgent(time_step)
		self.createPhysicAgent(time_step, phy_name, lmd_max, uc_relaxation_factor)

		self.connectClockToPhysic()

		self.clock.s.start()
		self.phy.s.start()

		if create_graphic is True:
			self.createAndConnectGraphicAgent(graph_name)


	def createAndConnectGraphicAgent(self, graph_name):
		assert(self.phy is not None)

		self.createGraphicAgent(graph_name)
		self.connectGraphToPhysic()
		self.graph.s.start()


	def getPhysicAgentFromCorba(self, phy_name):
		phy_p = rtt_interface_corba.GetProxy(phy_name, False)
		self.phy = dsimi.rtt.Task(phy_p, binding_class = dsimi.rtt.ObjectStringBinding, static_classes=['agent'])

		self.ms = self.phy.s.GVM.Scene("main")
		self.xcd = self.phy.s.XCD.Scene("xcd")

	def getGraphicAgentFromCorba(self, graph_name):
		graph_p = rtt_interface_corba.GetProxy(graph_name, False)
		self.graph = dsimi.rtt.Task(graph_p, binding_class = dsimi.rtt.ObjectStringBinding, static_classes=['agent'])

		self.graph_scn = self.graph.s.Interface("mainScene")

	def addWorldToPhysic(self, new_world, stop_simulation=False):
		phy = self.phy
		verbose_print("STOP PHYSIC...")
		phy.s.stop()
		old_T = phy.s.getPeriod()
		phy.s.setPeriod(0)
		scene = self.ms
		Lmat = new_world.scene.physical_scene.contact_materials
		for mat in Lmat:
			if mat in scene.getContactMaterials():
				new_world.scene.physical_scene.contact_materials.remove(mat)

		agents.physic.builder.deserializeWorld(self.phy, self.ms, self.xcd, new_world)

		while len(new_world.scene.physical_scene.contact_materials):
			new_world.scene.physical_scene.contact_materials.remove(new_world.scene.physical_scene.contact_materials[-1])
		new_world.scene.physical_scene.contact_materials.extend(Lmat)

		verbose_print("RESTART PHYSIC...")
		phy.s.setPeriod(old_T)
		phy.s.start()
		if stop_simulation is True:
			phy.s.stopSimulation()

	def addWorldToGraphic(self, new_world):
		if (self.graph is not None):
  			agents.graphic.builder.deserializeWorld(self.graph, self.graph_scn, new_world)

			verbose_print("CREATE CONNECTION PHY/GRAPH...")
			ocb = self.phy.s.Connectors.OConnectorBodyStateList("ocb")
			for b in new_world.scene.rigid_body_bindings:
				if len(b.graph_node) and len(b.rigid_body):
					ocb.addBody(str(b.rigid_body))



	def addWorld(self, new_world, stop_simulation=False):
		"""
		Add the world description into the simulation:
		Deserialize physic, graphic removing redundant material description
		and adding the body state to the OConnectorBodyStateList.

		stop_simulation     if True, the simulation is paused after the deserialization
							it can be useful to initialize other things.
		"""
		phy_name = self.phy.getName()

		verbose_print("CREATE WORLD...")
		self.addWorldToPhysic(new_world, stop_simulation)

		self.addWorldToGraphic(new_world)


		if phy_name in self.phy_worlds:
			self.phy_worlds[phy_name].append(new_world)
		else:
			self.phy_worlds[phy_name] = [new_world]

	def removeWorldFromGraphicAgent(self, world):
		if (self.graph is not None):
			verbose_print("REMOVE CONNECTION PHY/GRAPH...")
			ocb = self.phy.s.Connectors.OConnectorBodyStateList("ocb")

			for b in world.scene.rigid_body_bindings:
				if len(b.graph_node) and len(b.rigid_body):
					ocb.removeBody(str(b.rigid_body))

			verbose_print("REMOVE GRAPHICAL WORLD...")
			def deleteNodeInGraphicalAgent(node):
				for child in node.children:
					deleteNodeInGraphicalAgent(child)
				nname = str(node.name)
				verbose_print('deleting '+nname)
				if self.graph_scn.SceneInterface.nodeExists(nname):
					self.graph_scn.SceneInterface.removeNode(nname)

			deleteNodeInGraphicalAgent(world.scene.graphical_scene.root_node)

			verbose_print("REMOVE MARKERS...")
			markers = world.scene.graphical_scene.markers

			if not len(markers) == 0:
				for marker in markers:
					if marker.name in self.graph_scn.MarkersInterface.getMarkerLabels():
						verbose_print("Remove "+marker.name)
						self.graph_scn.MarkersInterface.removeMarker(str(marker.name))


	def removeWorldFromPhysicAgent(self, world, stop_simulation=False):
		assert(self.phy is not None)
		phy = self.phy

		verbose_print("REMOVE PHYSICAL WORLD...")

		verbose_print("STOP PHYSIC...")
		phy.s.stop()
		old_T = phy.s.getPeriod()
		phy.s.setPeriod(0)

		for mechanism in world.scene.physical_scene.mechanisms:
			mname = str(mechanism.name)
			self.phy.s.deleteComponent(mname)

		scene = self.ms
		def removeRigidBodyChildren(node):
			for child in node.children:
				removeRigidBodyChildren(child)
			verbose_print("deleting "+node.rigid_body.name)
			rbname = str(node.rigid_body.name)

			if rbname in scene.getBodyNames(): #TODO: Body and rigidBody, the same???
				scene.removeRigidBody(rbname)

			for to_del in [rbname, str(rbname+".comp"), str(node.inner_joint.name)]:
				if to_del in self.phy.s.getComponents():
					self.phy.s.deleteComponent(to_del)

		for node in world.scene.physical_scene.nodes:
			removeRigidBodyChildren(node)

		verbose_print("REMOVE UNUSED MATERIAL...")
		scene.removeUnusedContactMaterials()

		verbose_print("RESTART PHYSIC...")
		phy.s.setPeriod(old_T)
		phy.s.start()
		if stop_simulation is True:
			phy.s.stopSimulation()

	def removeWorld(self, old_world, stop_simulation=False):
		"""
		Remove everything included in old_world from the simulation.
		"""
		phy_name = self.phy.getName()

		#delete graphical scene
		self.removeWorldFromGraphicAgent(old_world)

		#delete physical scene
		self.removeWorldFromPhysicAgent(old_world, stop_simulation)

		self.phy_worlds[phy_name].remove(old_world)


	def cleanGraph(self):
		if(self.graph is not None):
			for world in self.phy_worlds[self.phy.getName()]:
				self.removeWorldFromGraphicAgent(world)

	def cleanPhy(self, stop_simulation=False):
		if(self.phy is not None):
			for world in self.phy_worlds[self.phy.getName()]:
				self.removeWorldFromPhysicAgent(world, stop_simulation)

	def stopSimulation(self):
		self.phy.s.stopSimulation()

	def startSimulation(self):
		self.phy.s.startSimulation()


	def addInteraction(self, pairs_of_contact):
		occ = self.phy.s.Connectors.OConnectorContactBody("occ")
		for b1, b2 in pairs_of_contact:
			occ.addInteraction(b1, b2)


	def removeInteraction(self, pairs_of_contact):
		occ = self.phy.s.Connectors.OConnectorContactBody("occ")
		for b1, b2 in pairs_of_contact:
			occ.removeInteraction(b1, b2)


	def removeAllInteractions(self):
		occ = self.phy.s.Connectors.OConnectorContactBody("occ")
		occ.removeAllInteractions()



	def addMarkers(self, world, bodies_to_display=None, thin_markers=True):
		"""
		Add a visual frame to each body of bodies_to_display list.
		If the list is empty, a visual frame is added for all body in world.
		This must be call before addWorld
		"""
		if (self.graph is None):
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
			if body_name not in self.graph_scn.MarkersInterface.getMarkerLabels():
				self.addFreeMarkers(world, str(body_name))
			else:
				verbose_print("Warning: "+body_name+" marker already exists. Nothing to do.")

	def createMarkerWorld(self, world_name, marker_name_list):
		marker_world = desc.scene.createWorld(name = world_name)
		self.addFreeMarkers(marker_world, marker_name_list)

		return marker_world

	def addMarkerToSimulation(self, name, thin_markers=True):
		self.graph_scn.MarkersInterface.addMarker(str(name), thin_markers)

	def removeMarkerFromSimulation(self, name):
		self.graph_scn.MarkersInterface.removeMarker(str(name))

	def addFreeMarkers(self, world, marker_name_list):
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


	def removeMarkers(self, world, bodies_to_hide=None):
		"""
		Remove the visual frame attached to each body of bodies_to_display list.
		If the list is empty, a visual frame is removed for all body in world.
		"""
		if (self.graph is None):
			verbose_print("No graphic agent. Nothing to do.")
			return

		allNodeNames = []
		def getNodeName(node):
			allNodeNames.append(node.rigid_body.name)

		if bodies_to_hide is None:
			for child in world.scene.physical_scene.nodes:
				desc.core.visitDepthFirst(getNodeName, child)
			bodies_to_hide = allNodeNames

		for body_name in bodies_to_hide:
			if body_name in self.graph_scn.MarkersInterface.getMarkerLabels():
				self.graph_scn.MarkersInterface.removeMarker(str(body_name))
			else:
				verbose_print("Warning: "+body_name+" marker does not exist. Nothing to do.")



	def createOConnectorContactBody(self, connector_name, port_name, body1_name, body2_name):
		"""
		Create the OConnectorContactBody and define the interaction for the pair (body1, body2).
		Return the ContactInfo data structure associated.
		"""
		phy = self.phy

		connector = phy.s.Connectors.OConnectorContactBody.new(connector_name, port_name)
		connector.addInteraction(body1_name, body2_name)

		contact_info = contact.ContactInfo()
		contact_info.body1 = body1_name
		contact_info.body2 = body2_name
		contact_info.connector = connector
		contact_info.port = phy.getPort(port_name)

		return contact_info

