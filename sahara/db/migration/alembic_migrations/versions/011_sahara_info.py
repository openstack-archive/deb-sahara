# Copyright 2014 OpenStack Foundation.
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

"""add Sahara settings info to cluster

Revision ID: 011
Revises: 010
Create Date: 2014-08-26 22:36:00.783444

"""

# revision identifiers, used by Alembic.
revision = '011'
down_revision = '010'

from alembic import op
import sqlalchemy as sa

from sahara.db.sqlalchemy import types as st


def upgrade():
    op.add_column('clusters',
                  sa.Column('sahara_info', st.JsonEncoded()))
