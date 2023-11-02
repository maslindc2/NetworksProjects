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
    
    def process_length(self, rcv_packet: bytes):

        # Extract the length section
        packet_length_bytes = rcv_packet[10:]
            
        # Convert it to an int
        packet_length_int = int.from_bytes(packet_length_bytes, 'big')
            
        # Convert the int into a binary string
        packet_length_binary = bin(packet_length_int)

        rcv_ack_num = int(packet_length_binary[-2])
        rcv_sequence_num = int(packet_length_binary[-1])
        
        return rcv_ack_num, rcv_sequence_num

    def extract_ACK(self, rcv_packet: bytes):
        
        # An ACK packet is always going to be of length 12 bytes
        if len(rcv_packet) == 12:
            rcv_ack_num, rcv_seq_num = self.process_length(rcv_packet)

            print(f"Got an ACK packet, ACK={rcv_ack_num} SEQ={rcv_seq_num}")
            return rcv_ack_num, rcv_seq_num
        else:
            print(f"ERROR For some reason we got a data packet")
            return None, None
        

    def rdt_send(self, app_msg_str):
        """
        Reliably send a message to the receiver (MUST-HAVE DO-NOT-CHANGE)
        Args:
            app_msg_str: the message string (to be put in the data field of the packet)
        """

        # Create the UDP socket for communicating with the Receiver
        sender_socket = self.create_socket()

        print("Created Sender Socket")

        print(f"Creating packet with message: {app_msg_str}")
            
        ack_num = 0
        seq_num = 0
        expected_ack_num = 0
        expected_seq_num = 0

        # Create packet with 0 for ack and 0 for sequence number
        udp_packet = make_packet(app_msg_str, ack_num, seq_num)

        #TODO: Add function to store the packets to a txt file

        print(f"Created packet: {udp_packet}")
        
        # Wait 3s for timeout value
        sender_socket.settimeout(3)
        
        # Send the UDP packet to the localhost on generated port number + 1
        sender_socket.sendto(udp_packet, ('0.0.0.0', self.port_number+1))

        while True:
            try:
                # Print current status
                print("Waiting for ACK\n")
                
                # Receive and store the ack packet
                rcv_packet, address = self.rdt_recv(sender_socket)

                # If these two variables are NOT NoneType then we got a response
                if rcv_packet and address:
                    # Check if the packet was corrupted
                    if verify_checksum(rcv_packet):
                        # Let's see what our ack is 
                        rcv_ack_num, rcv_seq_num = self.extract_ACK(rcv_packet)

                        # If the received sequence number equals the expected sequence number i.e. we send a seq num 0, and we expect to get an ACK back with the sequence number 0
                        # If we sent the wrong sequence number but we get back the last successfully received packet i.e. we sent seq 0 but the receiver sends the last successfully received packet of seq 0
                        if expected_seq_num == rcv_seq_num:
                            if expected_ack_num == rcv_ack_num:
                                print("Success! We sent the correct packet and got an ACK back")
                                break
                            else:
                                print("OOPS! We sent the wrong sequence number retrying")
                                if seq_num == 0:
                                    seq_num = 1
                                    expected_seq_num = 1
                                    expected_ack_num = 1
                                    
                                udp_packet = make_packet(app_msg_str, expected_ack_num, seq_num)
                                print(f"Created packet: {udp_packet}")
                                sender_socket.sendto(udp_packet, address)
                                print("SENT PACKET")
                else:
                    sender_socket.sendto(udp_packet, ('0.0.0.0', self.port_number+1))

            except KeyboardInterrupt:
                print("User exited with ctrl+c")
                break