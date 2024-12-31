def test_find_path(session, sample_tree):
    """Test finding a path between nodes."""
    node1 = sample_tree.add_node(data={"id": 1}, session=session)
    node2 = sample_tree.add_node(data={"id": 2}, session=session)
    node3 = sample_tree.add_node(data={"id": 3}, session=session)
    
    sample_tree.add_edge(node1.id, node2.id, data={}, session=session)
    sample_tree.add_edge(node2.id, node3.id, data={}, session=session)
    session.commit()
    
    path = sample_tree.find_path(node1.id, node3.id, session=session)
    assert len(path) == 3
    assert path[0][0].id == node1.id
    assert path[-1][0].id == node3.id

def test_root_nodes(session, sample_tree):
    """Test getting root nodes."""
    node1 = sample_tree.add_node(data={"root": True}, session=session)
    node2 = sample_tree.add_node(data={"child": True}, session=session)
    
    sample_tree.add_edge(node1.id, node2.id, data={}, session=session)
    session.commit()
    
    roots = sample_tree.get_root_nodes(session=session)
    assert len(roots) == 1
    assert roots[0].id == node1.id

def test_get_nodes_at_depth(session, sample_tree):
    """Test getting nodes at a specific depth."""
    root = sample_tree.add_node(data={"level": 0}, session=session)
    child1 = sample_tree.add_node(data={"level": 1}, session=session)
    child2 = sample_tree.add_node(data={"level": 1}, session=session)
    
    sample_tree.add_edge(root.id, child1.id, data={}, session=session)
    sample_tree.add_edge(root.id, child2.id, data={}, session=session)
    session.commit()
    
    level_1_nodes = sample_tree.get_nodes_at_depth(1, session=session)
    assert len(level_1_nodes) == 2
    assert all(node.data["level"] == 1 for node in level_1_nodes)
    
def test_edge_metadata(session, sample_tree):
    """Test edge metadata inspection."""
    node1 = sample_tree.add_node(data={"id": "source"}, session=session)
    node2 = sample_tree.add_node(data={"id": "target"}, session=session)
    
    edge_data = {"type": "connection", "weight": 1.0}
    sample_tree.add_edge(node1.id, node2.id, data=edge_data, session=session)
    session.commit()

    edges = sample_tree.get_node_edges(node1.id, session=session)
    assert len(edges) == 1
    assert edges[0].data == edge_data

def test_parent_traversal(session, sample_tree):
    """Test parent node traversal."""
    parent = sample_tree.add_node(data={"type": "parent"}, session=session)
    child1 = sample_tree.add_node(data={"type": "child1"}, session=session)
    child2 = sample_tree.add_node(data={"type": "child2"}, session=session)
    
    sample_tree.add_edge(parent.id, child1.id, data={}, session=session)
    sample_tree.add_edge(parent.id, child2.id, data={}, session=session)
    session.commit()

    parents1 = sample_tree.get_parent_nodes(child1.id, session=session)
    parents2 = sample_tree.get_parent_nodes(child2.id, session=session)
    
    assert len(parents1) == 1
    assert len(parents2) == 1
    assert parents1[0].id == parent.id
    assert parents2[0].id == parent.id