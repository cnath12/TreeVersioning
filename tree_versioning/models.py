# tree_versioning/models.py

from datetime import datetime
from typing import Optional, List, Dict, Any, Tuple
from sqlalchemy import (
    create_engine, Column, Integer, String, JSON, 
    DateTime, ForeignKey, UniqueConstraint, Index
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, Session
from .database import db
from .exceptions import CycleError, TagNotFoundError, NodeNotFoundError

Base = declarative_base()

class Tree(Base):
    __tablename__ = 'tree'
    
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    parent_tree_id = Column(Integer, ForeignKey('tree.id'), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    nodes = relationship("TreeNode", back_populates="tree", cascade="all, delete-orphan")
    tags = relationship("TreeTag", back_populates="tree", cascade="all, delete-orphan")
    parent = relationship("Tree", remote_side=[id], backref="children")

    @classmethod
    def get(cls, id: int) -> 'Tree':
        """Get a tree by its ID."""
        with db.session_scope() as session:
            tree = session.query(cls).get(id)
            if not tree:
                raise ValueError(f"Tree {id} not found")
            return tree

    @classmethod
    def get_by_tag(cls, tag_name: str, session: Session) -> 'Tree':
        """Get a tree by its tag name."""
        tag = session.query(TreeTag).filter_by(name=tag_name).first()
        if not tag:
            raise TagNotFoundError(f"Tag {tag_name} not found")
        return tag.tree

    def create_tag(self, name: str, description: str = None, session: Session = None) -> 'TreeTag':
        """Create a new tag for this tree version."""
        tag = TreeTag(tree=self, name=name, description=description)
        if session:
            session.add(tag)
            return tag
        else:
            with db.session_scope() as session:
                session.add(tag)
                return tag

    def create_new_tree_version_from_tag(self, tag_name: str, session: Session = None) -> 'Tree':
        """Create a new tree version from a tagged state."""
        if not session:
            raise ValueError("Session is required")
            
        tag = session.query(TreeTag).filter_by(name=tag_name, tree_id=self.id).first()
        if not tag:
            raise TagNotFoundError(f"Tag {tag_name} not found")

        # Create new tree with reference to parent
        new_tree = Tree(name=f"{self.name}_from_{tag_name}", parent_tree_id=self.id)  # Changed this line
        session.add(new_tree)
        
        # Copy nodes
        node_mapping = {}  # old_id -> new_node
        for old_node in self.nodes:  # Changed this line
            new_node = TreeNode(
                tree=new_tree,
                data=old_node.data
            )
            session.add(new_node)
            node_mapping[old_node.id] = new_node

        # Copy edges
        for old_node in self.nodes:  # Changed this line
            edges = session.query(TreeEdge).filter_by(incoming_node_id=old_node.id).all()
            for edge in edges:
                new_edge = TreeEdge(
                    incoming_node=node_mapping[edge.incoming_node_id],
                    outgoing_node=node_mapping[edge.outgoing_node_id],
                    data=edge.data
                )
                session.add(new_edge)

        return new_tree

    def add_node(self, data: Dict[str, Any], session: Session = None) -> 'TreeNode':
        """Add a new node to the tree."""
        if not session:
            raise ValueError("Session is required")
            
        node = TreeNode(tree=self, data=data)
        session.add(node)
        session.flush()  # Added this to ensure ID is generated
        return node

    def add_edge(self, node_id_1: int, node_id_2: int, data: Dict[str, Any], session: Session) -> 'TreeEdge':
        """Add a new edge between nodes, preventing cycles."""
        if not session:
            raise ValueError("Session is required")
        
        if self.would_create_cycle(node_id_1, node_id_2, session):  # Changed from _would_create_cycle to would_create_cycle
            raise CycleError("Adding this edge would create a cycle")

        edge = TreeEdge(
            incoming_node_id=node_id_1,
            outgoing_node_id=node_id_2,
            data=data
        )
        session.add(edge)
        session.flush()
        return edge

    def get_root_nodes(self, session: Session) -> List['TreeNode']:
        """Get all root nodes (nodes with no incoming edges)."""
        subquery = session.query(TreeEdge.outgoing_node_id).distinct()
        return session.query(TreeNode).filter(
            TreeNode.tree_id == self.id,
            ~TreeNode.id.in_(subquery)
        ).all()

    def get_root_node(self) -> 'TreeNode':
        """Get the single root node. Raises error if multiple roots exist."""
        roots = self.get_root_nodes()
        if len(roots) > 1:
            raise ValueError("Tree has multiple root nodes")
        if not roots:
            raise NodeNotFoundError("Tree has no root node")
        return roots[0]

    def get_node(self, node_id: int, session: Session) -> 'TreeNode':
        """Get a specific node by ID."""
        node = session.query(TreeNode).filter_by(id=node_id, tree_id=self.id).first()
        if not node:
            raise NodeNotFoundError(f"Node {node_id} not found")
        return node

    def get_child_nodes(self, node_id: int) -> List['TreeNode']:
        """Get all child nodes of a specific node."""
        with db.session_scope() as session:
            edges = session.query(TreeEdge).filter_by(incoming_node_id=node_id).all()
            return [edge.outgoing_node for edge in edges]

    def get_parent_nodes(self, node_id: int, session: Session) -> List['TreeNode']:
        """Get all parent nodes of a specific node."""
        edges = session.query(TreeEdge).filter_by(outgoing_node_id=node_id).all()
        return [edge.incoming_node for edge in edges]

    def get_node_edges(self, node_id: int, session: Session) -> List['TreeEdge']:
        """Get all edges connected to a specific node."""
        return session.query(TreeEdge).filter(
            (TreeEdge.incoming_node_id == node_id) | 
            (TreeEdge.outgoing_node_id == node_id)
        ).all()


    def get_nodes_at_depth(self, depth: int, session: Session) -> List['TreeNode']:
        """Get all nodes at a specific depth in the tree."""
        def get_node_depth(node_id: int, visited=None) -> int:
            if visited is None:
                visited = set()
            if node_id in visited:
                return -1
            visited.add(node_id)
            
            parents = session.query(TreeEdge).filter_by(outgoing_node_id=node_id).all()
            if not parents:
                return 0
            return 1 + max(get_node_depth(edge.incoming_node_id, visited.copy()) 
                        for edge in parents)

        all_nodes = session.query(TreeNode).filter_by(tree_id=self.id).all()
        return [node for node in all_nodes if get_node_depth(node.id) == depth]

    def find_path(self, start_node_id: int, end_node_id: int, session: Session) -> List[Tuple['TreeNode', Optional['TreeEdge']]]:
        """Find a path between two nodes."""
        if not session:
            raise ValueError("Session is required")

        def bfs(start: int, end: int) -> List[Tuple[int, Optional[int]]]:
            queue = [(start, [])]
            visited = {start}
            
            while queue:
                current, path = queue.pop(0)
                if current == end:
                    return path + [(current, None)]
                
                edges = session.query(TreeEdge).filter_by(incoming_node_id=current).all()
                for edge in edges:
                    next_node = edge.outgoing_node_id
                    if next_node not in visited:
                        visited.add(next_node)
                        queue.append((next_node, path + [(current, edge.id)]))
            
            return []

        path = bfs(start_node_id, end_node_id)
        if not path:
            raise ValueError(f"No path found between nodes {start_node_id} and {end_node_id}")

        result = []
        for i, (node_id, edge_id) in enumerate(path):
            node = session.query(TreeNode).get(node_id)
            edge = session.query(TreeEdge).get(edge_id) if edge_id else None
            result.append((node, edge))
        return result

    def restore_from_tag(self, tag_name: str, session: Session) -> 'Tree':
        """Restore the tree to a previously tagged state."""
        tag = session.query(TreeTag).filter_by(name=tag_name, tree_id=self.id).first()
        if not tag:
            raise TagNotFoundError(f"Tag {tag_name} not found")
        
        # Get nodes that existed before the tag was created
        tag_time = tag.created_at
        old_nodes = session.query(TreeNode).filter(
            TreeNode.tree_id == self.id,
            TreeNode.created_at <= tag_time
        ).all()
        
        # Create new tree with parent relationship
        new_tree = Tree(name=f"{self.name}_restored_from_{tag_name}", 
                    parent_tree_id=self.id)
        session.add(new_tree)
        session.flush()
        
        # Copy only the nodes that existed at tag time
        node_mapping = {}
        for old_node in old_nodes:
            new_node = TreeNode(
                tree=new_tree,
                data=old_node.data.copy()  # Make a copy of the data
            )
            session.add(new_node)
            session.flush()
            node_mapping[old_node.id] = new_node
        
        # Copy only the edges that existed at tag time
        old_edges = session.query(TreeEdge).filter(
            TreeEdge.incoming_node_id.in_([n.id for n in old_nodes]),
            TreeEdge.created_at <= tag_time
        ).all()
        
        for edge in old_edges:
            if edge.outgoing_node_id in node_mapping:
                new_edge = TreeEdge(
                    incoming_node=node_mapping[edge.incoming_node_id],
                    outgoing_node=node_mapping[edge.outgoing_node_id],
                    data=edge.data.copy()
                )
                session.add(new_edge)
        
        session.flush()
        return new_tree
    
    def would_create_cycle(self, from_node: int, to_node: int, session: Session) -> bool:
        """Check if adding an edge would create a cycle."""
        visited = set()
        
        def dfs(current_node: int) -> bool:
            if current_node == from_node:
                return True
            if current_node in visited:
                return False
                
            visited.add(current_node)
            edges = session.query(TreeEdge).filter_by(incoming_node_id=current_node).all()
            return any(dfs(edge.outgoing_node_id) for edge in edges)
            
        return dfs(to_node)
    
    def get_state_at_tag(self, tag_name: str, session: Session):
        """View tree state at a specific tag without creating new version."""
        tag = session.query(TreeTag).filter_by(name=tag_name, tree_id=self.id).first()
        if not tag:
            raise TagNotFoundError(f"Tag {tag_name} not found")
        
        tag_time = tag.created_at
        nodes = session.query(TreeNode).filter(
            TreeNode.tree_id == self.id,
            TreeNode.created_at <= tag_time
        ).all()
        
        edges = session.query(TreeEdge).filter(
            TreeEdge.incoming_node_id.in_([n.id for n in nodes]),
            TreeEdge.created_at <= tag_time
        ).all()
        
        return {
            'nodes': nodes,
            'edges': edges,
            'tag_time': tag_time
        }

class TreeNode(Base):
    __tablename__ = 'tree_node'
    
    id = Column(Integer, primary_key=True)
    tree_id = Column(Integer, ForeignKey('tree.id'), nullable=False)
    data = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    tree = relationship("Tree", back_populates="nodes")
    incoming_edges = relationship("TreeEdge", 
                                foreign_keys="TreeEdge.incoming_node_id", 
                                back_populates="incoming_node")
    outgoing_edges = relationship("TreeEdge", 
                                foreign_keys="TreeEdge.outgoing_node_id", 
                                back_populates="outgoing_node")

class TreeEdge(Base):
    __tablename__ = 'tree_edge'
    
    id = Column(Integer, primary_key=True)
    incoming_node_id = Column(Integer, ForeignKey('tree_node.id'), nullable=False)
    outgoing_node_id = Column(Integer, ForeignKey('tree_node.id'), nullable=False)
    data = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    incoming_node = relationship("TreeNode", 
                               foreign_keys=[incoming_node_id], 
                               back_populates="incoming_edges")
    outgoing_node = relationship("TreeNode", 
                               foreign_keys=[outgoing_node_id], 
                               back_populates="outgoing_edges")

class TreeTag(Base):
    __tablename__ = 'tree_tag'
    
    id = Column(Integer, primary_key=True)
    tree_id = Column(Integer, ForeignKey('tree.id'), nullable=False)
    name = Column(String, nullable=False)
    description = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    tree = relationship("Tree", back_populates="tags")

    __table_args__ = (
        UniqueConstraint('tree_id', 'name', name='uix_tree_tag_name'),
    )

# Create indexes for better query performance
Index('idx_tree_parent', Tree.parent_tree_id)
Index('idx_node_tree', TreeNode.tree_id)
Index('idx_edge_nodes', TreeEdge.incoming_node_id, TreeEdge.outgoing_node_id)
Index('idx_tag_tree_name', TreeTag.tree_id, TreeTag.name)