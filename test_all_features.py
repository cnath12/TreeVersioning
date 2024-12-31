# test_all_features.py

from tree_versioning.models import Tree
from tree_versioning.database import db

def print_tree_info(tree, session, indent=""):
    """Helper function to print tree information."""
    print(f"{indent}Tree: {tree.name} (ID: {tree.id})")
    print(f"{indent}Nodes:")
    for node in tree.nodes:
        print(f"{indent}- Node {node.id}: {node.data}")
    print(f"{indent}Tags:")
    for tag in tree.tags:
        print(f"{indent}- {tag.name}: {tag.description}")

def test_configuration_management(session):
    print("\n=== Testing Configuration Management ===")

    # Create initial tree and configuration
    tree = Tree(name="main_config")
    session.add(tree)
    session.flush()
    
    # Add initial nodes
    db_node = tree.add_node(
        data={"type": "database", "host": "localhost", "port": 5432},
        session=session
    )
    cache_node = tree.add_node(
        data={"type": "cache", "host": "redis", "port": 6379},
        session=session
    )
    
    # Add initial edge
    tree.add_edge(
        db_node.id, 
        cache_node.id, 
        data={"relation": "uses"},
        session=session
    )
    session.commit()
    
    print("Initial configuration:")
    print_tree_info(tree, session)

    # Create new tag
    print("\nCreating new tag...")
    new_tag = tree.create_tag("release-v1.0", "Initial stable release", session=session)
    session.commit()
    
    # Create new version
    print("\nCreating new version from tag...")
    modified_tree = tree.create_new_tree_version_from_tag("release-v1.0", session=session)
    new_node = modified_tree.add_node(data={"setting": "new_value"}, session=session)
    modified_tree.create_tag("release-v1.1", "Added new setting", session=session)
    session.commit()
    
    print("\nModified tree:")
    print_tree_info(modified_tree, session, "  ")

def test_feature_branching(session):
    print("\n=== Testing Feature Branching ===")
    # Create main version
    main_tree = Tree(name="main_branch")
    session.add(main_tree)
    session.flush()
    
    base_config = main_tree.add_node(data={"version": "2.0"}, session=session)
    main_tree.create_tag("main-v2.0", "Main version 2.0", session=session)
    session.commit()  # Commit main branch changes
    
    # Create feature branch
    feature_branch = main_tree.create_new_tree_version_from_tag("main-v2.0", session=session)
    feature_branch.name = "feature_branch"
    
    # Add feature nodes
    node1 = feature_branch.add_node(data={"feature_flag": True}, session=session)
    node2 = feature_branch.add_node(data={"config": "new_setting"}, session=session)
    feature_branch.add_edge(node1.id, node2.id, data={"relation": "depends_on"}, session=session)
    feature_branch.create_tag("feature-x-v1", "Feature X implementation", session=session)
    session.commit()  # Commit feature branch changes
    
    print("\nFeature branch:")
    print_tree_info(feature_branch, session, "  ")

def test_rollback(session):
    print("\n=== Testing Rollback Scenario ===")
    # Get stable tree
    stable_tree = session.query(Tree).get(1)
    
    # Mark current state
    stable_tag = stable_tree.create_tag("stable-v1", "Known good state", session=session)
    session.commit()  # Commit the stable tag
    
    print("\nMarked stable state:")
    print_tree_info(stable_tree, session, "  ")
    
    # Make risky changes
    new_node = stable_tree.add_node(data={"experimental": True}, session=session)
    root_nodes = stable_tree.get_root_nodes(session=session)
    if root_nodes:
        stable_tree.add_edge(root_nodes[0].id, new_node.id, 
                           data={"type": "experimental"}, session=session)
    session.commit()  # Commit the risky changes
    
    print("\nAfter risky changes:")
    print_tree_info(stable_tree, session, "  ")
    
    # Rollback
    print("\nRolling back...")
    rollback_tree = stable_tree.restore_from_tag("stable-v1", session=session)
    session.commit()  # Commit the rollback
    
    print("\nAfter rollback:")
    print_tree_info(rollback_tree, session, "  ")
    
def test_advanced_traversal(session):
    print("\n=== Testing Advanced Traversal ===")
    tree = session.query(Tree).get(1)  # Get main config tree

    print("\nTesting depth traversal:")
    depth_0_nodes = tree.get_nodes_at_depth(0, session=session)
    depth_1_nodes = tree.get_nodes_at_depth(1, session=session)
    print(f"Nodes at depth 0: {[n.data for n in depth_0_nodes]}")
    print(f"Nodes at depth 1: {[n.data for n in depth_1_nodes]}")

    print("\nTesting path finding:")
    # Find path between first and last node
    nodes = tree.nodes
    if len(nodes) >= 2:
        path = tree.find_path(nodes[0].id, nodes[-1].id, session=session)
        print("Path found:")
        for node, edge in path:
            print(f"Node: {node.data}")
            print(f"Edge: {edge.data if edge else 'None'}")

    print("\nTesting recursive traversal:")
    def traverse_and_print(node_id, level=0):
        indent = "  " * level
        node = tree.get_node(node_id, session=session)
        print(f"{indent}Node {node_id}: {node.data}")
        edges = tree.get_node_edges(node_id, session=session)
        for edge in edges:
            if edge.incoming_node_id == node_id:  # Only traverse forward
                print(f"{indent}├── Edge: {edge.data}")
                traverse_and_print(edge.outgoing_node_id, level + 1)

    root_nodes = tree.get_root_nodes(session=session)
    for root in root_nodes:
        print("\nTraversing from root:", root.id)
        traverse_and_print(root.id)
        
def test_state_inspection(session):
    print("\n=== Testing State Inspection ===")
    tree = session.query(Tree).filter_by(name="main_config").first()
    
    # Get state at original tag
    state = tree.get_state_at_tag("v1.0", session=session)
    print("\nState at v1.0:")
    print(f"Number of nodes: {len(state['nodes'])}")
    print(f"Number of edges: {len(state['edges'])}")
    print(f"Tag time: {state['tag_time']}")
    
    for node in state['nodes']:
        print(f"Node: {node.data}")
    for edge in state['edges']:
        print(f"Edge: {edge.data}")
        
def cleanup_database(session):
    """Clean up the database before running tests."""
    print("Cleaning up database...")
    session.execute('DELETE FROM tree_edge')
    session.execute('DELETE FROM tree_tag')
    session.execute('DELETE FROM tree_node')
    session.execute('DELETE FROM tree')
    session.commit()
    
def main():
    with db.get_session() as session:
        try:
            # Clean up before running tests
            cleanup_database(session)
            
            test_configuration_management(session)
            session.commit()
            
            test_feature_branching(session)
            session.commit()
            
            test_rollback(session)
            session.commit()
            
            test_advanced_traversal(session)
            session.commit()
            
            test_state_inspection(session)
            session.commit()
            
            print("\nFinal database state:")
            print("\nTrees:")
            for tree in session.query(Tree).all():
                print_tree_info(tree, session, "  ")
                
        except Exception as e:
            print(f"Error: {e}")
            session.rollback()
            raise

if __name__ == "__main__":
    main()