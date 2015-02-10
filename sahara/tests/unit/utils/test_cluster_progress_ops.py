# Copyright (c) 2014 Mirantis Inc.
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

import uuid

from sahara import conductor
from sahara import context
from sahara.tests.unit import base
from sahara.tests.unit.conductor import test_api
from sahara.utils import cluster_progress_ops as cpo


class FakeInstance(object):
    def __init__(self):
        self.id = uuid.uuid4()
        self.name = uuid.uuid4()


class ClusterProgressOpsTest(base.SaharaWithDbTestCase):
    def setUp(self):
        super(ClusterProgressOpsTest, self).setUp()
        self.api = conductor.API

    def _make_sample(self):
        ctx = context.ctx()
        cluster = self.api.cluster_create(ctx, test_api.SAMPLE_CLUSTER)
        return ctx, cluster

    def test_update_provisioning_steps(self):
        ctx, cluster = self._make_sample()

        step_id1 = self.api.cluster_provision_step_add(ctx, cluster.id, {
            "step_name": "some_name1",
            "total": 2,
        })

        self.api.cluster_event_add(ctx, step_id1, {
            "event_info": "INFO",
            "successful": True
        })

        cpo.update_provisioning_steps(cluster.id)

        # check that we have correct provision step

        result_cluster = self.api.cluster_get(ctx, cluster.id)
        result_step = result_cluster.provision_progress[0]

        self.assertEqual(None, result_step.successful)
        self.assertEqual(1, result_step.completed)

        # check updating in case of successful provision step

        self.api.cluster_event_add(ctx, step_id1, {
            "event_info": "INFO",
            "successful": True
        })

        cpo.update_provisioning_steps(cluster.id)

        result_cluster = self.api.cluster_get(ctx, cluster.id)
        result_step = result_cluster.provision_progress[0]

        self.assertEqual(True, result_step.successful)
        self.assertEqual(2, result_step.completed)

        # check updating in case of failed provision step

        step_id2 = self.api.cluster_provision_step_add(ctx, cluster.id, {
            "step_name": "some_name1",
            "total": 2,
        })

        self.api.cluster_event_add(ctx, step_id2, {
            "event_info": "INFO",
            "successful": False,
        })

        cpo.update_provisioning_steps(cluster.id)

        result_cluster = self.api.cluster_get(ctx, cluster.id)

        for step in result_cluster.provision_progress:
            if step.id == step_id2:
                self.assertEqual(False, step.successful)

        # check that it's possible to add provision step after failed step

        step_id3 = self.api.cluster_provision_step_add(ctx, cluster.id, {
            "step_name": "some_name",
            "total": 2,
        })

        self.assertEqual(
            step_id3, cpo.get_current_provisioning_step(cluster.id))

    def test_get_cluster_events(self):
        ctx, cluster = self._make_sample()

        step_id1 = self.api.cluster_provision_step_add(ctx, cluster.id, {
            'step_name': "some_name1",
        })
        step_id2 = self.api.cluster_provision_step_add(ctx, cluster.id, {
            'step_name': "some_name",
        })

        self.api.cluster_event_add(ctx, step_id1, {
            "event_info": "INFO",
            'successful': True,
        })

        self.api.cluster_event_add(ctx, step_id2, {
            "event_info": "INFO",
            'successful': True,
        })

        self.assertEqual(2, len(cpo.get_cluster_events(cluster.id)))
        self.assertEqual(1, len(cpo.get_cluster_events(cluster.id, step_id1)))
        self.assertEqual(1, len(cpo.get_cluster_events(cluster.id, step_id2)))

    def _make_checks(self, instance, sleep=True):
        ctx = context.ctx()

        if sleep:
            context.sleep(2)

        current_instance_info = ctx.current_instance_info
        expected = [None, instance.id, instance.name, None]
        self.assertEqual(expected, current_instance_info)

    def test_instance_context_manager(self):
        fake_instances = [FakeInstance() for _ in range(50)]

        # check that InstanceContextManager works fine sequentially

        for instance in fake_instances:
            info = [None, instance.id, instance.name, None]
            with context.InstanceInfoManager(info):
                self._make_checks(instance, sleep=False)

        # check that InstanceContextManager works fine in parallel

        with context.ThreadGroup() as tg:
            for instance in fake_instances:
                info = [None, instance.id, instance.name, None]
                with context.InstanceInfoManager(info):
                    tg.spawn("make_checks", self._make_checks, instance)
