# Copyright (c) 2015 Mirantis Inc.
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


import mock
from oslo_serialization import jsonutils

from sahara.plugins.ambari import client as ambari_client
from sahara.tests.unit import base


class AmbariClientTestCase(base.SaharaTestCase):
    def setUp(self):
        super(AmbariClientTestCase, self).setUp()

        self.http_client = mock.Mock()
        self.http_client.get = mock.Mock()
        self.http_client.post = mock.Mock()
        self.http_client.put = mock.Mock()
        self.http_client.delete = mock.Mock()

        self.headers = {"X-Requested-By": "sahara"}

        self.remote = mock.Mock()
        self.remote.get_http_client.return_value = self.http_client

        self.instance = mock.Mock()
        self.instance.remote.return_value = self.remote
        self.instance.management_ip = "1.2.3.4"

    def test_init_client_default(self):
        client = ambari_client.AmbariClient(self.instance)
        self.assertEqual(self.http_client, client._http_client)
        self.assertEqual("http://1.2.3.4:8080/api/v1", client._base_url)
        self.assertEqual("admin", client._auth.username)
        self.assertEqual("admin", client._auth.password)
        self.remote.get_http_client.assert_called_with("8080")

    def test_init_client_manual(self):
        client = ambari_client.AmbariClient(self.instance, port="1234",
                                            username="user", password="pass")
        self.assertEqual("http://1.2.3.4:1234/api/v1", client._base_url)
        self.assertEqual("user", client._auth.username)
        self.assertEqual("pass", client._auth.password)
        self.remote.get_http_client.assert_called_with("1234")

    def test_close_http_session(self):
        with ambari_client.AmbariClient(self.instance):
            pass
        self.remote.close_http_session.assert_called_with("8080")

    def test_get_method(self):
        client = ambari_client.AmbariClient(self.instance)
        client.get("http://spam")
        self.http_client.get.assert_called_with(
            "http://spam", verify=False, auth=client._auth,
            headers=self.headers)

    def test_post_method(self):
        client = ambari_client.AmbariClient(self.instance)
        client.post("http://spam", data="data")
        self.http_client.post.assert_called_with(
            "http://spam", data="data", verify=False, auth=client._auth,
            headers=self.headers)

    def test_put_method(self):
        client = ambari_client.AmbariClient(self.instance)
        client.put("http://spam", data="data")
        self.http_client.put.assert_called_with(
            "http://spam", data="data", verify=False, auth=client._auth,
            headers=self.headers)

    def test_delete_method(self):
        client = ambari_client.AmbariClient(self.instance)
        client.delete("http://spam")
        self.http_client.delete.assert_called_with(
            "http://spam", verify=False, auth=client._auth,
            headers=self.headers)

    def test_get_registered_hosts(self):
        client = ambari_client.AmbariClient(self.instance)
        resp_data = """{
  "href" : "http://1.2.3.4:8080/api/v1/hosts",
  "items" : [
    {
      "href" : "http://1.2.3.4:8080/api/v1/hosts/host1",
      "Hosts" : {
        "host_name" : "host1"
      }
    },
    {
      "href" : "http://1.2.3.4:8080/api/v1/hosts/host2",
      "Hosts" : {
        "host_name" : "host2"
      }
    },
    {
      "href" : "http://1.2.3.4:8080/api/v1/hosts/host3",
      "Hosts" : {
        "host_name" : "host3"
      }
    }
  ]
}"""
        resp = mock.Mock()
        resp.text = resp_data
        resp.status_code = 200
        self.http_client.get.return_value = resp
        hosts = client.get_registered_hosts()
        self.http_client.get.assert_called_with(
            "http://1.2.3.4:8080/api/v1/hosts", verify=False,
            auth=client._auth, headers=self.headers)
        self.assertEqual(3, len(hosts))
        self.assertEqual("host1", hosts[0]["Hosts"]["host_name"])
        self.assertEqual("host2", hosts[1]["Hosts"]["host_name"])
        self.assertEqual("host3", hosts[2]["Hosts"]["host_name"])

    def test_update_user_password(self):
        client = ambari_client.AmbariClient(self.instance)
        resp = mock.Mock()
        resp.text = ""
        resp.status_code = 200
        self.http_client.put.return_value = resp
        client.update_user_password("bart", "old_pw", "new_pw")
        exp_req = jsonutils.dumps({
            "Users": {
                "old_password": "old_pw",
                "password": "new_pw"
            }
        })
        self.http_client.put.assert_called_with(
            "http://1.2.3.4:8080/api/v1/users/bart", data=exp_req,
            verify=False, auth=client._auth, headers=self.headers)

    def test_create_blueprint(self):
        client = ambari_client.AmbariClient(self.instance)
        resp = mock.Mock()
        resp.text = ""
        resp.status_code = 200
        self.http_client.post.return_value = resp
        client.create_blueprint("cluster_name", {"some": "data"})
        self.http_client.post.assert_called_with(
            "http://1.2.3.4:8080/api/v1/blueprints/cluster_name",
            data=jsonutils.dumps({"some": "data"}), verify=False,
            auth=client._auth, headers=self.headers)

    def test_create_cluster(self):
        client = ambari_client.AmbariClient(self.instance)
        resp = mock.Mock()
        resp.text = """{
    "Requests": {
        "id": 1,
        "status": "InProgress"
    }
}"""
        resp.status_code = 200
        self.http_client.post.return_value = resp
        req_info = client.create_cluster("cluster_name", {"some": "data"})
        self.assertEqual(1, req_info["id"])
        self.http_client.post.assert_called_with(
            "http://1.2.3.4:8080/api/v1/clusters/cluster_name",
            data=jsonutils.dumps({"some": "data"}), verify=False,
            auth=client._auth, headers=self.headers)
