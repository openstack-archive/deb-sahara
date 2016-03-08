# Copyright 2015 OpenStack Foundation.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""set is_protected on is_default

Revision ID: 029
Revises: 028
Create Date: 2015-11-4 12:41:52.571258

"""

# revision identifiers, used by Alembic.
revision = '029'
down_revision = '028'

from alembic import op
import sqlalchemy as sa
from sqlalchemy.sql import table, column


def upgrade():
    ng = table('node_group_templates',
               column('is_protected', sa.Boolean),
               column('is_default', sa.Boolean))
    op.execute(
        ng.update().where(
            ng.c.is_default).values({'is_protected': True})
    )

    clt = table('cluster_templates',
                column('is_protected', sa.Boolean),
                column('is_default', sa.Boolean))
    op.execute(
        clt.update().where(
            clt.c.is_default).values({'is_protected': True})
    )
