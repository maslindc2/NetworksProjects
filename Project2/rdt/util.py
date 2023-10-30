def create_checksum(packet_wo_checksum):
    """create the checksum of the packet (MUST-HAVE DO-NOT-CHANGE)

    Args:
      packet_wo_checksum: the packet byte data (including headers except for checksum field)

    Returns:
      the checksum in bytes

    """
    # Calculate the checksum for the packet
    checksum = 0
    for i in range(0, len(packet_wo_checksum), 2):
        if i + 1 < len(packet_wo_checksum):
            checksum += (packet_wo_checksum[i] + (packet_wo_checksum[i + 1] << 8))
        else:
            checksum += packet_wo_checksum[i]
    checksum = (checksum & 0xffff)
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
  # Ensure data_str is no longer than 1000 bytes
  if len(data_str) > 1000:
    raise ValueError("Data string too long")

  # Create the initial 10-byte header (8 bytes for "COMPNETW" and 2 bytes for reserved checksum)
  header = b"COMPNETW"
  
  # Here we reserve 16 bits for the checksum
  header += b"\x00\x00"

  # Get the packet length of header and data, we shift ack_num 14 bits so the ack will be stored at the 15th bit, seq_num is shifted 15 bits to the left
  # so we can store the sequence number at the 16th bit position. 
  packetLength = (len(header) + len(data_str)) | (ack_num << 14) | (seq_num << 15)

  # Convert the packet length to bytes. 
  packetLengthBytes = packetLength.to_bytes(2, byteorder='big')

  # Combine header, packetLength and data together
  packet = header + packetLengthBytes + data_str.encode()
  
  # Send the packet that does not has an empty reserved spot for the checksum over to create_checksum
  checksum = create_checksum(packet)
  
  # Now we insert the checksum into that reserved space and we get our completed packet
  packet = packet[:8] + checksum + packet[10:]
  print(packet)

  # return the complete udp packet
  return packet



###### These three functions will be automatically tested while grading. ######
###### Hence, your implementation should NOT make any changes to         ######
###### the above function names and args list.                           ######
###### You can have other helper functions if needed.                    ######  
