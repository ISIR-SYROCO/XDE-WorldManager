class Contact(object):
    def __init__(self, wm):
        self._wm = wm
        self.contact_info_list = []

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

    def removeAllInteractionsInvolving(self, body_name):
        """ Remove all interaction that involving body_name.

        :param body_name: the name of the body
        """
        occ = self._wm.phy.s.Connectors.OConnectorContactBody("occ")
        for interactions in occ.getInteractions():
            if body_name in interactions:
                occ.removeInteraction(interactions[0], interactions[1])


    def hideAllContacts(self):
        """ Remove the visualization of all interactions already registered.
        """
        occ = self._wm.phy.s.Connectors.OConnectorContactBody("occ")
        occ.removeAllInteractions()

    def createOConnectorContactBody(self, connector_name, port_name, body1_name, body2_name):
        """ Create the OConnectorContactBody and define the interaction for the pair (body1, body2).

        :param string connector_name: the name of the new output connector
        :param string port_name: the name of the OutputPort<SMsg>, which transmits interaction data
        :param string body1_name: the name of the first body
        :param string body2_name: the name of the second body
        :rtype: a :class:`contact.ContactInfo` instance associated to this interaction
        """
        phy = self._wm.phy

        if connector_name in phy.s.Connectors.getOConnectorNames():
            print "Connector "+connector_name+" already exists"
            return
        else:
            connector = phy.s.Connectors.OConnectorContactBody.new(connector_name, port_name)
            connector.addInteraction(body1_name, body2_name)

            contact_info = ContactInfo()
            contact_info.body1 = body1_name
            contact_info.body2 = body2_name
            contact_info.connector = connector
            contact_info.port = phy.getPort(port_name)

            self.contact_info_list.append(contact_info)

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
