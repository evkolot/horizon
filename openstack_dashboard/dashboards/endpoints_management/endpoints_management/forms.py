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
from django.template.defaultfilters import register
from django.core.urlresolvers import reverse_lazy
from django.utils.datastructures import SortedDict

from keystoneclient import exceptions as ks_exceptions

from openstack_dashboard.fiware_api import keystone
from openstack_dashboard.dashboards.endpoints_management import utils

LOG = logging.getLogger('idm_logger')


class UpdateEndpointsForm(forms.SelfHandlingForm):
    description = 'Update Service Endpoints'
    template = 'endpoints_management/endpoints_management/_endpoints.html'

    def __init__(self, *args, **kwargs):
        self.service = kwargs.pop('service')
        self.endpoints_list = kwargs.pop('endpoints_list')

        super(UpdateEndpointsForm, self).__init__(*args, **kwargs)

        fields = SortedDict()
        initial = {}

        for region in self.request.session['endpoints_allowed_regions']:
            for interface in ['public', 'internal', 'admin']:
                field_ID = '_'.join([self.service.name, region, interface])
                fields[field_ID] = forms.CharField(label=interface.capitalize(),
                                                   required=True,
                                                   widget=forms.TextInput(
                                                    attrs={'class': 'endpoint_input'})
                                                   )
                fields.keyOrder.append(field_ID)

        if self.endpoints_list:
            self.service_enabled = True
            for endpoint in self.endpoints_list:
                field_ID = '_'.join([self.service.name, endpoint.region, endpoint.interface])
                initial[field_ID] = endpoint.url
        else:
            self.service_enabled = False

        self.fields = fields
        self.initial = initial

        self.service_account_name = keystone.get_service_account_name(self.request,
                                                                      self.service.name,
                                                                      self.request.session['endpoints_user_region'])

    def handle(self, request, data):
        
        for field_ID, new_url in data.iteritems():
            service_name, region, interface = field_ID.split('_')

            # check if the endpoint already exists
            endpoint = next((e for e in self.endpoints_list if e.region_id == region and e.interface == interface), None)
            if not endpoint:
                # create new endpoint
                keystone.endpoint_create(request, service=self.service.id, url=new_url, interface=interface, region=region)
            elif new_url != '' and new_url != endpoint.url:
                # update endpoint
                keystone.endpoint_update(request, endpoint_id=endpoint.id, endpoint_new_url=new_url)

        self._create_endpoint_group_for_region(request)

        # create service account if it does not exist
        try:
            keystone.user_get(request, self.service_account_name)
        except ks_exceptions.NotFound:
            self._create_service_account(request)

        # display success messages
        messages.success(request, 'Endpoints updated for your region.')

        return shortcuts.redirect('horizon:endpoints_management:endpoints_management:service', self.service.name)


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
                                                          service=self.service.name,
                                                          region=region)

        request.session['new_service_password'] = password
        request.session['new_service_name'] = self.service.name

@register.filter(name='filter_region')
def filter_region(form, region_id):
    filtered_fields = SortedDict()
    
    for field in form.fields:
        service_name, region, interface = field.split('_')
        if region == region_id:
            filtered_fields[field] = form.fields[field]

    filtered_form = UpdateEndpointsForm(request=form.request,
                                        service=form.service,
                                        endpoints_list=form.endpoints_list)
    filtered_form.fields = filtered_fields
    return filtered_form
