# Copyright (c) 2016 Red Hat, Inc.
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

from sahara import conductor as c
from sahara import context


conductor = c.API


# NodeGroupTemplate ops

def get_node_group_templates(**kwargs):
    return conductor.node_group_template_get_all(context.ctx(),
                                                 regex_search=True, **kwargs)


def get_node_group_template(id):
    return conductor.node_group_template_get(context.ctx(), id)


def create_node_group_template(values):
    return conductor.node_group_template_create(context.ctx(), values)


def terminate_node_group_template(id):
    return conductor.node_group_template_destroy(context.ctx(), id)


def update_node_group_template(id, values):
    return conductor.node_group_template_update(context.ctx(), id, values)
