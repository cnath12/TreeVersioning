from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from .models import Tree, TreeNode, TreeEdge
from .database import db

def create_initial_tree(
    name: str,
    root_data: Dict[str, Any],
    initial_tag: Optional[str] = "v1.0",
    session: Optional[Session] = None
) -> Tree:
    """Create an initial tree with a root node and optional tag."""
    if session is None:
        with db.get_session() as session:
            return _create_tree(name, root_data, initial_tag, session)
    return _create_tree(name, root_data, initial_tag, session)

def _create_tree(name: str, root_data: dict, initial_tag: str, session: Session) -> Tree:
    """Internal function to create tree with session."""
    tree = Tree(name=name)
    session.add(tree)
    session.flush()
    
    root = tree.add_node(data=root_data, session=session)
    
    if initial_tag:
        tree.create_tag(
            name=initial_tag,
            description=f"Initial version of {name}",
            session=session
        )
    
    session.commit()
    return tree