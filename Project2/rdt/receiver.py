from socket import *
from time import sleep
from util import *
## No other imports allowed

def create_socket():
    try:
        receiver_socket = socket(AF_INET, SOCK_DGRAM)
        # Change this variable for controlling what port receiver is running on
        port_number = 10100 + (4202012) % 500 + 1
        
        receiver_socket.bind(('0.0.0.0', port_number))
        return receiver_socket
    except PermissionError:
        print("PERMISSION ERROR: You do not have permission to use the current port. Please change the var listening_port")
        return None

def listen_incoming_data(receiver_socket: socket):
    try:
        print("Listening for incoming data...")

        udp_packet, address = receiver_socket.recvfrom(1024)
        
        print("Received a client connection from: ", address)
        
        return udp_packet, address
    
    except KeyboardInterrupt:
        print("Server interrupted by user (Ctrl+c). Closing Connection")
        receiver_socket.close()
        return None, None

def send_response(receiver_socket: socket, sender_address: str, ack_num:int, seq_num:int):
    response_packet = make_packet(None, ack_num, seq_num)

    print("Generated ACK Packet, now sending...")
    receiver_socket.sendto(response_packet, sender_address)

    print("Sent!")

if __name__ == "__main__":
    receiver_socket = create_socket()
    if receiver_socket:
        print("Receiver Socket Created, starting listening function....")
        while True:
            # Process incoming data
            udp_packet, sender_address = listen_incoming_data(receiver_socket)
            
            # If udp_packet is None then break the loop as the user wanted to quit
            if udp_packet is None and sender_address is None:
                break
            
            # Print the udp_packet we got back
            print(udp_packet)

            if verify_checksum(udp_packet):
                print("Valid Checksum!")
                
                # We received a packet correctly let's send an ACK for it
                send_response(receiver_socket, sender_address, 1, 0)
            else:
                print("Invalid Checksum!")
    else:
        print("ERROR: Failed to create receiver socket!")
            
            