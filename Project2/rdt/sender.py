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

        # This is used for adjusting the port number the sender will be using to communicate with the receiver
        self.port_number = 10100 + (4202012) % 400

        # Create the UDP socket for communicating with the Receiver
        self.sender_socket = self.create_socket()
    
    def create_socket(self) -> socket:
        """
        This function handles creating a socket for the sender to send and receive packets.
        Returns:
            sender_socket (socket): This is the socket we will be using for sending and receiving packets
        """
        try:
            sender_socket = socket(AF_INET, SOCK_DGRAM)
            sender_socket.bind(('0.0.0.0', self.port_number))
            print(f"Socket created! Ready to send...")
            return sender_socket
        except PermissionError:
            print(f"PERMISSION ERROR: You do not have permission to use the current port: {self.port_number}")

    def rdt_recv(self, sender_socket:socket):
        # Receive the ACK packet from the receiver
        try:
            # Store the received packet and address
            rcv_packet, address = sender_socket.recvfrom(1024)
            # Return the ack_packet and the address
            return rcv_packet, address
        
        except Exception as e:
            # If the packet timed out socket.timeout will throw an exception
            # If the exception contains timed out we handle it our own way
            if "timed out" in str(e):
                return None, None
            else:
                print(e)
                return None, None
    
    def process_length(self, rcv_packet: bytes):
        # Extract the length section
        packet_length_bytes = rcv_packet[10:]
            
        # Convert it to an int
        packet_length_int = int.from_bytes(packet_length_bytes, 'big')
            
        # Convert the int into a binary string
        packet_length_binary = bin(packet_length_int)

        # Extract the ACK Number with received from the Receiver
        rcv_ack_num = int(packet_length_binary[-2])
        # Extract the SEQ Number we received from the Receiver
        rcv_sequence_num = int(packet_length_binary[-1])
        
        return rcv_ack_num, rcv_sequence_num

    def isACK(self, rcv_packet: bytes, expected_ack_num):
        # An ACK packet is always going to be of length 12 bytes
        if len(rcv_packet) == 12:
            # Store the ack number we received
            # The receiver does not send sequence numbers in the ACK packet
            rcv_ack_num, rcv_seq_num = process_packet_length_section(rcv_packet)

            # If the received ack number matches the ACK we expected then we got an ACK for the packet we sent
            if rcv_ack_num == expected_ack_num:
                return True
            # If it doesn't match we sent an out of sequence packet
            else:
                return False
        

    def rdt_send(self, app_msg_str):
        """
        Reliably send a message to the receiver (MUST-HAVE DO-NOT-CHANGE)
        Args:
            app_msg_str: the message string (to be put in the data field of the packet)
        """

        # This is the ack_num and sequence nums we will be using to generate the packet initially
        ack_num = 0
        seq_num = 0

        # This flag is used solely for a print statement to let the user know we are retransmitting
        # This exists to try and match the professor's sample output
        isRetransmission = False

        # Display the original message
        print(f"Original message string: {app_msg_str}")
        
        # Create packet with 0 for ack and 0 for sequence number
        udp_packet = make_packet(app_msg_str, ack_num, seq_num)

        # Wait 3s for timeout value
        self.sender_socket.settimeout(3)
        
        # Send the UDP packet to the localhost on generated port number + 1
        self.sender_socket.sendto(udp_packet, ('0.0.0.0', self.port_number+1))

        while True:
            try:
                # Receive and store the ack packet and the receiver's address
                rcv_packet, address = self.rdt_recv(self.sender_socket)
                
                # If these two variables are NOT NoneType then we got a response
                if rcv_packet and address:

                    # Check if the packet was corrupted
                    if verify_checksum(rcv_packet):

                        # If the received packet is an ACK and the received packet has the expected ACK_NUM
                        if self.isACK(rcv_packet, ack_num):
                            # Write the packet we used to our log
                            write_packet_to_log(udp_packet, "sent_pkt.txt")

                            # If we are not retransmitting then print the packet we created
                            # This is here to try and match the professor's sender side output example
                            if not isRetransmission:
                                print(f"Packet created: {udp_packet}")

                            print("Packet was sent successfully to the receiver!")
                            
                            # Then print that the packet was received correctly with the sequence number and the ack number
                            print(f"Packet is received correctly: SEQ = {seq_num} ACK = {ack_num}")
                            print("All Done\n")
                            
                            # Break because we successfully sent the message the sender class was provided
                            break
                        else:
                            # If we are here that is because we did not receive an ACK for the packet we sent
                            # Check if our current sequence number is 0 if so we are in the wrong state and need to move to seq=1
                            if seq_num == 0:
                                # Transition the sequence number to the correct one.
                                # Wrong sequence numbers will always be the sender starts on sequence 0 but the receiver is at 1
                                # This is because the sender is receiving one message at a time from main.py
                                seq_num = 1
                                
                                # Make the packet with the correct sequence number
                                udp_packet = make_packet(app_msg_str, ack_num, seq_num)

                                # Send the packet to the receiver
                                self.sender_socket.sendto(udp_packet, address)

                                # Transition our ack_num to be the expected ack number.
                                # If we send a packet with the sequence number of 1 we expect an ACK of 1
                                ack_num = 1
                            else:
                                # Here we print sender error as something went wrong with the sequence number
                                # This serves as a core dump of sorts.  The receiver should have sent an ACK for the packet we sent as it is the correct sequence number
                                # This statement hopefully should never execute but if it does quit sending because something went wrong.
                                print(f"SENDER ERROR: Something went wrong with transitions ACK = {ack_num}, SEQ = {seq_num}, PACKET: {rcv_packet}")
                                break
                else:
                    # print that we are retransmitting
                    print(f"[Timeout retransmission]: {app_msg_str}")
                    # Print the packet that we are sending again.
                    print(f"Sending packet: {udp_packet}")
                    
                    # Set this retransmission flag to prevent creating packet print executing again
                    # This is purely done to match the professor's sender side example
                    isRetransmission = True
                    
                    # If the socket timed out then we need to resend the packet we made to the receiver
                    self.sender_socket.sendto(udp_packet, ('0.0.0.0', self.port_number+1))
            
            # Here we handle ctrl+c exits gracefully
            except KeyboardInterrupt:
                print("User exited with ctrl+c")
                break