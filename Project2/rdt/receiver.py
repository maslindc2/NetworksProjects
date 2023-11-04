from socket import *
from time import sleep
# Importing util.py as we need to access our utility functions
from util import *
## No other imports allowed

def create_socket(PORT_NUMBER:int):
    """
    Creates a socket object used later for receiving and sending UDP packets.
    Returns:
        receiver_socket (socket): This is the socket we will use for receiving and sending UDP packets.
    """
    try:
        receiver_socket = socket(AF_INET, SOCK_DGRAM)
        receiver_socket.bind(('0.0.0.0', PORT_NUMBER))
        return receiver_socket
    except PermissionError:
        print("PERMISSION ERROR: You do not have permission to use the current port. Please change the var listening_port")
        return None

def rdt_recv(receiver_socket: socket):
    """
    RDT Received function handles receiving packets from the sender
    Args:
        receiver_socket (socket): This is the socket connection for the receiver class, used here for receiving packets from the sender
    Returns:
        rcv_packet (bytes): This is the packet we have received from the sender
        address: This is the sender's address
    """
    try:
        # Receive the response that was sent from the sender
        rcv_packet, address = receiver_socket.recvfrom(1024)
        
        # Return the received rcv_packet
        return rcv_packet, address
    
    except KeyboardInterrupt:
        print("Server interrupted by user (Ctrl+c). Closing Connection")
        
        # When Ctrl+c is pressed close the connection
        receiver_socket.close()
        
        # Return NoneType, NoneType this is done to handle breaking the connection loop
        return None, None

def extract_message(rcv_packet: bytes) -> str:
    """
    Extract message function used for getting the message out of the packet we have received
    Args:
        rcv_packet (bytes): This is the packet we have received from the sender
    Returns:
        (str): The decoded message as a string used later for printing
    """
    # Message is located past the 12th bit
    packet_data = rcv_packet[12:]
    
    # Return the decoded message
    return packet_data.decode('utf-8')

def send_packet(receiver_socket: socket, sender_address: str, ack_num:int, seq_num: int):
    """
    Send Packet function makes an ACK packet and send the ACK packet back to the sender using the provided parameters
    Args:
        receiver_socket (socket): This is the receiver socket object for sending ACK packets back to the sender
        sender_address (str): This is the sender's IP Address, as it is configured sender and receiver are both located on localhost but on different sockets
        ack_num (int): This is the ACK number we are going to use for our ACK packet
        seq_num (int): This is the SEQ number we are going to use for our ACK packet
    """
    # Make packet using None as the data_str this tells make_packet function to make an ACK packet
    # Use the provided ack_num and seq_num
    response_packet = make_packet(None, ack_num, seq_num)

    # Send the ACK packet to the receiver
    receiver_socket.sendto(response_packet, sender_address)

if __name__ == "__main__":

    # This variable sets the port number for the receiver socket to use
    PORT_NUMBER = (10100 + (4202012) % 400) + 1

    # This is used for controlling the amount of time the receiver sleeps when simulating timeouts
    # If you want a longer delay set this variable
    ADJUST_TIMEOUT = 3

    # Create the receiver socket we will be using
    receiver_socket = create_socket(PORT_NUMBER)
    
    print("Receiver Socket Created, starting listening function....\n")

    # Used for keeping track of the number of packets we have received
    packet_num = 0

    # Receiver is always on so we can keep track of the sequence numbers easily
    expected_seq_num = 0
    
    # This variable is used when the sender sends a packet that is out of sequence
    # The receiver will ack the last correctly received packet.
    last_correctly_received_ack_num = 0
    
    # Here we set the initial ACK number
    # This will change depending on what state the receiver is in.
    ack_num = 0

    # If the receiver_socket is not NoneType then we have created a socket object and it's safe to start listening for data
    if receiver_socket:

        # Infinite loop to continue listening for packets
        while True:
            
            # This function listens and returns any incoming UDP packets
            rcv_packet, sender_address = rdt_recv(receiver_socket)
                
            # If udp_packet is None then break the loop as the user wanted to quit
            # Since we use a separate receive packet function when the user ctrl+c exits 
            # the function returns NoneType for both rcv_packet and sender_address
            # This handles any Traceback errors that might occur from a simple ctrl+c exit
            if rcv_packet is None and sender_address is None:
                break

            # Verify the checksum
            if verify_checksum(rcv_packet):

                # Here we are extracting the ack number and the sequence number of the packet we just received
                # This function is located in util.py. 
                rcv_ack_num, rcv_seq_num = process_packet_length_section(rcv_packet)

                # Check if the received packet has the correct sequence number for the current state of our receiver
                # Expected_seq_num can be thought of as the "Wait for _ from below" state in the receiver FSM
                # If we are in the state "Wait for 0 from below" then we want a packet with a sequence number of 0
                # If we are in the state "Wait for 1 from below" then we want a packet with a sequence number of 1
                if rcv_seq_num == expected_seq_num:
                    
                    # Here we increment our packet number account to keep track of the successfully received packets
                    packet_num += 1

                    # Here we log the packet we have just successfully received to the file received_pkt.txt
                    write_packet_to_log(rcv_packet, "received_pkt.txt")

                    # Print the current packet number and the packet we have received
                    print(f"Packet Number {packet_num} Received UDP Packet: {rcv_packet}")

                    # If the packet number is divisible by both 3 and 6, simulate a timeout only
                    if packet_num % 6 == 0 and packet_num % 3 == 0:
                        print("Simulating packet loss: sleep a while to trigger timeout event on the sender side....")
                        sleep(ADJUST_TIMEOUT)
                    
                    # If the packet number is divisible by 6 we trigger a timeout on the sender side
                    elif packet_num % 6 == 0:
                        print("Simulating packet loss: sleep a while to trigger timeout event on the sender side....")
                        sleep(ADJUST_TIMEOUT)

                    # If the packet number is divisible by 3 we simulate packet corruption
                    elif packet_num % 3 == 0:
                        print("Simulating packet corruption.")
                        # Remember in RDT3.0 If a packet is corrupted the receiver simply drops the packet and does not send an acknowledgement to the sender
                    
                    # If the packet number is not divisible by 6 or 3 we follow normal RDT3.0 operations
                    else:
                        
                        # Extract the message from the received packet
                        message = extract_message(rcv_packet)
                        print(f"Packet is expected, message string delivered: {message}")
                        
                        print("Packet is delivered, now creating and sending the ACK packet...")
                        # Send our ACK packet
                        send_packet(receiver_socket, sender_address, ack_num, expected_seq_num)
                        
                        # As this packet was successfully received and expected update our last correctly received ack variable
                        last_correctly_received_ack_num = ack_num

                        # Here we are transitioning to a new state since the packet was received correctly move to the next state in the FSM
                        # Transition our sequence number 
                        if expected_seq_num == 0:
                            expected_seq_num = 1
                        else:
                            expected_seq_num = 0
                        
                        # Transition our ack number 
                        if ack_num == 0:
                            ack_num = 1
                        else:
                            ack_num = 0
                    print("All done with this packet\n")

                # If we received a packet that has the wrong sequence number we use our variable last_correctly_received_ack_num to send the last successful ack to the sender
                else:
                    send_packet(receiver_socket, sender_address, ack_num, last_correctly_received_ack_num)
            
            # If we receive a packet with an invalid checksum then we print that we are dropping this packet due to an invalid checksum
            else:
                print("Invalid Checksum! Dropping this packet...\n")
    else:
        print("ERROR: Socket creation failed. Receiver Socket returned NoneType!")