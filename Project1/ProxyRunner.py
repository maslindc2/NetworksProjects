import sys
import asyncio
from Proxy import Proxy

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
        proxy = Proxy()
        asyncio.run(proxy.server(listeningPort))

    # The user didn't use an integer for the server's listening port
    except ValueError:
        # If the user did not supply an int as a listening port, let them know they made a mistake
        print("The listening port command must be an integer")
        print("Example usage: python3 proxy.py 1530")
        sys.exit(1)