
# Usage Examples

## Basic Usage

### Creating a Configuration Tree
```python
from tree_versioning.models import Tree
from tree_versioning.database import db

with db.get_session() as session:
    # Create tree
    tree = Tree(name="config_tree")
    session.add(tree)
    
    # Add configuration
    root = tree.add_node(
        data={"type": "database", "host": "localhost"},
        session=session
    )
    
    # Tag version
    tree.create_tag("v1.0", "Initial version", session=session)
    session.commit()
```

### Version Management
```python
# Create new version
new_version = tree.create_new_tree_version_from_tag("v1.0", session=session)

# Add changes
new_config = new_version.add_node(
    data={"type": "cache", "host": "redis"},
    session=session
)

# Tag new version
new_version.create_tag("v1.1", "Added cache", session=session)
```

### Traversal Operations
```python
# Get configuration state
state = tree.get_state_at_tag("v1.0", session=session)

# Find paths
path = tree.find_path(node1.id, node2.id, session=session)
```
