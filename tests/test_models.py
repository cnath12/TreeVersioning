import pytest
from tree_versioning.models import Tree, TreeNode, TreeEdge, TreeTag
from tree_versioning.exceptions import CycleError

def test_create_tree(session):
    """Test creating a new tree."""
    tree = Tree(name="test_tree")
    session.add(tree)
    session.commit()
    
    assert tree.id is not None
    assert tree.name == "test_tree"

def test_create_tag(session, sample_tree):
    """Test creating a tag for a tree."""
    tag = sample_tree.create_tag("test-tag", "Test tag", session=session)
    session.commit()
    
    assert tag.name == "test-tag"
    assert tag.description == "Test tag"
    assert tag.tree_id == sample_tree.id

def test_create_version_from_tag(session, sample_tree):
    """Test creating a new version from a tag."""
    # Create initial node and tag
    node = sample_tree.add_node(data={"setting": "initial"}, session=session)
    sample_tree.create_tag("test-version", "Test version", session=session)
    session.commit()
    
    # Create new version
    new_version = sample_tree.create_new_tree_version_from_tag("test-version", session=session)
    session.commit()
    
    assert new_version.parent_tree_id == sample_tree.id
    assert len(new_version.nodes) == len(sample_tree.nodes)
    
def test_configuration_management(session):
    """Test complete configuration management workflow."""
    # Initial setup
    tree = Tree(name="config_tree")
    session.add(tree)
    session.flush()

    # Initial version
    tree.create_tag("v1.0", "Initial stable release", session=session)
    base_config = tree.add_node(data={"config": "base"}, session=session)
    session.commit()

    # Create new version with changes
    modified_tree = tree.create_new_tree_version_from_tag("v1.0", session=session)
    new_config = modified_tree.add_node(data={"setting": "new_value"}, session=session)
    modified_tree.add_edge(base_config.id, new_config.id, data={"weight": 0.5}, session=session)
    modified_tree.create_tag("v1.1", "Added new setting", session=session)
    session.commit()

    assert len(modified_tree.nodes) > len(tree.nodes)

def test_feature_branching(session):
    """Test feature branch workflow."""
    # Setup main branch
    main = Tree(name="main")
    session.add(main)
    session.flush()
    
    main_config = main.add_node(data={"main_setting": "default"}, session=session)
    main.create_tag("main-v1", "Main version", session=session)
    session.commit()

    # Create feature branch
    feature = main.create_new_tree_version_from_tag("main-v1", session=session)
    feature_flag = feature.add_node(data={"feature_flag": True}, session=session)
    feature_config = feature.add_node(data={"config": "new_setting"}, session=session)
    
    # Link feature configurations
    feature.add_edge(feature_flag.id, feature_config.id, 
                    data={"relation": "depends_on"}, session=session)
    feature.create_tag("feature-x", "Feature implementation", session=session)
    session.commit()

    assert len(feature.nodes) > len(main.nodes)

def test_rollback_scenario(session):
    """Test system rollback capability."""
    # Initial stable state
    tree = Tree(name="stable_system")
    session.add(tree)
    session.flush()
    
    stable_config = tree.add_node(data={"status": "stable"}, session=session)
    tree.create_tag("stable-v1", "Known good state", session=session)
    session.commit()

    # Record the initial state
    initial_node_count = len(tree.nodes)

    # Make risky changes
    experimental = tree.add_node(data={"experimental": True}, session=session)
    tree.add_edge(stable_config.id, experimental.id, 
                 data={"type": "experimental"}, session=session)
    session.commit()

    # Verify changes were made
    assert len(tree.nodes) > initial_node_count

    # Rollback
    rollback = tree.restore_from_tag("stable-v1", session=session)
    session.commit()

    # Verify rollback state
    assert len(rollback.nodes) == initial_node_count
    assert all(node.data.get("experimental") is None for node in rollback.nodes)
    """Test system rollback capability."""
    # Initial stable state
    tree = Tree(name="stable_system")
    session.add(tree)
    session.flush()
    
    stable_config = tree.add_node(data={"status": "stable"}, session=session)
    tree.create_tag("stable-v1", "Known good state", session=session)
    session.commit()

    # Make risky changes
    experimental = tree.add_node(data={"experimental": True}, session=session)
    tree.add_edge(stable_config.id, experimental.id, 
                 data={"type": "experimental"}, session=session)
    session.commit()

    # Rollback
    rollback = tree.restore_from_tag("stable-v1", session=session)
    session.commit()

    assert len(rollback.nodes) == 1
    assert rollback.nodes[0].data["status"] == "stable"