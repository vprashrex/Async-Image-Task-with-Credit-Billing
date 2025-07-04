"""rename task_metadata to processing_metadata

Revision ID: ae210956d3ac
Revises: 4b9c1245fa24
Create Date: 2025-06-12 02:03:54.691037

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'ae210956d3ac'
down_revision: Union[str, None] = '4b9c1245fa24'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('tasks', sa.Column('processing_metadata', sa.JSON(), nullable=True))
    op.drop_column('tasks', 'task_metadata')
    # ### end Alembic commands ###


def downgrade() -> None:
    """Downgrade schema."""
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('tasks', sa.Column('task_metadata', postgresql.JSON(astext_type=sa.Text()), autoincrement=False, nullable=True))
    op.drop_column('tasks', 'processing_metadata')
    # ### end Alembic commands ###
