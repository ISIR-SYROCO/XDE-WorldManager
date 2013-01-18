
import agents.graphic.simple
import agents.graphic.proto
import agents.graphic.builder

graph = None
graph_scn = None

def createTask():
  graph = agents.graphic.simple.createAgent("graphic", 0) 
  setProxy(graph)
  return graph

def setProxy(_graph):
  global graph
  graph = _graph

def init():
  global graph, graph_scn

  graph_scn,scene_name,window_name,viewport_name = agents.graphic.simple.setupSingleGLView(graph)
  print scene_name,window_name,viewport_name

  agents.graphic.proto.configureBasicLights(graph_scn)
  agents.graphic.proto.configureBasicCamera(graph_scn)

  graph.s.Viewer.enableNavigation(True)
  graph_scn.SceneryInterface.showGround(True)

  return scene_name




def deserializeWorld(world):
  agents.graphic.builder.deserializeWorld(graph, graph_scn, world)

def startTask():
  graph.s.start()

