"""Initial migration

Revision ID: 001
Revises: 
Create Date: 2024-12-27
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers
revision = '001'
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    # Create Tree table
    op.create_table(
        'tree',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('parent_tree_id', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.ForeignKeyConstraint(['parent_tree_id'], ['tree.id'])
    )

    # Create TreeNode table
    op.create_table(
        'tree_node',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('tree_id', sa.Integer(), nullable=False),
        sa.Column('data', sa.JSON()),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.ForeignKeyConstraint(['tree_id'], ['tree.id'])
    )

    # Create TreeEdge table
    op.create_table(
        'tree_edge',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('incoming_node_id', sa.Integer(), nullable=False),
        sa.Column('outgoing_node_id', sa.Integer(), nullable=False),
        sa.Column('data', sa.JSON()),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.ForeignKeyConstraint(['incoming_node_id'], ['tree_node.id']),
        sa.ForeignKeyConstraint(['outgoing_node_id'], ['tree_node.id'])
    )

    # Create TreeTag table
    op.create_table(
        'tree_tag',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('tree_id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('description', sa.String()),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.ForeignKeyConstraint(['tree_id'], ['tree.id']),
        sa.UniqueConstraint('tree_id', 'name', name='uix_tree_tag_name')
    )

    # Create indexes
    op.create_index('idx_tree_parent', 'tree', ['parent_tree_id'])
    op.create_index('idx_node_tree', 'tree_node', ['tree_id'])
    op.create_index('idx_edge_nodes', 'tree_edge', ['incoming_node_id', 'outgoing_node_id'])
    op.create_index('idx_tag_tree_name', 'tree_tag', ['tree_id', 'name'])

def downgrade():
    # Drop indexes
    op.drop_index('idx_tag_tree_name')
    op.drop_index('idx_edge_nodes')
    op.drop_index('idx_node_tree')
    op.drop_index('idx_tree_parent')

    # Drop tables
    op.drop_table('tree_tag')
    op.drop_table('tree_edge')
    op.drop_table('tree_node')
    op.drop_table('tree')