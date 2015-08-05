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

"""Add data_source_urls to job_executions to support placeholders

Revision ID: 021
Revises: 020
Create Date: 2015-02-24 12:47:17.871520

"""

# revision identifiers, used by Alembic.
revision = '021'
down_revision = '020'

from alembic import op
import sqlalchemy as sa

from sahara.db.sqlalchemy import types as st


def upgrade():
    op.add_column('job_executions',
                  sa.Column('data_source_urls', st.JsonEncoded()))
