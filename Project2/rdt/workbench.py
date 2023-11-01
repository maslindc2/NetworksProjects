def create_checksum(packet_wo_checksum):
    """create the checksum of the packet (MUST-HAVE DO-NOT-CHANGE)

    Args:
      packet_wo_checksum: the packet byte data (including headers except for checksum field)

    Returns:
      the checksum in bytes
    """
    
    if len(packet_wo_checksum) % 2 == 1:
        packet_wo_checksum += b'\x00'
    
    checksum = 0
    
    for i in range(0, len(packet_wo_checksum), 2):
        word  = (packet_wo_checksum[i] << 8) + packet_wo_checksum[i+1]
        checksum += word

        # If the checksum overflows beyond 16 bits we need to add the carry bit
        if checksum > 0xffff:
            checksum = (checksum & 0xffff) + 1
    # Take the ones complement of the sum
    checksum = ~checksum & 0xffff
    return checksum.to_bytes(2, byteorder='big')

def make_packet(data_str, ack_num, seq_num):
  """Make a packet (MUST-HAVE DO-NOT-CHANGE)
  Args:
    data_str: the string of the data (to be put in the Data area)
    ack: an int tells if this packet is an ACK packet (1: ack, 0: non ack)
    seq_num: an int tells the sequence number, i.e., 0 or 1

  Returns:
    a created packet in bytes

  """

  header = b'COMPNETW'

  if data_str:
      data = data_str.encode('utf-8')

      # Convert packet length 16 to binary within the space of 14 bits
      # The packet length will be 8 bytes, checksum 2 bytes, length 2 bytes and data
      packet_length = len(header) + 2 + 2 + len(data_str)

      # Here we generate the packet length, format it as a binary string such that the 
      # length is 14 bits, next we append the ack_num and seq_num
      packet_length_binary = format(packet_length, '014b') + str(ack_num) + str(seq_num)
      
      # Since the packet length is a binary string in base 2 we must convert it to an int before we can 
      # convert it to bytes.
      packet_length_int = int(packet_length_binary,2)

      # Here we convert the packet length as an int to packet length as a byte for our udp packet
      # We set the length of bytes to use to 2 as our packet length section is 2 bytes
      packet_length_bytes = packet_length_int.to_bytes(2, byteorder='big')

      # Here we are building out the packet with a 2 byte filler for the checksum
      packet_wo_checksum = header + b'\x00\x00' + packet_length_bytes + data

      # Create the checksum for the packet we have made
      checksum = create_checksum(packet_wo_checksum)

      # Now we get the returned checksum and insert it ini it's 2 byte slot
      packet_with_checksum = packet_wo_checksum[:8] + checksum + packet_wo_checksum[10:]
      
      # Return our packet with our checksum
      return packet_with_checksum
      
  else:
      packet_length = len(header) + 2 + 2
      ack_bit = ack_num << 14
      seq_bit = seq_num << 15

      packet_info = packet_length | ack_bit | seq_bit

      packet_info_bytes = packet_info.to_bytes(2, byteorder='big')
      
      packet = header + b'\x00\x00' + packet_info_bytes


      checksum = create_checksum(packet)

      #Insert checksum into the packet replacing the checksum placeholder
      packet_with_checksum = packet[:8] + checksum + packet[10:]

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