import unittest
from Proxy import Proxy  # Import the Proxy class from Proxy.py

class TestProxy(unittest.TestCase):
    def test_create_socket(self):
        # Instantiate the Proxy class
        proxy = Proxy()
        # Call the createSocket method from the Proxy class
        result = proxy.createSocket(1532)
        # Perform your assertions or checks here
        self.assertIsNotNone(result)  # Example assertion, replace with your own test cases

if __name__ == '__main__':
    unittest.main()
