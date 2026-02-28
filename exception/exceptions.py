# exception/exceptions.py

class KmeansError(Exception):
    """Raised when Kmeans fails."""
    pass    

class A2ARouterError(Exception):
    """Raised when an A2A Router message is not supported."""
    pass    