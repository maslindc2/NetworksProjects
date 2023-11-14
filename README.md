# CPSC 5510 Networking Projects
## What is this repository?
This is a small collection of the projects I have made for Seattle U's CPSC 5510 Networking Course.  Project 1 is a simple HTTP proxy/cache and Project 2 is an RDT3.0 Implementation in python.

### Project 1  
This simply HTTP cache is designed to accept requests from a telnet client.  The program will check the cache first to see if it has the requested file, if it doesn't it will contact the origin server (provided in the client's request), save the file to the cache and then serve it to the client.  If the program has the request already stored it will read the saved file from the cache and serve the contents to the client without involving the origin server. 

An important note, this version is a bit more complicated as I have added asynchronous support to the original project. The original project was designed for only one client connection, this setup now can support multiple clients reading and writing to the cache directory.  If you want to see the original state checkout [this commit](https://github.com/maslindc2/NetworksProjects/tree/5380647170206176a99b21fd290220be901d9058)
#### That's neat, how do I run it?
1. Clone the repository, open the folder "Project1", and launch a terminal window here.
2. Assuming you have python3 installed and aiofiles installed, start the proxy using "python3 ProxyRunner.py <port number>" where "<port number>" is the port you want the proxy to run on.
3. In a new terminal window run the telnet command "telnet 127.0.0.1 <port number>" where "<port number>" is the port you used to start your proxy.
4. Send a request to an HTTP webpage (Note: HTTPS is not supported), as a demo use my professor's website by entering the command "GET http://zhiju.me/networks/valid.html HTTP/1.1" into your telnet window.
5. The proxy will work it's magic and you will see the page content printed to your telnet client. That's it!

## Project 2
This is a simple implementation of RDT3.0.  The main goal of this project is to reliably send a message from sender.py to receiver.py.  This is done with the utility class util.py. Below is a breakdown of what each class does

### Util.py
This is used for creating UDP packets or in this case a modified UDP packet where in place of the source and destination address is an 8 byte header "COMPNETW", source and destination is handled using the Socket class that comes with python. This is all done in the make_packet function. The packet length is simply handled by the function create_packet_length_section.  Lastly all good UDP packets need a checksum, this is done using the checksum function where we first build out a pseudo UDP packet with no checksum.  We generate it using the standard internet checksum algorithm, once we have the checksum we reassemble it into the packet. 

### Sender.py
This is used to send messages to the receiver as launched using main.py.  Ideally this class is launched after the receiver is running, but it will handle re-transmissions if it doesn't receive a response.  This class implements the necessary components in the RDT3.0 Sender FSM diagram. 

### Receiver.py
This class is used to receive messages from the sender. This program also implements the necessary components of the RDT3.0 Receiver FSM diagram.
