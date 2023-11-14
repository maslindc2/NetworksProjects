# Maslin Farrell
# Computer Networks Project 1
import asyncio

import logging
import sys
import aiofiles

from socket import *
from urllib.parse import urlparse
from pathlib import Path


class Proxy:
    async def processClientRequest(self, reader):
        """
        Processes the received client requests.

        Parameters:
        serverSocket (socket): used for accepting and receiving client requests.

        Returns:
        uri (list): List containing the request from the client split into a list. [0] = request type, [1] = url [2] = http version
        clientSocket (socket): This is the created client socket used for communicating with the telnet client
        """
        
        try:
            # Accept 2KB packet size and decode it as utf-8
            data = await reader.read(2000)
            data = data.decode("utf-8")

            # Print the message received from the client
            print("Received a message from this client: " + data)

            # Split the data into a list called URI
            # Such that index 0 = GET, index 1 = URL, index 2 = HTTP Version
            uri = data.split()
            
            return uri
        # Exiting gracefully letting the user know they pressed Ctrl+c and the server is shutting down
        except KeyboardInterrupt:
            print("\nServer interrupted by user (Ctrl+c). Closing server.")
            reader.close()
            sys.exit(0)

    async def extractRequestData(self, uri: str):
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

    async def validURI(self, uri: list, writer: asyncio.StreamWriter) -> bool:
        """
        Validates the user-submitted URI for the proxy server.

        Performs the following checks:
        - Ensures the URI consists of exactly 3 parameters: GET <requested url> HTTP/1.1
        - Checks if the first parameter is a GET request. Only GET requests can be made.
        - Checks if the second parameter starts with 'http://' as only HTTP requests can be made. HTTPS is NOT supported.
        - Checks if the HTTP version is 1.1 as only HTTP/1.1 is supported.

        Parameters:
        uri (list): The request components from the telnet client.
        writer (StreamWriter): The StreamWriter object used for sending error messages to the telnet client.

        Returns:
        bool: True if the user's URI is valid; False otherwise.
        """

        # Make sure the uri list contains three elements if it doesn't let the user know and return false
        if len(uri) != 3:
            await writer.drain()
            writer.write("ERROR: Your request must contain the following: GET <URL> <HTTP/1.1>\n".encode("utf-8"))
            return False

        # Check if the first index is a GET request if it isn't let the user know and return false
        elif uri[0] != "GET":
            await writer.drain()
            writer.write("ERROR: This server only accepts the method GET\n".encode("utf-8"))
            return False

        # Check if the requested URL starts with http:// if it doesn't let them know and exit
        elif not uri[1].startswith("http://"):
            await writer.drain()
            writer.write("ERROR: Your URL must start with http://\n".encode("utf-8"))
            writer.write("Only HTTP requests are supported!\n".encode("utf-8"))
            return False

        # Check if the HTTP version is 1.1 if it isn't let the user know and return false
        elif uri[2] != "HTTP/1.1":
            await writer.drain()
            writer.write("ERROR: Your HTTP Version must be HTTP/1.1\n".encode("utf-8"))
            return False

        # Otherwise, we have a valid URI so return true
        else:
            return True

    async def handleInvalidRequest(self, writer):
        """
        Sends error messages back to the client if they made an invalid request.

        Parameters:
        clientSocket (socket): used for sending messages back to telnet client and closing their connection to the proxy. 
        """
        writer.write("ERROR: Your Request was not properly formatted. Closing Connection\nExample Usage: GET http://zhiju.me/networks/valid.html HTTP/1.1\n".encode("utf-8"))
        writer.close()

    async def readFromCache(self, cachePath: str, writer: asyncio.StreamWriter):
        """
        Reads the requested file from the cache and sends it to our client.
        
        Parameters:
        cachePath (str): This is the path for the requested file's location. All cached items are stored under the parent folder '.cache'
        clientSocket (socket): This is the socket object used for communicating with the client.

        """
        try:
            print("Serving the requested file from the cache to the client!")

            # We will be storing the cachedResponse to this variable
            cachedResponse = b''

            # Read the contents of the requested file (which is a bytes-like object) 
            # we will decode it and store it to the cachedResponse variable
            async with aiofiles.open(cachePath, 'rb') as file:
                cachedResponse = await file.read()
        
            # This done to strip the byte-like b'' format from python
            cachedResponse = cachedResponse.decode('utf-8')    

            # Since we will only save the requested file to the cache when the request is 200 
            # it is safe to hardcode the HTTP status message
            writer.write("HTTP/1.1 200 OK\n".encode("utf-8"))
            await writer.drain()
            # Send the Cache-Hit status, since we are pulling from the cache, the cache hit is 1
            writer.write(f"Cache-Hit: 1\n".encode("utf-8"))
            await writer.drain()
            # Send the body content to our client
            writer.write(f"\n\n{cachedResponse}\n\n".encode("utf-8"))
            await writer.drain()

        except Exception as e:
            logging.error(f"ERROR: Failed to read from cache! Dropping connection. {e}")
            writer.close()
            await writer.wait_closed()

    async def requestFromOrigin(self, requestType: str, path: str, httpVersion: str, host: str, port: int):
        try:
            # Make a request to the origin server
            reader, writer = await asyncio.open_connection(host, 80)

            # Build the request to the origin server
            httpRequest = f"{requestType} {path} {httpVersion}\nHost: {host}:{port}\nConnection: close\n\n"
            
            # Send the request
            writer.write(httpRequest.encode('utf-8'))
            await writer.drain()

            # Receive the response
            origin_response = await reader.read(4096)
            return origin_response

        except Exception as e:
            return f"An error occurred during the request to the origin server: {e}"

        finally:
            # Close the writer to indicate that we're done
            writer.close()
            await writer.wait_closed()

    async def handleOriginResponse(self, writer: asyncio.StreamWriter, response: bytes, cachePath: str):
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
            await self.handleSuccessfulResponse(writer, statusLine, body, cachePath)
        elif statusCode == "404":
            await self.handleNotFoundResponse(writer, statusLine)
        else:
            await self.handleUnsupportedResponse(writer, statusLine)

    async def handleSuccessfulResponse(self, writer: asyncio.StreamWriter, statusLine: str, body: str, cachePath: str):
        """
        If the status code was 200 then we store the requested file to our cache and serve the request to the client.

        Parameters:
        writer (StreamWriter): StreamWriter object used for sending messages back to the client.
        statusLine (str): Status line contains the HTTP status of the request.
        body (str): This is the body of the requested file as a string.
        cachePath (str): This is the directory where we will be storing the requested file.
        """

        print("Response Received from server, and status code is 200!\nWriting to cache...")

        # Since the directory doesn't exist make it
        try:
            # Creates the requested directories, if the requested directories already exist its okay so we don't get an error if it does
            await asyncio.to_thread(cachePath.parent.mkdir, parents=True, exist_ok=True)

            # Since we had to decode the body to originally extract it from the response, we now re-encode the body for storing it to our cache
            # This will save the body as a bytes-like object
            encodedBody = body.encode("utf-8")

            # Write the body of the response to our cache file
            # If we are serving a cache there is no point in storing the headers in our cache
            async with aiofiles.open(cachePath, 'wb') as file:
                await file.write(encodedBody)

        except FileNotFoundError as e:
            logging.error(f"ERROR: The cache path does not exist! {e}")
        except Exception as e:
            logging.error(f"ERROR: An unexpected error has occurred while writing to the cache! {e}")
        
        # Send the status line from the headers
        writer.write(f"{statusLine}\n".encode("utf-8"))
        await writer.drain()

        # Send the Cache-Hit message
        writer.write(f"Cache-Hit: 0\n".encode("utf-8"))
        await writer.drain()
        # Send the body we decoded from our response back to the client
        writer.write(f"\n\n{body}\n\n".encode("utf-8"))
        await writer.drain()

    async def handleNotFoundResponse(self, writer:asyncio.StreamWriter, statusLine: str):
        """
        If the status code was 404 then we let the client know and close the connection.

        Parameters:
        clientSocket (str): Client socket used for sending messages back to the client.
        statusLine (str): Status line contains the HTTP status of the request.
        """

        # Send the status line from the headers
        writer.write(f"{statusLine}\n".encode("utf-8"))
        await writer.drain()
        
        # Send the Cache-Hit message
        writer.write(f"Cache-Hit: 0\n".encode("utf-8"))
        await writer.drain()

        # Send the response to the client 404 NOT FOUND
        writer.write("\n404 NOT FOUND\n\n".encode("utf-8"))
        await writer.drain()

    async def handleUnsupportedResponse(self, writer:asyncio.StreamWriter, statusLine):
        """
        If the status code was something other than 200 or 404 then we have an unexpected error let the client know and close the connection.

        Parameters:
        clientSocket (str): Client socket used for sending messages back to the client.
        statusLine (str): Status line contains the HTTP status of the request.
        """
        
        # Send the status line from the headers
        writer.write(f"{statusLine}\n".encode("utf-8"))
        await writer.drain()
        
        # Send the Cache-Hit message
        writer.write(f"Cache-Hit: 0\n".encode("utf-8"))
        await writer.drain()
        
        # Send the unsupported error message
        writer.write(f"\nUnsupported Error\n\n".encode("utf-8"))
        await writer.drain()
    
    async def handleClient(self, reader, writer):
        """
        Handles the incoming client request.

        Parameters:
        reader (StreamReader): StreamReader object for reading from the client.
        writer (StreamWriter): StreamWriter object for writing to the client.
        """
        try:
            # Get the URI
            uri = await self.processClientRequest(reader)

            isValid = await self.validURI(uri, writer)
            
            # If the URI is valid then extract the request data
            if isValid:
                requestType, path, httpVersion, host, port, cachePath = await self.extractRequestData(uri)
                    
                # Check if the cache path exists
                if cachePath.exists():
                    # If we are here that means we have the file and we will serve it to the client without contacting the origin
                    await self.readFromCache(cachePath, writer)
                else:
                    # Request the file from the origin server as we do not have it stored in our cache
                    response = await self.requestFromOrigin(requestType, path, httpVersion, host, port)
                    
                    # Handle response from the origin server
                    await self.handleOriginResponse(writer, response, cachePath)
            # If the URI is not valid handle the invalid request
            else:
                await self.handleInvalidRequest(writer)
        finally:
            writer.close()
    
    async def server(self, listeningPort: int):
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
        serverSocket = await asyncio.start_server(self.handleClient, '0.0.0.0', listeningPort)

        async with serverSocket:
            await serverSocket.serve_forever()