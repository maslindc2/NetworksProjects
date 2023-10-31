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

def verify_checksum(packet):
    """verify packet checksum (MUST-HAVE DO-NOT-CHANGE)

    Args:
      packet: the whole (including original checksum) packet byte data

    Returns:
      True if the packet checksum is the same as specified in the checksum field
      False otherwise
    """
    # Extract the checksum, convert it to an int from bytes
    received_checksum = int.from_bytes(packet[8:10], byteorder='big')
    # Go and calculate a new checksum using the packet header the empty checksum, length, and data
    calculated_checksum = create_checksum(packet[:8] + b'\x00\x00' + packet[10:])
    # Return the boolean result of received_checksum == calculated_checksum
    return received_checksum == int.from_bytes(calculated_checksum, byteorder='big')



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

      # Header is 8 bytes, 2 bytes for checksum, 2 bytes for length w/ACK and SEQ, data
      packet_length = len(header) + 2 + 2 + len(data)

      ack_bit = ack_num << 14
      seq_bit = seq_num << 15

      packet_info = packet_length | ack_bit | seq_bit

      packet_info_bytes = packet_info.to_bytes(2, byteorder='big')

      packet = header + b'\x00\x00' + packet_info_bytes + data

      checksum = create_checksum(packet)

      packet_with_checksum = packet[:8] + checksum + packet[10:]

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

      


###### These three functions will be automatically tested while grading. ######
###### Hence, your implementation should NOT make any changes to         ######
###### the above function names and args list.                           ######
###### You can have other helper functions if needed.                    ######  
