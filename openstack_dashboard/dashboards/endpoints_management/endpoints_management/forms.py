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

from horizon import forms

from django import shortcuts
from django.core.urlresolvers import reverse_lazy

from openstack_dashboard.fiware_api import keystone


class UpdateEndpointsForm(forms.SelfHandlingForm):
    action = reverse_lazy('horizon:endpoints_management:endpoints_management:index')
    description = 'Account status'
    template_name = 'endpoints_management/endpoints_management/_endpoints.html'

    def __init__(self, *args, **kwargs):
        services = kwargs.pop('services')
        endpoints = kwargs.pop('endpoints')

        super(UpdateEndpointsForm, self).__init__(*args, **kwargs)

        fields = {}
        initial = {}
        for endpoint in endpoints:
            service_name = ''.join(service.name for service in services if service.id == endpoint.service_id)
            fields[endpoint.id] = forms.CharField(label=service_name + '_' + endpoint.interface,
                                                  required=False,
                                                  widget=forms.TextInput(attrs={'data-service-name': service_name,
                                                                                'data-endpoint-interface': endpoint.interface}))
            initial[endpoint.id] = endpoint.url

        self.fields = fields
        self.initial = initial

    def handle(self, request, data):
        for endpoint, url in data.iteritems():
            keystone.endpoint_update(request, endpoint_id=endpoint, endpoint_new_url=url)
        return shortcuts.redirect('horizon:endpoints_management:endpoints_management:index')

