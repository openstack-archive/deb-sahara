# Copyright (c) 2015, MapR Technologies
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.


import os


def _load_versions():
    d_name = os.path.dirname(__file__)
    m_template = 'sahara.plugins.mapr.versions.%s.version_handler'

    def predicate(v_dir):
        return os.path.isdir(os.path.join(d_name, v_dir))

    def mapper(v_dir):
        return m_template % v_dir

    def reducer(versions, m_name):
        m = __import__(m_name, fromlist=['sahara'])
        versions[m.version] = getattr(m, 'VersionHandler')()
        return versions

    v_dirs = filter(predicate, os.listdir(d_name))
    m_names = map(mapper, v_dirs)
    return reduce(reducer, m_names, {})


class VersionHandlerFactory(object):
    instance = None
    versions = None

    @staticmethod
    def get():
        if not VersionHandlerFactory.instance:
            VersionHandlerFactory.versions = _load_versions()
            VersionHandlerFactory.instance = VersionHandlerFactory()
        return VersionHandlerFactory.instance

    def get_versions(self):
        return VersionHandlerFactory.versions.keys()

    def get_handler(self, version):
        return VersionHandlerFactory.versions[version]
