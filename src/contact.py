class Contact(object):
    def __init__(self, wm):
        self._wm = wm

    def showContacts(self, list_of_body_name_pair, display = True):
		""" Add the visualization of interactions between pairs of bodies.

		:param list pairs_of_contact: a list of bodies name pairs.
        :param display: a bool True to display, False to hide

		For instance, if we want to see the interactions between "b1"/"b2" &
		between "b1"/"b3", the argument will be on the form:
		addInteraction( [("b1", "b2"), ("b1", "b3")] )
		"""
		occ = self._wm.phy.s.Connectors.OConnectorContactBody("occ")
		if display == True:
			for b1, b2 in list_of_body_name_pair:
				occ.addInteraction(b1, b2)
		else:
			for b1, b2 in list_of_body_name_pair:
				occ.removeInteraction(b1, b2)

    def hideAllContacts(self):
        """ Remove the visualization of all interactions already registered.
        """
        occ = self._wm.phy.s.Connectors.OConnectorContactBody("occ")
        occ.removeAllInteractions()

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
