# Tree Versioning System Examples

## Table of Contents
1. Basic Usage
2. Configuration Management
3. Feature Branching
4. Rollback Scenarios
5. Tree Traversal
6. Advanced Operations

## 1. Basic Usage
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

2. Configuration Management

```python
with db.get_session() as session:
    # Get existing tree
    tree = session.query(Tree).filter_by(name="config_tree").first()
    
    # Create new version from tag
    new_version = tree.create_new_tree_version_from_tag("v1.0", session=session)
    
    # Add new configuration
    db_config = new_version.add_node(
        data={
            "type": "database",
            "host": "db.example.com",
            "port": 5432,
            "user": "admin"
        },
        session=session
    )
    
    cache_config = new_version.add_node(
        data={
            "type": "cache",
            "host": "redis.example.com",
            "port": 6379
        },
        session=session
    )
    
    # Link configurations
    new_version.add_edge(
        db_config.id,
        cache_config.id,
        data={"relation": "uses"},
        session=session
    )
    
    # Tag new version
    new_version.create_tag("v1.1", "Added cache layer", session=session)
    session.commit()
```

3. Feature Branching
```python
with db.get_session() as session:
    # Create feature branch from main
    main_tree = Tree.get_by_tag("main-v1.0", session=session)
    feature_branch = main_tree.create_new_tree_version_from_tag("main-v1.0", session=session)
    
    # Add feature configuration
    feature_flag = feature_branch.add_node(
        data={
            "feature": "new_ui",
            "enabled": True,
            "rollout": 50
        },
        session=session
    )
    
    ui_config = feature_branch.add_node(
        data={
            "theme": "dark",
            "animations": True
        },
        session=session
    )
    
    # Connect configurations
    feature_branch.add_edge(
        feature_flag.id,
        ui_config.id,
        data={"controls": True},
        session=session
    )
    
    # Tag feature version
    feature_branch.create_tag(
        "feature-ui-v1",
        "New UI feature configuration",
        session=session
    )
    session.commit()
```

4. Rollback Scenarios
```python
with db.get_session() as session:
    # Mark current state as stable
    tree = session.query(Tree).filter_by(name="production").first()
    tree.create_tag("stable-v1", "Known good state", session=session)
    
    # Make risky changes
    new_config = tree.add_node(
        data={"experimental": True, "unsafe": "value"},
        session=session
    )
    
    # Problems detected - rollback
    rollback_tree = tree.restore_from_tag("stable-v1", session=session)
    rollback_tree.create_tag("recovery-v1", "Restored from stable", session=session)
    session.commit()
```
5. Tree Traversal
```python
with db.get_session() as session:
    tree = session.query(Tree).first()
    
    # Get root nodes
    roots = tree.get_root_nodes(session=session)
    
    # Get nodes at specific depth
    level_2_nodes = tree.get_nodes_at_depth(2, session=session)
    
    # Find path between nodes
    path = tree.find_path(node1.id, node2.id, session=session)
    for node, edge in path:
        print(f"Node: {node.data}")
        if edge:
            print(f"Connected by: {edge.data}")
    
    # Get state at specific tag
    state = tree.get_state_at_tag("v1.0", session=session)
    print(f"Nodes at v1.0: {len(state['nodes'])}")
    print(f"Edges at v1.0: {len(state['edges'])}")
```

6. Advanced Operations
```python
with db.get_session() as session:
    # Compare versions
    v1_state = tree.get_state_at_tag("v1.0", session=session)
    v2_state = tree.get_state_at_tag("v2.0", session=session)
    
    # Get all children of a node
    children = tree.get_child_nodes(node_id, session=session)
    
    # Get all parents of a node
    parents = tree.get_parent_nodes(node_id, session=session)
    
    # Get connected edges
    edges = tree.get_node_edges(node_id, session=session)
    
    # Complex traversal
    def traverse_tree(node_id, level=0):
        node = tree.get_node(node_id, session=session)
        print(f"{'  ' * level}Node {node_id}: {node.data}")
        
        edges = tree.get_node_edges(node_id, session=session)
        for edge in edges:
            if edge.incoming_node_id == node_id:
                print(f"{'  ' * level}├── Edge: {edge.data}")
                traverse_tree(edge.outgoing_node_id, level + 1)

    # Start traversal from root
    roots = tree.get_root_nodes(session=session)
    for root in roots:
        traverse_tree(root.id)
```