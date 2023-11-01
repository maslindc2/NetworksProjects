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
    checksum = 0
    for i in range(0, len(packet_wo_checksum), 2):
        w = (packet_wo_checksum[i] << 8) + packet_wo_checksum[i+1]
        checksum += w

        # If the checksum has a carry-bit i.e. the length is not 16 bits we need to add the carry bit
        if checksum > 0xffff:
            checksum = (checksum & 0xffff) + 1
        # Take the ones complement of the sum
        checksum = ~checksum & 0xffff
        return checksum.to_bytes(2, byteorder='big')


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
    # We format it as a binary string such that the length is 14 bits
    packet_length_binary = format(packet_length, '014b')

    # Now we append our ack_num to the packet_length
    packet_length_binary += str(ack_num)
        
    # Now we aped our seq_num to the packet_length
    packet_length_binary += str(seq_num)

    # Since the packet length is a binary string in base 2, we must convert it to an int 
    # we do this because our desired data type is bytes
    packet_length_int = int(packet_length_binary, 2)

    # Here we convert the packet length from an int to a byte for our udp packet
    # We set the length of the bytes to 2 as our packet_length section is 2 bytes
    packet_length_bytes = packet_length_int.to_bytes(2, byteorder='big')

    return packet_length_bytes

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
    


if __name__ == "__main__":
    
    """
    If the binary is 010000 which is the length 16
    If the binary string is 01000000 = 64 as decimal or @ as ASCII or 0x40 as hex
    If the binary string is 01000001 = 65 as decimal or A as ASCII or 0x41 as hex
    If the binary string is 01000010 = 66 as decimal or B as ASCII or 0x42 as hex
    If the binary string is 01000011 = 67 as decimal or C as ASCII or 0x43 as hex
    Then why is an ACK = 1 and SEQ = 1 equal 0x41
    
    While in office hours ask if the test suite uses an empty string for testing as currently we see if it's none type for generating ACK packets
    """

    packet1 = make_packet('msg1', 0, 0)
    print(packet1)

    packet2 = make_packet('msg2', 0, 1)
    print(packet2)

    packet3 = make_packet('msg3', 0, 0)
    print(packet3)