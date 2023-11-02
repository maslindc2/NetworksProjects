from socket import *
from time import sleep
from util import *
## No other imports allowed

def create_socket():
    """
    Creates a socket object used later for receiving and sending UDP packets. Adjust the variable port_number if this port is not available.
    Returns:
        receiver_socket (socket): This is the socket we will use for receiving and sending UDP packets.
    """
    try:
        receiver_socket = socket(AF_INET, SOCK_DGRAM)
        # Change this variable for controlling what port receiver is running on
        port_number = 10100 + (4202012) % 500 + 1
        
        receiver_socket.bind(('0.0.0.0', port_number))
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
        print("Listening for incoming data...")
        
        # Receive the response that was sent from the sender
        rcv_packet, address = receiver_socket.recvfrom(1024)
        print("Received a client connection from: ", address)
        # Return the received rcv_packet
        return rcv_packet, address
    
    except KeyboardInterrupt:
        print("Server interrupted by user (Ctrl+c). Closing Connection")
        # When Ctrl+c is pressed close the connection
        receiver_socket.close()
        # Return NoneType, NoneType this is done to handle breaking the connection loop
        return None, None

def extract_seq(rcv_packet: bytes) -> int:
    """
    Extract the sequence number from the received packet located in the packet length section, at bytes 11-12
    Args:
        rcv_packet (bytes): This is the packet we have received from the sender
    Returns:
        seq_num (int): This is the extracted sequence number from the packet we have received
    """
    # Extract the length section
    packet_length_bytes = rcv_packet[10: + 12:]

    # Convert the packet length section from bytes to an integer
    packet_length_int = int.from_bytes(packet_length_bytes, 'big')
            
    # Convert the packet length as an integer into a binary string
    packet_length_binary = bin(packet_length_int)

    # Extract the sequence number from the binary string
    # This is located at the end of the binary string packet length section
    seq_num = int(packet_length_binary[-1])
    
    # Return the extracted sequence number
    return seq_num


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

def send_packet(receiver_socket: socket, sender_address: str, ack_num:int, seq_num:int):
    """
    Send Packet function makes an ACK packet and send the ACK packet back to the sender using the provided parameters
    Args:
        receiver_socket (socket): This is the receiver socket object for sending ACK packets back to the sender
        sender_address (str): This is the sender's IP Address, as it is configured sender and receiver are both located on localhost but on different sockets
        ack_num (int): This is the ACK number we are going to use for our ACK packet
        seq_num (int): This is the SEQ number we are going to use for our ACK packet
    """
    # Make packet using None as the data_str this tells make_packet to make an ACK packet
    # Use the provided ack_num and seq_num
    response_packet = make_packet(None, ack_num, seq_num)
    
    print(f"Generated ACK Packet, now sending...")
    # Send the ACK packet to the receiver
    receiver_socket.sendto(response_packet, sender_address)

if __name__ == "__main__":
    # Create the receiver socket we will be using
    receiver_socket = create_socket()

    
    print("Receiver Socket Created, starting listening function....")

    # TODO Setup simulated timeouts based on packet numbers
    packet_num = 0

    # Receiver is always on so we can keep track of the sequence numbers easily
    expected_seq_num = 0
    last_correctly_received_seq = 0
    ack_num = 0

    while True:
        # Process incoming data
        rcv_packet, sender_address = rdt_recv(receiver_socket)
            
        # If udp_packet is None then break the loop as the user wanted to quit
        # Since we use a separate receive packet function when the user ctrl+c exits 
        # the function returns NoneType for rcv_packet and sender_address
        # This handles any Traceback errors from a simple ctrl+c exit
        if rcv_packet is None and sender_address is None:
            break
        # If we rcv_packet and sender_address is NOT NoneType then we got a packet
        # Increment the packet_num
        else:
            packet_num += 1
            
        # Print the udp packet we just got
        print(f"Received UDP Packet: {rcv_packet}")

        # Verify the checksum
        if verify_checksum(rcv_packet):
            
            # Extract the sequence number of the packet we got
            rcv_seq_num = extract_seq(rcv_packet)

            if rcv_seq_num == expected_seq_num:
                print(f"Success! We expected {expected_seq_num} and got a packet with the seq: {rcv_seq_num}")
                message = extract_message(rcv_packet)
                print(f"Got the message {message}\n")

                # Update the last correctly received packet
                last_correctly_received_seq = rcv_seq_num

                print("Sending ACK Packet")
                
                # Send our ACK packet
                send_packet(receiver_socket, sender_address, ack_num, expected_seq_num)

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

                print(f"Transitioned to Wait for {expected_seq_num} from below\n")
            else:
                print(f"Wrong sequence number, sending last successful packet")
                send_packet(receiver_socket, sender_address, ack_num, last_correctly_received_seq)
                
        else:
            print("Invalid Checksum! Dropping this packet...")