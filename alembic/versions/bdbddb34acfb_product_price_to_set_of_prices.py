"""product price to set of prices

Revision ID: bdbddb34acfb
Revises: 
Create Date: 2024-08-25 20:52:53.948705

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'bdbddb34acfb'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'product_price',
        sa.Column('product_id', sa.Integer, nullable=False),
        sa.Column('price', sa.Float, nullable=True),
        sa.ForeignKeyConstraint(['product_id'], ['products.id']),
        sa.UniqueConstraint('product_id', 'price', name='uq_id_price')
    )

    # Удаление колонки price из products
    with op.batch_alter_table('products') as batch_op:
        batch_op.drop_column('price')


def downgrade() -> None:
    with op.batch_alter_table('products') as batch_op:
        batch_op.add_column(sa.Column('price', sa.Float, nullable=True))

    # Удаление новой таблицы
    op.drop_table('product_price')
