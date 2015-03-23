# Copyright (c) 2013 Mirantis Inc.
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

import copy

from sahara.service.validations import node_group_template_schema as ngt_schema


def _build_ng_schema_for_cluster_tmpl():
    cl_tmpl_ng_schema = copy.deepcopy(ngt_schema.NODE_GROUP_TEMPLATE_SCHEMA)
    cl_tmpl_ng_schema['properties'].update({"count": {"type": "integer"}})
    cl_tmpl_ng_schema["required"] = ['name', 'flavor_id',
                                     'node_processes', 'count']
    del cl_tmpl_ng_schema['properties']['hadoop_version']
    del cl_tmpl_ng_schema['properties']['plugin_name']
    return cl_tmpl_ng_schema


_cluster_tmpl_ng_schema = _build_ng_schema_for_cluster_tmpl()


def _build_ng_tmpl_schema_for_cluster_template():
    cl_tmpl_ng_tmpl_schema = copy.deepcopy(_cluster_tmpl_ng_schema)
    cl_tmpl_ng_tmpl_schema['properties'].update(
        {
            "node_group_template_id": {
                "type": "string",
                "format": "uuid",
            }
        })
    cl_tmpl_ng_tmpl_schema["required"] = ["node_group_template_id",
                                          "name", "count"]
    return cl_tmpl_ng_tmpl_schema


_cluster_tmpl_ng_tmpl_schema = _build_ng_tmpl_schema_for_cluster_template()

CLUSTER_TEMPLATE_SCHEMA = {
    "type": "object",
    "properties": {
        "name": {
            "type": "string",
            "minLength": 1,
            "maxLength": 50,
            "format": "valid_name_hostname",
        },
        "plugin_name": {
            "type": "string",
        },
        "hadoop_version": {
            "type": "string",
        },
        "default_image_id": {
            "type": "string",
            "format": "uuid",
        },
        "cluster_configs": {
            "type": "configs",
        },
        "node_groups": {
            "type": "array",
            "items": {
                "oneOf": [_cluster_tmpl_ng_tmpl_schema,
                          _cluster_tmpl_ng_schema]
            }
        },
        "anti_affinity": {
            "type": "array",
            "items": {
                "type": "string",
            },
        },
        "description": {
            "type": "string",
        },
        "neutron_management_network": {
            "type": "string",
            "format": "uuid"
        },
    },
    "additionalProperties": False,
    "required": [
        "name",
        "plugin_name",
        "hadoop_version",
    ]
}

CLUSTER_TEMPLATE_UPDATE_SCHEMA = copy.copy(CLUSTER_TEMPLATE_SCHEMA)
CLUSTER_TEMPLATE_UPDATE_SCHEMA["required"] = []
