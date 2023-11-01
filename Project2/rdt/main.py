from sender import Sender

# note: no arguments will be passed in
sender = Sender() 

#Original was 1 to 10
for i in range(1, 3):
    # this is where your rdt_send will be called
    sender.rdt_send('msg' + str(i))