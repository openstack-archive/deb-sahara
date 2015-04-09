# Copyright (c) 2013 Hortonworks, Inc.
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

from sahara import exceptions
from sahara.i18n import _
from sahara.plugins import provisioning as p


HOST_REGISTRATIONS_TIMEOUT = p.Config(
    'Host registrations timeout', 'general',
    'cluster', config_type='int', priority=1,
    default_value=3600, is_optional=True,
    description='Timeout for host registrations, in seconds')

DECOMMISSIONING_TIMEOUT = p.Config(
    'Timeout for decommissioning nodes', 'general',
    'cluster', config_type='int', priority=1,
    default_value=1000, is_optional=True,
    description='Timeout for decommissioning nodes, in seconds')


class ConfigurationProvider(object):
    def __init__(self, config, hadoop_version):
        self.config = config
        self.config_mapper = {}
        self.config_items = []
        self.hadoop_version = hadoop_version
        self._initialize(config)

    def get_config_items(self):
        return self.config_items

    def get_applicable_target(self, name):
        return self.config_mapper.get(name)

    def _get_target(self, apptarget):
        if apptarget == 'TODO':
            apptarget = 'general'

        return apptarget

    def _initialize(self, config):
        for configuration in self.config['configurations']:
            for service_property in configuration['properties']:
                config = p.Config(service_property['name'],
                                  self._get_target(
                                      service_property['applicable_target']),
                                  service_property['scope'],
                                  config_type=service_property['config_type'],
                                  default_value=service_property
                                  ['default_value'],
                                  is_optional=service_property[
                                      'is_optional'],
                                  description=service_property[
                                      'description'])

                setattr(config, 'tag', configuration['tag'].rsplit(".", 1)[0])
                self.config_items.append(config)
                # TODO(jspeidel): an assumption is made that property names
                # are unique across configuration sections which is dangerous
                property_name = service_property['name']
                # if property already exists, throw an exception
                if property_name in self.config_mapper:
                    # internal error
                    # ambari-config-resource contains duplicates
                    raise exceptions.InvalidDataException(
                        _('Internal Error. Duplicate property '
                          'name detected: %s') % property_name)
                self.config_mapper[service_property['name']] = (
                    self._get_target(
                        service_property['applicable_target']))
        host_reg_timeout = copy.copy(HOST_REGISTRATIONS_TIMEOUT)
        setattr(host_reg_timeout, 'tag', 'global')
        self.config_items.append(host_reg_timeout)
        self.config_mapper[host_reg_timeout.name] = 'global'
        if self.hadoop_version == '2.0.6':
            dec_timeout = copy.copy(DECOMMISSIONING_TIMEOUT)
            setattr(dec_timeout, 'tag', 'global')
            self.config_items.append(dec_timeout)
            self.config_mapper[dec_timeout.name] = 'global'
