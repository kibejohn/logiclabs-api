"""Add client_id to ScoreCalculation

Revision ID: 4235318828c6
Revises: 7569267de298
Create Date: 2025-04-10 19:05:31.825424

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '4235318828c6'
down_revision: Union[str, None] = '7569267de298'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('score_calculations', sa.Column('client_id', sa.Integer(), nullable=False))
    op.alter_column('score_calculations', 'percentage_threshold',
               existing_type=sa.INTEGER(),
               type_=sa.Float(),
               existing_nullable=True)
    op.alter_column('scorecard_versions', 'percentage_threshold',
               existing_type=sa.INTEGER(),
               type_=sa.Float(),
               existing_nullable=True)
    op.alter_column('scorecards', 'percentage_threshold',
               existing_type=sa.INTEGER(),
               type_=sa.Float(),
               existing_nullable=True)
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column('scorecards', 'percentage_threshold',
               existing_type=sa.Float(),
               type_=sa.INTEGER(),
               existing_nullable=True)
    op.alter_column('scorecard_versions', 'percentage_threshold',
               existing_type=sa.Float(),
               type_=sa.INTEGER(),
               existing_nullable=True)
    op.alter_column('score_calculations', 'percentage_threshold',
               existing_type=sa.Float(),
               type_=sa.INTEGER(),
               existing_nullable=True)
    op.drop_column('score_calculations', 'client_id')
    # ### end Alembic commands ###
