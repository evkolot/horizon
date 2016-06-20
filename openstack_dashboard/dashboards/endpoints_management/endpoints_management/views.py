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

from django.shortcuts import redirect
from django.utils import simplejson
from django.forms.formsets import formset_factory

from openstack_dashboard import fiware_api

from horizon import forms
from horizon import messages
from horizon import exceptions
from openstack_dashboard.dashboards.endpoints_management.endpoints_management import forms as endpoints_forms
from openstack_dashboard.dashboards.endpoints_management import utils

from keystoneclient.openstack.common.apiclient import exceptions as ks_exceptions


LOG = logging.getLogger('idm_logger')

# NOTE @(federicofdez) Move to local_settings.py
AVAILABLE_SERVICES = [
    {'name': 'Swift',
     'type': 'Object storage',
     'description': 'Stores and retrieves arbitrary unstructured data objects via a RESTful, HTTP based API. It is highly fault tolerant with its data replication and scale out architecture. Its implementation is not like a file server with mountable directories.'},
    {'name': 'Nova',
     'type': 'Compute',
     'description': 'Manages the lifecycle of compute instances in an OpenStack environment. Responsibilities include spawning, scheduling and decomissioning of machines on demand.'},
    {'name': 'Neutron',
     'type': 'Networking',
     'description': 'Enables network connectivity as a service for other OpenStack services, such as OpenStack Compute. Provides an API for users to define networks and the attachments into them. Has a pluggable architecture that supports many popular networking vendors and technologies.'},
    {'name': 'Cinder',
     'type': 'Block storage',
     'description': 'Provides persistent block storage to running instances. Its pluggable driver architecture facilitates the creation and management of block storage devices.'},
    {'name': 'Glance',
     'type': 'Image service',
     'description': 'Stores and retrieves virtual machine disk images. OpenStack Compute makes use of this during instance provisioning.'},
]

class EndpointsView(forms.ModalFormView):
    form_class = endpoints_forms.UpdateEndpointsForm
    template_name = 'endpoints_management/endpoints_management/endpoints.html'

    def get_form_kwargs(self):
        kwargs = super(EndpointsView, self).get_form_kwargs()

        kwargs['services'] = fiware_api.keystone.service_list(self.request)
        kwargs['regions'] = fiware_api.keystone.region_list(self.request)
        kwargs['endpoints'] = []

        endpoints = fiware_api.keystone.endpoint_list(self.request)
        for region in self.request.session['endpoints_allowed_regions']:
            region_endpoints = [e for e in endpoints if e.region_id == region]
            kwargs['endpoints'] += region_endpoints

        return kwargs

    def get_context_data(self, **kwargs):
        context = super(EndpointsView, self).get_context_data(**kwargs)
        
        highlighted_service = self.kwargs.get('service_name', None)
        if highlighted_service:
            context['highlighted_service'] = highlighted_service

        context['available_services'] = AVAILABLE_SERVICES
        context['endpoints_user_region'] = self.request.session['endpoints_user_region']
        context['endpoints_allowed_regions'] = self.request.session['endpoints_allowed_regions']

        new_service_name = self.request.session.pop('new_service_name', None)
        new_services = self.request.session.get('new_services', None)

        context['new_services'] = new_services
        context['new_service_name'] = new_service_name
        context['new_service_password'] = self.request.session.pop('new_service_password', None)

        return context

    def dispatch(self, request, *args, **kwargs):
        if not utils.can_manage_endpoints(request):
            return redirect('horizon:user_home')
        return super(EndpointsView, self).dispatch(request, *args, **kwargs)            


def enable_service_view(request, service_name):
    if not utils.can_manage_endpoints(request):
        return redirect('horizon:user_home')
    
    region = request.session['endpoints_user_region']
    password = uuid.uuid4().hex
    try:
        # try to retrieve service
        services_list = fiware_api.keystone.service_list(request)
        service = next((s for s in services_list if s.name == service_name), None)

        if not service:
            messages.error(request, ('Unable to enable {0} service for your region (service not found).'.format(service_name.capitalize())))
        else:
            service_account = fiware_api.keystone.create_service_account(request=request,
                                                                         password=password,
                                                                         service=service_name,
                                                                         region=region)

            request.session['new_service_password'] = password
            request.session['new_service_name'] = service_name

            if 'new_services' not in request.session:
                request.session['new_services'] = []
            request.session['new_services'].append(service_name)

            #LOG.debug('New services: {0}'.format(request.session['new_services']))
            messages.warning(request, 'Service {0} enabled. Don\'t forget to add the new endpoints.'.format(service_name.capitalize()))
    except ks_exceptions.Conflict:
        exceptions.handle(request, ('{0} service is already enabled.'.format(service_name.capitalize())))        

    return redirect('horizon:endpoints_management:endpoints_management:service', service_name)


def disable_service_view(request, service_name):
    if not utils.can_manage_endpoints(request):
        return redirect('horizon:user_home')

    region = request.session['endpoints_user_region']

    try:
        LOG.debug('Disabling service {0}...'.format(service_name))
        
        # delete service account
        fiware_api.keystone.delete_service_account(request, service=service_name, region=region)

        new_services = request.session.get('new_services', None)
        if new_services and service_name in new_services:
            new_services.pop(new_services.index(service_name))
            request.session['new_services'] = new_services
        else:
            # delete service endpoints (if any)
            services = fiware_api.keystone.service_list(request)
            current_service = next((s for s in services if s.name == service_name), None)
            for region in request.session['endpoints_allowed_regions']:
                for endpoint in fiware_api.keystone.endpoint_list(request, region=region, service_id=current_service.id):
                    fiware_api.keystone.endpoint_delete(request, endpoint)

        messages.success(request,
                         ('Service %s was successfully disabled.')
                         % service_name.capitalize())

    except Exception:
        exceptions.handle(request, ('Unable to disable service.'))

    return redirect('horizon:endpoints_management:endpoints_management:service', service_name)


def reset_service_password_view(request, service_name):
    if not utils.can_manage_endpoints(request):
        return redirect('horizon:user_home')

    region = request.session['endpoints_user_region']
    password = uuid.uuid4().hex
    service_account = fiware_api.keystone.reset_service_account(request=request, 
                                                                service=service_name,
                                                                region=region,
                                                                password=password)
    request.session['new_service_password'] = password
    request.session['new_service_name'] = service_name
    messages.success(request, 'Password for service {0} was reset.'.format(service_name.capitalize()))

    return redirect('horizon:endpoints_management:endpoints_management:service', service_name)