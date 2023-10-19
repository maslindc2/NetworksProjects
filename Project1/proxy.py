# Maslin Farrell
# Computer Networks Project 1
from socket import *
from urllib.parse import urlparse
import sys
from pathlib import Path

def server(listeningPort: int):
    """
    Handles all of the proxy server logic.
    The function creates two sockets: serverSocket and outboundSocket.
    - serverSocket: Processes requests from the telnet client and sends responses back. 
      It uses the user specified 'listeningPort' for listening to requests from the client.
    - Fetches information from the requested server (origin server). 
      It uses a predefined port based on my student ID.

    Parameters:
    listeningPort (int): The port specified by the user for telnet communications
    """
    
    try:
        # Try to create the server socket for receiving requests from a telnet client
        serverSocket = socket(AF_INET, SOCK_STREAM)
    
        serverSocket.bind(('0.0.0.0', listeningPort))
        serverSocket.listen(1)

        print("Listening on port:", listeningPort)
    # Permission Errors occur when the user launches the proxy on ports that they are not allowed to use
    except PermissionError:
        print(f"PERMISSION ERROR: You do not have permission to use port {listeningPort}. Please try again with a different port")
        sys.exit(1)

    # This is in a try catch to handle ctrl+c exits.
    try:
        while True:
            print("*********** Ready To Serve.... ***********")

            # Accept the incoming connection and output the clientSocket (used for processing requests from the client) and the address
            clientSocket, addr = serverSocket.accept()

            # Print the clients IP address
            print("Received a client connection from: ", addr)
            
            # Accept 2KB packet size and decode it as utf-8
            data = clientSocket.recv(2000).decode("utf-8")
            
            # Print the message received from the client
            print("Received a message from this client: " + data)
            
            # Split the data into a list called URI
            # Such that index 0 = GET, index 1 = URL, index 2 = HTTP Version
            uri = data.split()
            
            # Check if the request is valid by calling validURI with the uri list and clientSocket (so we can send messages back if the URI is wrong)
            if(validURI(uri, clientSocket)):                
                # Parse the url into a var called parsedURL
                parsedURL = urlparse(uri[1])
                
                # Set the request type
                requestType = uri[0]
                
                # Set the path
                path = parsedURL.path
                
                # Set the http version
                httpVersion = uri[2]
                
                # Set the hostname
                host = parsedURL.hostname
                
                # Set the port If one is provided use that one if not we use the default port 80
                port = parsedURL.port if parsedURL.port is not None else 80

                # Store the file we will be working from. 
                # if we requested zhiju.me/networks/valid.html
                # we will have the path .cache/zhiju.me/networks/valid.html
                cachePath = ".cache" / Path(parsedURL.netloc) / Path(parsedURL.path.strip('/'))

                if cachePath.exists():
                    # If we are here that means we have the file and we will serve it to the client without contacting the origin
                    print("Serving the requested file from the cache to the client!")
                    
                    # We will be storing the cachedResponse to this variable
                    cachedResponse = ''
                    
                    # Read the contents of 'valid.html' (which is a bytes-like object) 
                    # we will decode it and store it to the cachedResponse variable
                    with open(cachePath, 'rb') as file:
                        cachedResponse = file.read().decode("utf-8")

                    # Since we will only save the requested file to the cache when the request is 200 
                    # it is safe to hardcode the HTTP status message
                    clientSocket.sendall("HTTP/1.1 200 OK\n".encode("utf-8"))
                    
                    # Send the Cache-Hit status, since we are pulling from the cache, the cache hit is 1
                    clientSocket.sendall(f"Cache-Hit: 1\n".encode("utf-8"))
                    
                    # Send the body content to our client
                    clientSocket.sendall(f"\n\n{cachedResponse}\n\n".encode("utf-8"))
                    
                    print("All done! Closing socket...\n")
                    
                    # Close the client socket
                    clientSocket.close()
                else:
                    # If we are here that means we don't have the file cached
                    print("No Cache Hit! Requesting origin server for the file...")
                    
                    # We will store our request here, consisting of the request type, path, http version, host, and finally close connection headers
                    httpRequest = f"{requestType} {path} {httpVersion}\nHost: {host}\nConnection: close\n\n"
                    
                    # Print the http request we will be sending to the origin server
                    print("Sending the following msg from proxy to server: " + requestType + " " + path + " " + httpVersion)
                    
                    # Print the host we are going to be connecting to
                    print("Host: " + host)
                    
                    # Creating another socket to handle the outbound requests as our current socket is being used for talking with our client
                    outboundSocket = socket(AF_INET, SOCK_STREAM)
                    
                    # Bind the outboundSocket to a specific outbound port
                    assignedOutboundPort = 10500 + (4202012) % 100

                    # Bind the outbound socket to localhost on the port we calculated using the above formula
                    outboundSocket.bind(('0.0.0.0', assignedOutboundPort))
                    
                    # Connect to the requested host using either the specified or default port (see line 50 for where this is set)
                    outboundSocket.connect((host, port))
                    
                    # Send the http request to the origin server
                    outboundSocket.sendall(httpRequest.encode("utf-8"))
                    
                    # Receive the response from the server we sent the request to
                    response = outboundSocket.recv(2000)                  

                    # If we didn't receive anything then we need to abort and tell the client we received nothing from the origin server
                    if not response:
                        print("ERROR: Did not receive any data from the requested server.")
                        
                        # Tell the client we received nothing from the origin server
                        clientSocket.sendall("ERROR: The requested server did not send any data back\n".encode("utf-8"))
                        clientSocket.sendall("Please check that the URL you requested is correct.\n".encode("utf-8"))
                        
                        # Close the outbound socket
                        outboundSocket.close()
                        
                        # Disconnect the client
                        clientSocket.close()
                                        
                    # We will always close connection after the request as it's in our http request
                    # Since we got back the requested data, the origin server then closes the connection we established
                    print("Connection: close\n")
                    
                    # Since we are done making requests to the origin server, we can close the socket we used
                    outboundSocket.close()
                    
                    # Decode the response output from a bytes-like object into a string datatype
                    responseOutput = response.decode("utf-8")

                    # Here we are extracting the headers and the body such that the headers are stored in one variable and the body is stored in the other
                    # Using \n and \r here to ensure that we get the line break between headers and body
                    headers, body = responseOutput.split('\r\n\r\n', 1)
                    
                    # Split the headers string so we can extract the status line containing the version and the status code
                    statusLine = headers.split('\n')[0]

                    # Extract the status code
                    statusCode = statusLine.split(' ')[1]
                    
                    # If we got the status code 200
                    if statusCode == "200":
                        print("Response Received from server, and status code is 200!\nWriting to cache...")
                        
                        # Since the directory doesn't exist make it
                        # Creates the requested directories, if the requested directories already exist its okay so we don't get an error if it does
                        cachePath.parent.mkdir(parents=True, exist_ok=True)
                        
                        # Since we had to decode the body to originally extract it from the response, we now re-encode the body for storing it to our cache
                        # This will save the body as a bytes-like object
                        encodedBody = body.encode("utf-8")

                        # Write the body of the response to our cache file
                        # If we are serving a cache there is no point in storing the headers in our cache
                        with open(cachePath, 'wb') as file:
                            file.write(encodedBody)
                        
                        print("Wrote file to cache")
                        print("Now responding to client...")
                        
                        # Send the status line from the headers
                        clientSocket.sendall(f"{statusLine}\n".encode("utf-8"))
                        
                        # Send the Cache-Hit message
                        clientSocket.sendall(f"Cache-Hit: 0\n".encode("utf-8"))
                        
                        # Send the body we decoded from our response back to the client
                        clientSocket.sendall(f"\n\n{body}\n\n".encode("utf-8"))
                        
                        # Print that we are closing the socket
                        # NOTE: This will be done outside of our conditional statements as we will always close the clientSocket and outbound
                        # no matter the status code we got. 
                        print("All done! Closing socket...\n")
                    elif statusCode == "404":
                        print("Response Received from server, but status code is not 200! No cache writing...")
                        
                        print("Now responding to client...")
                        
                        # Send the status line from the headers
                        clientSocket.sendall(f"{statusLine}\n".encode("utf-8"))
                        
                        # Send the Cache-Hit message
                        clientSocket.sendall(f"Cache-Hit: 0\n".encode("utf-8"))
                        
                        # Send the response to the client 404 NOT FOUND
                        clientSocket.sendall("\n404 NOT FOUND\n\n".encode("utf-8"))
                        
                        print("All done! Closing socket...\n")
                    else:
                        print("Response Received from server, but status code is not 200! No cache writing...")
                        
                        print("Now responding to client...")
                        
                        # Send the status line from the headers
                        clientSocket.sendall(f"{statusLine}\n".encode("utf-8"))
                        
                        # Send the Cache-Hit message
                        clientSocket.sendall(f"Cache-Hit: 0\n".encode("utf-8"))
                        
                        # Send the unsupported error message
                        clientSocket.sendall(f"\nUnsupported Error\n\n".encode("utf-8"))
                        
                        print("All done! Closing socket...")
                    
                    # Close out the client socket we used
                    clientSocket.close()
            else:
                print("Client Request ERROR: Request was not properly formatted. Closing connection")
                
                # If the request was not formatted correctly send to the client that it was
                clientSocket.sendall("ERROR: Your Request was not properly formatted. Closing Connection\nExample Usage: GET http://zhiju.me/networks/valid.html HTTP/1.1\n".encode("utf-8"))
                
                # Close the client connection
                clientSocket.close()
    
    # Exiting gracefully letting the user know they pressed Ctrl+c and the server is closing down now
    except KeyboardInterrupt:
        print("\nServer interrupted by user (Ctrl+c). Closing server.")
        serverSocket.close()
        sys.exit(0)


def validURI(uri: list, clientSocket: socket) -> bool:
    """
    Validates the user submitted URI for the proxy server
    
    Performs the following checks:
    - Ensures the URI consists of exactly 3 parameters: GET <requested url> HTTP/1.1
    - Checks if the first parameter is a GET request. Only GET requests can be made.
    - Checks if the second parameter starts with 'http://' as only http requests can be made. HTTPS is NOT supported.
    - Checks if the HTTP version is 1.1 as only HTTP/1.1 is supported.

    Parameters:
    uri (list): The request components from the telnet client.
    clientSocket (socket): The clientSocket object used for sending error messages to the telnet client.

    Returns:
    bool: True if the user's URI is valid; False otherwise.
    """

    # Make sure the uri list contains three elements if it doesn't let the user know and return false
    if (len(uri) != 3):
        clientSocket.sendall("ERROR: Your request must contain the following: GET <URL> <HTTP/1.1>\n".encode("utf-8"))
        return False
    
    # Check if the first index is a GET request if it isn't let the user know and return false
    elif(uri[0] != "GET"):
        clientSocket.sendall("ERROR: This server only accepts the method GET\n".encode("utf-8"))
        return False
    
    # Check if the requested url starts with http:// if it doesn't let them know and exit
    elif(not uri[1].startswith("http://")):
        clientSocket.sendall("ERROR: Your URL must start with http://\n".encode("utf-8"))
        clientSocket.sendall("Only HTTP requests are supported!\n".encode("utf-8"))
        return False
    
    # Check if the HTTP version is 1.1 if it isn't let the user know and return false
    elif(uri[2] != "HTTP/1.1"):
        clientSocket.sendall("ERROR: Your HTTP Version must be HTTP/1.1\n".encode("utf-8"))
        return False
    
    # Otherwise we have a valid URI so return true
    else:
        return True

if __name__ == "__main__":
    # Check if the length of issued commands are correct
    if len(sys.argv) != 2:
        print("ERROR: Not enough parameters supplied")
        print("Example Usage: python3 proxy.py <listening port number>")
        sys.exit(1)

    # Get the user-supplied listening port
    listeningPort = sys.argv[1]

    # Check if the supplied listening port is an integer
    try:
        # Try to cast the listening port to an int to double check the user specified an int for the port
        listeningPort = int(listeningPort)
        
        # If we were able to cast the requested listening port to an int start the server
        server(listeningPort)

    # The user didn't use an integer for the server's listening port
    except ValueError:
        # If the user did not supply an int as a listening port, let them know they made a mistake
        print("The listening port command must be an integer")
        print("Example usage: python3 proxy.py 1530")
        sys.exit(1)