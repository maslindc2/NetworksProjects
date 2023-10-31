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
        self.port_number = 10100 + (4202012) % 500
    
    def rdt_send(self, app_msg_str):
        """
        Reliably send a message to the receiver (MUST-HAVE DO-NOT-CHANGE)
        Args:
            app_msg_str: the message string (to be put in the data field of the packet)
        """

        # Create the UDP socket for communicating with the Receiver
        sender_socket = self.create_socket()

        if sender_socket:
            print("Created Sender Socket")

            print(f"Creating packet with message: {app_msg_str}")
            udp_packet = make_packet(app_msg_str, 0, 0)

            print(f"Created packet: {udp_packet}")

            # TODO: Setup time out function
            # Wait 3s
            sender_socket.settimeout(3)
            
            while True:
                try:
                    sender_socket.sendto(udp_packet, ('0.0.0.0', self.port_number+1))
                    rdt_rcv(sender_socket)

                except KeyboardInterrupt:
                    print("User exited with ctrl+c")
                    break

    def create_socket(self) -> socket:
        try:
            sender_socket = socket(AF_INET, SOCK_DGRAM)
            sender_socket.bind(('0.0.0.0', self.port_number))
            return sender_socket
        except PermissionError:
            print(f"PERMISSION ERROR: You do not have permission to use the current port!")