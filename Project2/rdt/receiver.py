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

def rdt_recv(receiver_socket: socket):
    try:
        print("Listening for incoming data...")

        udp_packet, address = receiver_socket.recvfrom(1024)
        
        print("Received a client connection from: ", address)
        
        return udp_packet, address
    
    except KeyboardInterrupt:
        print("Server interrupted by user (Ctrl+c). Closing Connection")
        receiver_socket.close()
        return None, None

def process_seq(rcv_packet: bytes):
    length_bytes = rcv_packet[10:] + rcv_packet[:12]

    # Extract the sequence number from the packet
    sequence_number = (int.from_bytes(length_bytes, byteorder='big') >> 15) & 1
    print(f"SEQ {sequence_number}")

    return sequence_number

def send_response(receiver_socket: socket, sender_address: str, ack_num:int, seq_num:int):
    response_packet = make_packet(None, ack_num, seq_num)
    
    print(f"Generated ACK Packet, now sending...")
    receiver_socket.sendto(response_packet, sender_address)

    print("Sent!")

if __name__ == "__main__":
    receiver_socket = create_socket()
    if receiver_socket:
        print("Receiver Socket Created, starting listening function....")

        packet_num = 0

        while True:
            # Process incoming data
            rcv_packet, sender_address = rdt_recv(receiver_socket)
            
            # If udp_packet is None then break the loop as the user wanted to quit
            if rcv_packet is None and sender_address is None:
                break
            else:
                packet_num += 1
            
            # Print the udp_packet we got back
            print(rcv_packet)

            if verify_checksum(rcv_packet):
                print("Valid Checksum!")
                
                sequence_num = process_seq(rcv_packet)

                # We received a packet correctly let's send an ACK for it
                send_response(receiver_socket, sender_address, 1, sequence_num)

                print("Transitioned to wait for 1 from below")
            else:
                print("Invalid Checksum!")
    else:
        print("ERROR: Failed to create receiver socket!")
            
            