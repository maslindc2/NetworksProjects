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
    
    def create_socket(self) -> socket:
        try:
            sender_socket = socket(AF_INET, SOCK_DGRAM)
            sender_socket.bind(('0.0.0.0', self.port_number))
            return sender_socket
        except PermissionError:
            print(f"PERMISSION ERROR: You do not have permission to use the current port!")

    def rdt_recv(self, sender_socket:socket):
        # Verify that the received packet has a correct checksum
        try:
            ack_packet, address = sender_socket.recvfrom(1024)
            print(f'Received response from {address}: {ack_packet}')
            return ack_packet, address

        except Exception as e:
            if "timed out" in str(e):
                #Resubmit the UDP packet
                print("No response received. Retrying....")
                return None, None
        
    def isACK(self, rcv_packet: bytes, seq_num) -> bool:
        print(f"Received Packet: {rcv_packet}")
        # Extract ACK number and sequence number
        if len(rcv_packet) == 12:
            print("We got an ACK Packet")
            length_bytes = rcv_packet[10:]

            # Extract the integer values from the byte string
            ack_number = (int.from_bytes(length_bytes, byteorder='big') >> 14) & 1
            sequence_number = (int.from_bytes(length_bytes, byteorder='big') >> 15) & 1

            if ack_number == 1 and sequence_number == seq_num:
                return True
            else:
                return False
        else:
            return False
        


        

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
            ack_num = 0
            seq_num = 0
            udp_packet = make_packet(app_msg_str, ack_num, seq_num)

            print(f"Created packet: {udp_packet}")

            # TODO: Setup time out function
            # Wait 3s
            sender_socket.settimeout(3)
            
            while True:
                try:
                    sender_socket.sendto(udp_packet, ('0.0.0.0', self.port_number+1))
                    print("Waiting for ACK")
                    
                    packet_recv, address = self.rdt_recv(sender_socket)

                    if packet_recv and address:
                        # verify the packet is not corrupt
                        if not verify_checksum(packet_recv) and not self.isACK(packet_recv, 0):
                            print(f"CheckSum: {verify_checksum(packet_recv)}")
                            print(f"ACK Result: {self.isACK(packet_recv, 0)}")
                            print("SENDING PACKET AGAIN AS IT WAS CORRUPT OR WRONG ACK")
                            sender_socket.sendto(udp_packet, ('0.0.0.0', self.port_number+1))
                        else:
                            print("All Good Send the next one please.....")
                            break
                    else:
                        print("Timeout occurred retrying...")

                except KeyboardInterrupt:
                    print("User exited with ctrl+c")
                    break
