class ContactInfo(object):
	""" Data structure to store contact information.

	Attributes:
	
		* body1     	One of the body pair
		* body2     	The other one
		* connector 	The OConnectorContactBody of the physic agents
		* port      	The OutputPort<SMsg> created by the creation of the OConnector
	"""
	body1 = ""
	body2 = ""
	connector = None
	port = None
