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

from horizon import forms
from horizon import messages
from horizon import exceptions

from django.forms import ValidationError
from django import shortcuts
from django.core.urlresolvers import reverse_lazy

from openstack_dashboard.fiware_api import keystone

LOG = logging.getLogger('idm_logger')


class UpdateEndpointsForm(forms.SelfHandlingForm):
    action = reverse_lazy('horizon:endpoints_management:endpoints_management:index')
    description = 'Account status'
    template_name = 'endpoints_management/endpoints_management/_endpoints.html'

    def __init__(self, *args, **kwargs):
        self.services = kwargs.pop('services')
        self.regions = kwargs.pop('regions')
        self.endpoints = kwargs.pop('endpoints')

        super(UpdateEndpointsForm, self).__init__(*args, **kwargs)

        fields = {}
        initial = {}

        # add fields for existing endpoints, and set initial values
        for endpoint in self.endpoints:
            service_name = ''.join(service.name for service in self.services \
                if service.id == endpoint.service_id)
            fields[endpoint.id] = forms.CharField(label=service_name + '_' + endpoint.interface,
                                                  required=False,
                                                  widget=forms.TextInput(
                                                  attrs={'data-service-name': service_name,
                                                         'data-endpoint-interface': endpoint.interface,
                                                         'data-endpoint-region': endpoint.region
                                                  }))
            initial[endpoint.id] = endpoint.url

        # add blank fields for new service, if any
        if 'new_services' in self.request.session and len(self.request.session['new_services']) > 0:
            for service in self.request.session['new_services']:
                for interface in ['public', 'admin', 'internal']:
                    for region in self.request.session['endpoints_allowed_regions']:
                        endpoint_id = service + '_' + interface + '_' + region
                        fields[endpoint_id] = forms.CharField(label=endpoint_id,
                                                              required=False,
                                                              widget=forms.TextInput(
                                                              attrs={'data-service-name': service,
                                                                     'data-endpoint-interface': interface,
                                                                     'data-endpoint-region': region
                                                              }))

        self.fields = fields
        self.initial = initial

    def clean(self):
        cleaned_data = super(UpdateEndpointsForm, self).clean()
        
        # endpoints may arrive in any order, so we need to count them in order 
        # to check if all of them are empty (delete service) or just some of 
        # them (validation error)

        empty_services = []
        new_data = {}

        for endpoint_id, new_url in cleaned_data.iteritems():
            if new_url == u'':
                service_id = endpoint_id.split('_')[0] if '_' in endpoint_id else keystone.endpoint_get(self.request, endpoint_id).service_id
                empty_services.append(service_id)
            else:
                new_data[endpoint_id] = 'http://' + new_url
        
        for service_id in set(empty_services):
            if empty_services.count(service_id) < 3*len(self.request.session['endpoints_allowed_regions']):
                service = keystone.service_get(self.request, service_id)
                raise ValidationError(('All interfaces for {0} service must be provided'.format(
                    service.name.capitalize() if service else service_id.capitalize())))

        # save endpoints to be deleted when handling form
        # do not save endpoints for newly created services, since they don't exist yet
        self.empty_endpoints = [e for e, url in cleaned_data.iteritems() if url == u'' and '_' not in e ]
        
        return new_data

    def handle(self, request, data):
        new_services = set()

        # create and update endpoints
        for endpoint_id, new_url in data.iteritems():
            if '_' in endpoint_id: # new endpoint ID will look like "service_interface"
                service_name, interface, region = endpoint_id.split('_')
                service = next((s for s in self.services if s.name == service_name), None)
                region = next((r for r in self.regions if r.id == region), None)
                if not service:
                    #LOG.debug ('Service {0} is not created, skipping this endpoint'.format(service_name))
                    messages.error(request, 
                        'Unable to store {0} endpoint for {1} service (service not found).'.format(interface, service_name))
                    continue
                keystone.endpoint_create(request, service=service, url=new_url, interface=interface, region=region)
                new_services.add(service_name)

            # existing endpoint ID can be used to retrieve endpoint object
            else:
                endpoint = keystone.endpoint_get(request, endpoint_id)
                if new_url != '' and new_url != endpoint.url:
                    keystone.endpoint_update(request, endpoint_id=endpoint_id, endpoint_new_url=new_url)

        self._delete_empty_endpoints(request)
        self._create_endpoint_group_for_region(request)

        for service in new_services:
            request.session['new_services'].pop(request.session['new_services'].index(service))

        # display success messages
        messages.success(request, 'Endpoints updated for your region.')

        return shortcuts.redirect('horizon:endpoints_management:endpoints_management:index')

    def _delete_empty_endpoints(self, request):
        if getattr(self, 'empty_endpoints'):
            for endpoint_id in self.empty_endpoints:
                keystone.endpoint_delete(request, endpoint_id)
            messages.success(request, 'Blank endpoints deleted.')


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

