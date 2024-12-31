class TreeVersioningError(Exception):
    """Base exception for tree versioning system."""
    pass

class CycleError(TreeVersioningError):
    """Raised when an operation would create a cycle in the tree."""
    pass

class TagNotFoundError(TreeVersioningError):
    """Raised when a requested tag doesn't exist."""
    pass

class NodeNotFoundError(TreeVersioningError):
    """Raised when a requested node doesn't exist."""
    pass