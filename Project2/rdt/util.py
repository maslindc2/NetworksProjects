def create_checksum(packet_wo_checksum):
    """
    Create the checksum of the packet (MUST-HAVE DO-NOT-CHANGE)
    Args:
        packet_wo_checksum: the packet byte data (including headers except for checksum field)
    Returns:
        the checksum in bytes
    """
    # If we have a packet of odd length then we must pad it with an empty byte
    if len(packet_wo_checksum) % 2 == 1:
        packet_wo_checksum += b'\x00'
    
    # We will store the created checksum here
    checksum = 0

    # Generate the checksum using the pseudo-UDP header
    for i in range(0, len(packet_wo_checksum), 2):
        # Here we are creating 16 bit word for the checksum, 
        # we first perform a left shift on the current byte by 8 bits
        # we then add the second byte or next byte together to form a checksum_word
        checksum_word = (packet_wo_checksum[i] << 8) + packet_wo_checksum[i+1]
        # We then add the current checksum word to the checksum value
        checksum += checksum_word

    if checksum >> 16:
        # Here we adjust for any carry bits
        # Start by shifting the checksum right by 16 bits, if a carry bit exists we will isolate it here
        # Next we mask out the lowest 16 bits so we have only the value without the carry bit
        # Finally we add the carry bit to the left over value processing any carry bits
        checksum = (checksum >> 16) + (checksum & 0xFFFF)
    
    # Now we take the ones complement of the calculated checksum and we have our final checksum value
    checksum = ~checksum & 0xFFFF

    # Return our checksum in bytes using a 2 byte space.
    return checksum.to_bytes(2, byteorder='big')

def verify_checksum(packet):
    """
    Verify the packet's checksum (MUST-HAVE DO-NOT-CHANGE)
    Args: 
        packet: the whole (including original checksum) packet byte data

    Returns:
        True if the packet checksum is the same as specified in the checksum field
        False otherwise
    """

    # Extract the checksum from the packet we just received
    received_checksum = packet[8:10]

    # Calculate a new checksum using the packet header, checksum placeholder, length, and data
    calculated_checksum = create_checksum(packet[:8] + b'\x00\x00' + packet[10:])

    # See if the received_checksum is the same as the checksum we just calculated
    return received_checksum == calculated_checksum


def create_packet_length_section(packet_length:int, ack_num, seq_num) -> bytes:
    """
    Creates the packet length section of our UDP header
    Args:
        packet_length: the length or number of bytes our packet will be
        ack_num: an int tells if this packet is an ACK packet (1: ack, 0: non ack)
        seq_num an int tells the sequence number, i.e., 0 or 1    
    Return:
        the packet length section in bytes ready to insert into our UDP packet
    """

    # Here we generate the packet_length as a binary string in base 2
    # This will convert the packet length from an int to a 14 bit binary string
    packet_length_binary = format(packet_length, '014b')

    # Now we append our ack_num to the packet_length_binary string
    packet_length_binary += str(ack_num)
        
    # Now we aped our seq_num to the packet_length_binary string
    packet_length_binary += str(seq_num)

    # Since the packet length is a binary string and we want a byte string we need to convert it to an int.
    # Example: If our packet length was 16 we get the binary string = 00000000010000, we then append the ack_num=0 and seq_num=0 we get 0000000001000000
    # When we convert it to an int we get the integer 64
    packet_length_int = int(packet_length_binary, 2)
    
    # Here we convert the packet length from an int to a byte for our udp packet
    # We set the length of the bytes to 2 as our packet_length section is 2 bytes
    # When we convert the packet_length_int=64 to a byte sequence we end up with b'\x00@'
    # Finally return the created packet length section of our header as bytes
    return packet_length_int.to_bytes(2, byteorder='big')

def process_packet_length_section(rcv_packet: bytes):
    """
    Extract the sequence number from the received packet located in the packet length section of the header, at bytes 11-12
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

    # Extract the ACK Number with received from the received packet
    # This is the 2nd to last bit at the end of length section
    rcv_ack_num = int(packet_length_binary[-2])
    
    # Extract the SEQ Number we received from the received packet
    # This is located at the end of length section
    rcv_sequence_num = int(packet_length_binary[-1])
    
    # Return the extracted sequence number
    return rcv_ack_num, rcv_sequence_num

def write_packet_to_log(packet: bytes, file_name:str):
    """
    This function handles writing the packets we have received or sent to a txt log.
    Args:
        packet (bytes): This is the packet that we want to log
        file_name (str): This is the name of the file that we are going to write to
    """
    with open(file_name, "a") as packet_log:
        packet_log.write(str(packet)+"\n")

def make_packet(data_str, ack_num, seq_num):
    """
    Make a packet (MUST-HAVE DO-NOT-CHANGE)
    Args:
        data_str: the string of the data (to be put in the Data area)
        ack: an int tells if this packet is an ACK packet (1: ack, 0: non ack)
        seq_num: an int tells the sequence number, i.e., 0 or 1
    Return:
        a created packet in bytes
    """

    header = b'COMPNETW'

    # If we were supplied data then we have 
    if data_str:
        data = data_str.encode('utf-8')

        # Header is 8 bytes, 2 bytes for checksum, 2 bytes for length with ACK and SEQ nums, data
        packet_length = len(header) + 2 + 2 + len(data)
        
        # Create the packet length section for our udp header
        packet_length_bytes = create_packet_length_section(packet_length, ack_num, seq_num)
        
        # Here we are building out the packet with a 2 byte placeholder for the checksum
        packet_wo_checksum = header + b'\x00\x00' + packet_length_bytes + data

        # Create the checksum for the packet we have made
        checksum = create_checksum(packet_wo_checksum)

        # Now we insert the created checksum into it's 2 byte slot
        packet_with_checksum = packet_wo_checksum[:8] + checksum + packet_wo_checksum[10:]

        # Return our UDP packet with the checksum
        return packet_with_checksum
    
    # If data_str is NoneType then we are making an ACK packet
    else:
        # Header is 8 bytes, 2 bytes for checksum, 2 bytes for packet length with ACK and SEQ nums
        # Notice we do not have a data field as this is an ACK packet
        packet_length = len(header) + 2 + 2

        # Create the packet length section for our udp header
        packet_length_bytes = create_packet_length_section(packet_length, ack_num, seq_num)
        
        # Here we are building out the packet with a 2 byte placeholder for the checksum
        packet_wo_checksum = header + b'\x00\x00' + packet_length_bytes

        # Create the checksum for the packet we have made
        checksum = create_checksum(packet_wo_checksum)

        # Now we insert the created checksum into it's 2 byte slot
        packet_with_checksum = packet_wo_checksum[:8] + checksum + packet_wo_checksum[10:]

        # Return our UDP packet with the checksum
        return packet_with_checksum

###### These three functions will be automatically tested while grading. ######
###### Hence, your implementation should NOT make any changes to         ######
###### the above function names and args list.                           ######
###### You can have other helper functions if needed.                    ######  