import pytest
from datetime import datetime
from sqlalchemy.exc import IntegrityError
from tree_versioning.models import Tree, TreeNode, TreeEdge, TreeTag
from tree_versioning.exceptions import CycleError

def test_tree_create_and_retrieve(session):
    """Test creating and retrieving a tree with nodes and edges."""
    # Create tree
    tree = Tree(name="integration_tree")
    session.add(tree)
    session.flush()

    # Add nodes
    root = tree.add_node(data={"type": "root", "value": "root_value"}, session=session)
    child1 = tree.add_node(data={"type": "child", "value": "child1_value"}, session=session)
    child2 = tree.add_node(data={"type": "child", "value": "child2_value"}, session=session)
    
    # Add edges
    edge1 = tree.add_edge(root.id, child1.id, data={"relation": "parent-child"}, session=session)
    edge2 = tree.add_edge(root.id, child2.id, data={"relation": "parent-child"}, session=session)
    session.commit()

    # Retrieve and verify
    loaded_tree = session.query(Tree).filter_by(name="integration_tree").first()
    assert loaded_tree is not None
    assert len(loaded_tree.nodes) == 3
    
    root_nodes = loaded_tree.get_root_nodes(session=session)
    assert len(root_nodes) == 1
    assert root_nodes[0].data["type"] == "root"

def test_version_management(session):
    """Test full version management workflow."""
    # Create initial tree
    tree = Tree(name="version_test")
    session.add(tree)
    session.flush()

    # Create initial structure
    root = tree.add_node(data={"version": "1.0"}, session=session)
    child = tree.add_node(data={"setting": "initial"}, session=session)
    tree.add_edge(root.id, child.id, data={}, session=session)
    
    # Tag initial version
    tree.create_tag("v1.0", "Initial version", session=session)
    session.commit()

    # Create new version
    new_version = tree.create_new_tree_version_from_tag("v1.0", session=session)
    new_setting = new_version.add_node(data={"setting": "modified"}, session=session)
    root_nodes = new_version.get_root_nodes(session=session)
    new_version.add_edge(root_nodes[0].id, new_setting.id, data={}, session=session)
    new_version.create_tag("v1.1", "Modified version", session=session)
    session.commit()

    # Verify both versions
    v1_tree = Tree.get_by_tag("v1.0", session=session)
    v2_tree = Tree.get_by_tag("v1.1", session=session)
    
    assert len(v1_tree.nodes) == 2
    assert len(v2_tree.nodes) == 3
    assert v2_tree.parent_tree_id == v1_tree.id

def test_concurrent_modifications(session, SessionFactory):
    """Test handling concurrent modifications to the same tree."""
    tree = Tree(name="concurrent_test")
    session.add(tree)
    session.flush()

    # Create initial structure
    node1 = tree.add_node(data={"value": "1"}, session=session)
    node2 = tree.add_node(data={"value": "2"}, session=session)
    session.commit()

    # Create second session
    session2 = SessionFactory()

    try:
        # Create edge 1->2 in first session
        tree.add_edge(node1.id, node2.id, data={"first": True}, session=session)
        
        # Try to create edge 2->1 in second session (would create cycle)
        tree2 = session2.query(Tree).filter_by(name="concurrent_test").first()
        
        # This should raise CycleError
        try:
            tree2.add_edge(node2.id, node1.id, data={"second": True}, session=session2)
            session2.commit()
            pytest.fail("Expected CycleError but no error was raised")
        except CycleError:
            # Test passed - we expected this error
            pass
        
        # First session's changes should still be committable
        session.commit()
        
        # Verify the edge 1->2 exists
        edges = session.query(TreeEdge).filter_by(
            incoming_node_id=node1.id, 
            outgoing_node_id=node2.id
        ).all()
        assert len(edges) == 1
        assert edges[0].data["first"] is True
        
    finally:
        session2.close()
def test_tree_constraints(session):
    """Test database constraints and integrity."""
    tree = Tree(name="constraint_test")
    session.add(tree)
    session.flush()

    # Test unique tag names per tree
    tree.create_tag("test-tag", "First tag", session=session)
    session.commit()

    # Should raise IntegrityError for duplicate tag
    with pytest.raises(IntegrityError):
        tree.create_tag("test-tag", "Duplicate tag", session=session)
        session.commit()
        
    # Always rollback after IntegrityError
    session.rollback()

def test_complex_operations(session):
    """Test complex tree operations and traversal."""
    tree = Tree(name="complex_test")
    session.add(tree)
    session.flush()

    # Create a more complex structure
    nodes = {}
    for i in range(5):
        nodes[i] = tree.add_node(data={"value": str(i)}, session=session)
    
    # Create a diamond pattern
    tree.add_edge(nodes[0].id, nodes[1].id, data={}, session=session)
    tree.add_edge(nodes[0].id, nodes[2].id, data={}, session=session)
    tree.add_edge(nodes[1].id, nodes[3].id, data={}, session=session)
    tree.add_edge(nodes[2].id, nodes[3].id, data={}, session=session)
    tree.add_edge(nodes[3].id, nodes[4].id, data={}, session=session)
    session.commit()

    # Test path finding
    path = tree.find_path(nodes[0].id, nodes[4].id, session=session)
    assert len(path) > 0
    
    # Test depth retrieval
    depth_2_nodes = tree.get_nodes_at_depth(2, session=session)
    assert len(depth_2_nodes) == 1
    assert depth_2_nodes[0].id == nodes[3].id

    # Verify structure
    root_nodes = tree.get_root_nodes(session=session)
    assert len(root_nodes) == 1
    assert root_nodes[0].id == nodes[0].id
    
def test_tag_metadata_and_state(session):
    """Test tag metadata and state inspection."""
    tree = Tree(name="tag_test")
    session.add(tree)
    session.flush()

    # Create initial structure
    root = tree.add_node(data={"config": "base"}, session=session)
    node1 = tree.add_node(data={"setting": "value1"}, session=session)
    tree.add_edge(root.id, node1.id, data={"type": "contains"}, session=session)
    session.commit()

    # Add tag and immediately get its time
    tag = tree.create_tag("v1", "Initial state", session=session)
    tag_time = tag.created_at
    session.commit()

    # Add more changes after tag
    node2 = tree.add_node(data={"setting": "value2"}, session=session)
    tree.add_edge(root.id, node2.id, data={"type": "contains"}, session=session)
    session.commit()

    # Get state at tag point
    state = tree.get_state_at_tag("v1", session=session)

    # Verify metadata and state
    assert tag.description == "Initial state"
    assert state['tag_time'] is not None
    assert state['tag_time'] == tag.created_at  # Compare with tag's time directly

    # Verify only original nodes/edges are present
    assert len(state['nodes']) == 2  # root and node1 only
    node_data = [n.data for n in state['nodes']]
    assert any(n.get("config") == "base" for n in node_data)  # has root node
    assert any(n.get("setting") == "value1" for n in node_data)  # has first child
    assert not any(n.get("setting") == "value2" for n in node_data)  # doesn't have second child

    assert len(state['edges']) == 1  # root->node1 edge only
    edge = state['edges'][0]
    assert edge.data["type"] == "contains"
      
def test_version_state_inspection(session):
    """Test state inspection across different versions."""
    # Create base version
    tree = Tree(name="version_state_test")
    session.add(tree)
    session.flush()

    root = tree.add_node(data={"version": "1.0"}, session=session)
    tree.create_tag("v1", "Version 1", session=session)
    session.commit()

    # Create new version
    v2 = tree.create_new_tree_version_from_tag("v1", session=session)
    new_node = v2.add_node(data={"version": "2.0"}, session=session)
    v2.add_edge(root.id, new_node.id, data={}, session=session)
    v2.create_tag("v2", "Version 2", session=session)
    session.commit()

    # Test state at different tags
    v1_state = tree.get_state_at_tag("v1", session=session)
    v2_state = v2.get_state_at_tag("v2", session=session)

    assert len(v1_state['nodes']) == 1
    assert len(v2_state['nodes']) == 2
    assert v1_state['tag_time'] < v2_state['tag_time']