from settings import SIZE

# Helper function to determine if a key falls within a range
def inrange(c, a, b):
	# is c in [a,b)?, if a == b then it assumes a full circle
	# on the DHT, so it returns True.
	a = a % SIZE
	b = b % SIZE
	c = c % SIZE
	if a < b:
		return a <= c and c < b
	return a <= c or c < b

class Address(object):
    def __init__(self, ip, port):
        self.ip = ip
        self.port = int(port)

    def __hash__(self):
        # Hash value within DHT ring size
        return hash(f"{self.ip}:{self.port}") % SIZE

    # Needed for set() and sorted()
    def __eq__(self, other):
        if not isinstance(other, Address):
            return False
        return (self.ip, self.port) == (other.ip, other.port)

    def __lt__(self, other):
        # Defines < operator so sorted() works
        if not isinstance(other, Address):
            return NotImplemented
        return (self.ip, self.port) < (other.ip, other.port)

    def __str__(self):
        return f'["{self.ip}", {self.port}]'

