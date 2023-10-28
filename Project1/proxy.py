# Maslin Farrell
# Computer Networks Project 1
from socket import *
from urllib.parse import urlparse
import sys
from pathlib import Path

def createSocket(listeningPort: int):
    """
    Creates the necessary serverSocket used for receiving client requests

    Parameters: 
    listeningPort (int): The port specified by the user for telnet communications
    """
    try:
        # Try to create the server socket for receiving requests from a telnet client
        serverSocket = socket(AF_INET, SOCK_STREAM)
        serverSocket.bind(('0.0.0.0', listeningPort))
        serverSocket.listen(1)
        return serverSocket

    # Permission Errors occur when the user launches the proxy on ports that they are not allowed to use
    except PermissionError:
        print(f"PERMISSION ERROR: You do not have permission to use port {listeningPort}. Please try again with a different port")
        sys.exit(1)

def processClientRequest(serverSocket):
    """
    Processes the received client requests.

    Parameters:
    serverSocket (socket): used for accepting and receiving client requests.

    Returns:
    uri (list): List containing the request from the client split into a list. [0] = request type, [1] = url [2] = http version
    clientSocket (socket): This is the created client socket used for communicating with the telnet client
    """
    
    try:
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
        
        return uri, clientSocket

    # Exiting gracefully letting the user know they pressed Ctrl+c and the server is shutting down
    except KeyboardInterrupt:
        print("\nServer interrupted by user (Ctrl+c). Closing server.")
        serverSocket.close()
        sys.exit(0)

def extractRequestData(uri: str):
    """
    This function extracts all of the necessary params from the clients URI

    Parameters:
    uri (str): this is the clients URI

    Returns:
    requestType (str): The request type which should always be GET
    path (str): The path for the requested file from the URI
    httpVersion (str): The requested HTTP version which will be 1.1 as we only support that.
    host (str): The host we will be requesting
    port (int): The port we will be using for the request, either user specified or default 80
    cachePath (str): The built cache path we will be using for storing files in the cache
    """

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
    
    return requestType, path, httpVersion, host, port, cachePath

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

def handleInvalidRequest(clientSocket):
    """
    Sends error messages back to the client if they made an invalid request.

    Parameters:
    clientSocket (socket): used for sending messages back to telnet client and closing their connection to the proxy. 
    """
    print("Client Request ERROR: Request was not properly formatted. Closing connection")
    clientSocket.sendall("ERROR: Your Request was not properly formatted. Closing Connection\nExample Usage: GET http://zhiju.me/networks/valid.html HTTP/1.1\n".encode("utf-8"))
    clientSocket.close()

def readFromCache(cachePath: str, clientSocket: socket):
    """
    Reads the requested file from the cache and sends it to our client.
    
    Parameters:
    cachePath (str): This is the path for the requested file's location. All cached items are stored under the parent folder '.cache'
    clientSocket (socket): This is the socket object used for communicating with the client.

    """
    print("Serving the requested file from the cache to the client!")

    # We will be storing the cachedResponse to this variable
    cachedResponse = ''

    # Read the contents of the requested file (which is a bytes-like object) 
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

def requestFromOrigin(requestType:str, path: str, httpVersion:str, host:str, port: int, clientSocket: socket):
    """
    Requests the file from the origin server

    Builds out a string used for the requesting the file from the origin server called httpRequest using the passed in params.
    Creates an outbound socket used for making requests to the origin server.

    Parameters:
    requestType (str): this will always be a GET request
    path (): Path of the uri i.e. networks/valid.html
    httpVersion (): Http Version will always be HTTP/1.1
    host (): Host we are going to connect to
    port (): Port we are going to use either user specified or the default 80
    clientSocket(): Socket we are using to communicate with our client

    Returns:
    response (bytes): This is the response we have received from the origin server
    """
    # If we are here that means we don't have the file cached
    print("No Cache Hit! Requesting origin server for the file...")
                    
    # We will store our request here, consisting of the request type, path, http version, host, and finally close connection headers
    httpRequest = f"{requestType} {path} {httpVersion}\nHost: {host}:{port}\nConnection: close\n\n"

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
    
    # Return the received response
    return response

def handleOriginResponse(clientSocket: socket, response: bytes, cachePath: str):
    """
    handles the response from the origin server. 
    If the status code is 200 we have a successful response and will write the requested file to our cache.
    If the status code is 404 we send a message back to the client and close their connection.
    If the status code is an unsupported error then we tell the client and close their connection.

    Parameters:
    clientSocket (socket): used for sending messages back to the client
    response (bytes): Response from the origin server
    cachePath (str): This is the location we will be writing our files to. 
    """

    # Decode the response output from a bytes-like object into a string data type
    responseDecoded = response.decode("utf-8")

    # Extract the headers and body
    headers, body = responseDecoded.split('\r\n\r\n', 1)
    statusLine = headers.split('\n')[0]
    statusCode = statusLine.split(' ')[1]

    # Process the response correctly depending on the status codes
    if statusCode == "200":
        handleSuccessfulResponse(clientSocket, statusLine, body, cachePath)
    elif statusCode == "404":
        handleNotFoundResponse(clientSocket, statusLine)
    else:
        handleUnsupportedResponse(clientSocket, statusLine)

def handleSuccessfulResponse(clientSocket: socket, statusLine: str, body: str, cachePath: str):
    """
    If the status code was 200 then we store the requested file to our cache and server the request to the client.

    Parameters:
    clientSocket (str): Client socket used for sending messages back to the client.
    statusLine (str): Status line contains the HTTP status of the request.
    body (str): This is the body of the requested file as a string.
    cachePath (str): This is the directory where we will be storing the requested file. 
    """

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
    
    print("All done! Closing socket...")

def handleNotFoundResponse(clientSocket, statusLine):
    """
    If the status code was 404 then we let the client know and close the connection.

    Parameters:
    clientSocket (str): Client socket used for sending messages back to the client.
    statusLine (str): Status line contains the HTTP status of the request.
    """

    print("Response Received from server, but status code is not 200! No cache writing...")
    print("Now responding to client...")

    # Send the status line from the headers
    clientSocket.sendall(f"{statusLine}\n".encode("utf-8"))
    # Send the Cache-Hit message
    clientSocket.sendall(f"Cache-Hit: 0\n".encode("utf-8"))
    # Send the response to the client 404 NOT FOUND
    clientSocket.sendall("\n404 NOT FOUND\n\n".encode("utf-8"))
    
    print("All done! Closing socket...")

def handleUnsupportedResponse(clientSocket, statusLine):
    """
    If the status code was something other than 200 or 404 then we have an unexpected error let the client know and close the connection.

    Parameters:
    clientSocket (str): Client socket used for sending messages back to the client.
    statusLine (str): Status line contains the HTTP status of the request.
    """

    print("Response Received from server, but status code is not 200! No cache writing...")
    
    print("Now responding to client...")
    
    # Send the status line from the headers
    clientSocket.sendall(f"{statusLine}\n".encode("utf-8"))
    
    # Send the Cache-Hit message
    clientSocket.sendall(f"Cache-Hit: 0\n".encode("utf-8"))

    # Send the unsupported error message
    clientSocket.sendall(f"\nUnsupported Error\n\n".encode("utf-8"))
    
    print("All done! Closing socket...")

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
    serverSocket = createSocket(listeningPort)
    
    # Infinite loop for our server to continue running
    while True:
        # Get the URI and the created clientSocket
        uri, clientSocket = processClientRequest(serverSocket)
        
        # If the URI is valid then extract the request data
        if validURI(uri, clientSocket):
            requestType, path, httpVersion, host, port, cachePath = extractRequestData(uri)
            
            # Check if the cache path exists
            if cachePath.exists():
                # If we are here that means we have the file and we will serve it to the client without contacting the origin
                readFromCache(cachePath, clientSocket)

                clientSocket.close()
            else:
                # Request the file from the origin server as we do not have it stored in our cache
                response = requestFromOrigin(requestType, path, httpVersion, host, port, clientSocket)

                # Handle response from the origin server
                handleOriginResponse(clientSocket, response, cachePath)
                clientSocket.close()
        # If the URI is not valid handle the invalid request
        else:
            handleInvalidRequest(clientSocket)


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