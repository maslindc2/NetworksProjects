from socket import *
from util import *

class Sender:
  def __init__(self):
    """ 
    Your constructor should not expect any argument passed in,
    as an object will be initialized as follows:
    sender = Sender()

    Please check the main.py for a reference of how your function will be called.
    """
    self.portNumber = 

  def rdt_send(self, app_msg_str):
    """reliably send a message to the receiver (MUST-HAVE DO-NOT-CHANGE)
    Args:
      app_msg_str: the message string (to be put in the data field of the packet)

    """
    # Used for communicating with the receiver
    clientSocket = self.createConnection()

    # Testing out building a packet
    udpPacket = make_packet(app_msg_str, 0, 0)

    if verify_checksum(udpPacket):
      print("Checksum is valid")
    else:
      print("Checksum invalid")

    


  def createConnection(self):
    try:
      clientSocket = socket(AF_INET, SOCK_DGRAM)
      clientSocket.bind(("0.0.0.0", self.portNumber))
      return clientSocket
    except error:
      print("Failed to create socket")


  ####### Your Sender class in sender.py MUST have the rdt_send(app_msg_str)  #######
  ####### function, which will be called by an application to                 #######
  ####### send a message. DO NOT change the function name.                    #######                    
  ####### You can have other functions if needed.                             #######   