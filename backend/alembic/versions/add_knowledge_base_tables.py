"""add_knowledge_base_tables

Revision ID: kb001
Revises: 425ccad1ad52
Create Date: 2024-12-19 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'kb001'
down_revision = '425ccad1ad52'
branch_labels = None
depends_on = None


def upgrade():
    # Create knowledge_base table
    op.create_table('knowledge_base',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(length=200), nullable=False, comment='知识标题'),
        sa.Column('content', sa.Text(), nullable=False, comment='知识内容'),
        sa.Column('summary', sa.Text(), nullable=True, comment='知识摘要'),
        sa.Column('source_file', sa.String(length=500), nullable=True, comment='来源文件'),
        sa.Column('source_type', sa.String(length=50), nullable=True, comment='来源类型'),
        sa.Column('tags', sa.String(length=500), nullable=True, comment='标签，逗号分隔'),
        sa.Column('created_by', sa.Integer(), nullable=True, comment='创建者ID'),
        sa.Column('is_active', sa.Boolean(), nullable=True, comment='是否启用'),
        sa.Column('view_count', sa.Integer(), nullable=True, comment='查看次数'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True, comment='创建时间'),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True, comment='更新时间'),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_knowledge_title', 'knowledge_base', ['title'], unique=False)
    op.create_index('idx_knowledge_tags', 'knowledge_base', ['tags'], unique=False)
    op.create_index('idx_knowledge_created_by', 'knowledge_base', ['created_by'], unique=False)
    op.create_index('idx_knowledge_created_at', 'knowledge_base', ['created_at'], unique=False)
    op.create_index(op.f('ix_knowledge_base_id'), 'knowledge_base', ['id'], unique=False)

    # Create knowledge_qa table
    op.create_table('knowledge_qa',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('knowledge_id', sa.Integer(), nullable=False, comment='知识ID'),
        sa.Column('question', sa.Text(), nullable=False, comment='问题'),
        sa.Column('answer', sa.Text(), nullable=False, comment='答案'),
        sa.Column('user_id', sa.Integer(), nullable=True, comment='用户ID'),
        sa.Column('session_id', sa.String(length=100), nullable=True, comment='会话ID'),
        sa.Column('is_guest', sa.Boolean(), nullable=True, comment='是否游客'),
        sa.Column('is_helpful', sa.Boolean(), nullable=True, comment='是否有帮助'),
        sa.Column('feedback', sa.Text(), nullable=True, comment='用户反馈'),
        sa.Column('response_time', sa.Integer(), nullable=True, comment='响应时间(毫秒)'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True, comment='创建时间'),
        sa.ForeignKeyConstraint(['knowledge_id'], ['knowledge_base.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_qa_knowledge_id', 'knowledge_qa', ['knowledge_id'], unique=False)
    op.create_index('idx_qa_user_id', 'knowledge_qa', ['user_id'], unique=False)
    op.create_index('idx_qa_session_id', 'knowledge_qa', ['session_id'], unique=False)
    op.create_index('idx_qa_created_at', 'knowledge_qa', ['created_at'], unique=False)
    op.create_index(op.f('ix_knowledge_qa_id'), 'knowledge_qa', ['id'], unique=False)

    # Create preset_questions table
    op.create_table('preset_questions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('question', sa.String(length=500), nullable=False, comment='问题内容'),
        sa.Column('category', sa.String(length=100), nullable=True, comment='问题分类'),
        sa.Column('order_index', sa.Integer(), nullable=True, comment='排序索引'),
        sa.Column('is_active', sa.Boolean(), nullable=True, comment='是否启用'),
        sa.Column('click_count', sa.Integer(), nullable=True, comment='点击次数'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True, comment='创建时间'),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True, comment='更新时间'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_preset_category', 'preset_questions', ['category'], unique=False)
    op.create_index('idx_preset_order', 'preset_questions', ['order_index'], unique=False)
    op.create_index(op.f('ix_preset_questions_id'), 'preset_questions', ['id'], unique=False)

    # Set default values
    op.execute("UPDATE knowledge_base SET source_type = 'document' WHERE source_type IS NULL")
    op.execute("UPDATE knowledge_base SET is_active = true WHERE is_active IS NULL")
    op.execute("UPDATE knowledge_base SET view_count = 0 WHERE view_count IS NULL")
    op.execute("UPDATE knowledge_qa SET is_guest = false WHERE is_guest IS NULL")
    op.execute("UPDATE preset_questions SET order_index = 0 WHERE order_index IS NULL")
    op.execute("UPDATE preset_questions SET is_active = true WHERE is_active IS NULL")
    op.execute("UPDATE preset_questions SET click_count = 0 WHERE click_count IS NULL")


def downgrade():
    # Drop tables in reverse order
    op.drop_index(op.f('ix_preset_questions_id'), table_name='preset_questions')
    op.drop_index('idx_preset_order', table_name='preset_questions')
    op.drop_index('idx_preset_category', table_name='preset_questions')
    op.drop_table('preset_questions')
    
    op.drop_index(op.f('ix_knowledge_qa_id'), table_name='knowledge_qa')
    op.drop_index('idx_qa_created_at', table_name='knowledge_qa')
    op.drop_index('idx_qa_session_id', table_name='knowledge_qa')
    op.drop_index('idx_qa_user_id', table_name='knowledge_qa')
    op.drop_index('idx_qa_knowledge_id', table_name='knowledge_qa')
    op.drop_table('knowledge_qa')
    
    op.drop_index(op.f('ix_knowledge_base_id'), table_name='knowledge_base')
    op.drop_index('idx_knowledge_created_at', table_name='knowledge_base')
    op.drop_index('idx_knowledge_created_by', table_name='knowledge_base')
    op.drop_index('idx_knowledge_tags', table_name='knowledge_base')
    op.drop_index('idx_knowledge_title', table_name='knowledge_base')
    op.drop_table('knowledge_base') 