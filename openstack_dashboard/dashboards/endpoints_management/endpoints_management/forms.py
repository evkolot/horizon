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
import uuid

from horizon import forms
from horizon import messages
from horizon import exceptions

from django import shortcuts
from django.core.urlresolvers import reverse_lazy

from openstack_dashboard.fiware_api import keystone

LOG = logging.getLogger('idm_logger')


class UpdateEndpointsForm(forms.SelfHandlingForm):
    service_name = '' # will be initialized in __init__
    action = reverse_lazy('horizon:endpoints_management:endpoints_management:edit_service', service_name)
    description = 'Update Service Endpoints'
    template = 'endpoints_management/endpoints_management/_endpoints.html'


    def __init__(self, *args, **kwargs):
        service = kwargs.pop('service')
        self.service_name = service.name
        self.service_type = getattr(service, 'type', None)
        self.service_description = getattr(service, 'description', None)
        self.service_id = service.id

        self.endpoints_list = kwargs.pop('endpoints_list')

        super(UpdateEndpointsForm, self).__init__(*args, **kwargs)

        fields = {}
        initial = {}

        for region in self.request.session['endpoints_allowed_regions']:
            for interface in ['public', 'internal', 'admin']:
                field_ID = '_'.join([self.service_name, region.lower(), interface])
                fields[field_ID] = forms.CharField(label=interface.capitalize(),
                                                   required=True,
                                                   widget=forms.TextInput(
                                                   attrs={'data-service-name': self.service_name,
                                                          'data-endpoint-interface': interface,
                                                          'data-endpoint-region': region
                                                   }))
        for endpoint in self.endpoints_list:
            field_ID = '_'.join([self.service_name, endpoint.region.lower(), endpoint.interface])
            initial[field_ID] = endpoint.url

        self.fields = fields
        self.initial = initial

    def handle(self, request, data):
        is_new_service = False
        
        for field_ID, new_url in data.iteritems():
            service_name, region, interface = field_ID.split('_')

            endpoint = next((e for e in self.endpoints_list if e.region_id == region.capitalize() and e.interface == interface), None)
            if not endpoint:
                is_new_service = True
                keystone.endpoint_create(request, service=self.service_id, url=new_url, interface=interface, region=region)
            elif new_url != '' and new_url != endpoint.url:
                keystone.endpoint_update(request, endpoint_id=endpoint.id, endpoint_new_url=new_url)

        self._create_endpoint_group_for_region(request)
        if (is_new_service):
            self._create_service_account(request)

        # display success messages
        messages.success(request, 'Endpoints updated for your region.')

        return shortcuts.redirect('horizon:endpoints_management:endpoints_management:index')


    def _create_endpoint_group_for_region(self, request):
        for region in request.session['endpoints_allowed_regions']:
            endpoint_group_for_region = [
                eg for eg in keystone.endpoint_group_list(request)
                if eg.filters.get('region_id', None) == region
            ]

            if not endpoint_group_for_region:
                LOG.debug('Creating endpoint_group for region {0}'.format(region))
                keystone.endpoint_group_create(
                    request=request,
                    name=region + ' Region Group',
                    region_id=region)


    def _create_service_account(self, request):
        region = request.session['endpoints_user_region']
        password = uuid.uuid4().hex

        service_account = keystone.create_service_account(request=request,
                                                          password=password,
                                                          service=self.service_name,
                                                          region=region)

        request.session['new_service_password'] = password
        request.session['new_service_name'] = self.service_name

