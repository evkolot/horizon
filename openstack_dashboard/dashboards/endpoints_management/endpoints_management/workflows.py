# Copyright (C) 2016 Universidad Politecnica de Madrid
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

import logging

from horizon import workflows
from horizon import forms

LOG = logging.getLogger('idm_logger')

class UpdateEndpointsAction(workflows.Action):
    name = forms.CharField(max_length=255,
                           label= "Testing Name",
                           help_text="",
                           required=True)

    def handle(self, request, data):
        pass

class UpdateEndpointsStep(workflows.Step):
    action_class = UpdateEndpointsAction
    contributes = ("region_id",)
    template_name = "endpoints_management/endpoints_management/_workflow_step_update_endpoints.html"
    
    def contribute(self, data, context):
        region_id = context['region_id']
        return context

class EndpointsWorkflow(workflows.Workflow):
    default_steps = (UpdateEndpointsStep,)
    slug = 'update_endpoints'

    def handle(self, request, data):
        pass
