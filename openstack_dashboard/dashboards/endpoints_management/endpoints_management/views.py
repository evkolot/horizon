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
from django.forms.formsets import formset_factory

from openstack_dashboard import fiware_api

from horizon import views
from horizon import forms
from horizon import messages
from horizon import exceptions
from openstack_dashboard.dashboards.endpoints_management.endpoints_management import forms as endpoints_forms
from openstack_dashboard.dashboards.endpoints_management import utils

from keystoneclient.openstack.common.apiclient import exceptions as ks_exceptions


LOG = logging.getLogger('idm_logger')

# NOTE @(federicofdez) Move to local_settings.py
AVAILABLE_SERVICES = {
    'swift': {'type': 'Object storage',
              'description': 'Stores and retrieves arbitrary unstructured data objects via a RESTful, HTTP based API. It is highly fault tolerant with its data replication and scale out architecture. Its implementation is not like a file server with mountable directories.'},
    'nova': {'type': 'Compute',
             'description': 'Manages the lifecycle of compute instances in an OpenStack environment. Responsibilities include spawning, scheduling and decomissioning of machines on demand.'},
    'neutron': {'type': 'Networking',
                'description': 'Enables network connectivity as a service for other OpenStack services, such as OpenStack Compute. Provides an API for users to define networks and the attachments into them. Has a pluggable architecture that supports many popular networking vendors and technologies.'},
    'cinder': {'type': 'Block storage',
               'description': 'Provides persistent block storage to running instances. Its pluggable driver architecture facilitates the creation and management of block storage devices.'},
    'glance': {'type': 'Image service',
               'description': 'Stores and retrieves virtual machine disk images. OpenStack Compute makes use of this during instance provisioning.'},
}

class ManageEndpointsView(views.APIView):
    template_name = 'endpoints_management/endpoints_management/index.html'

    def get_context_data(self, **kwargs):
        context = super(ManageEndpointsView, self).get_context_data(**kwargs)
        
        highlighted_service = self.kwargs.get('service_name', None)
        if highlighted_service:
            context['highlighted_service'] = highlighted_service

        context['endpoints_user_region'] = self.request.session['endpoints_user_region']
        context['endpoints_allowed_regions'] = self.request.session['endpoints_allowed_regions']

        context['new_service_name'] = self.request.session.pop('new_service_name', None)
        context['new_service_password'] = self.request.session.pop('new_service_password', None)

        # create forms
        services = fiware_api.keystone.service_list(self.request)
        endpoints = fiware_api.keystone.endpoint_list(self.request)

        context['endpoints_forms'] = []
        context['services'] = []
        for service in services:
            if service.name not in AVAILABLE_SERVICES.keys() or service.name == 'keystone':
                continue

            if not getattr(service, 'description', None):
                service.description = AVAILABLE_SERVICES[service.name]['description']
            
            # data needed for service endpoints form
            service_endpoints = []
            for region in self.request.session['endpoints_allowed_regions']:
                region_endpoints = [e for e in endpoints if e.region_id == region and e.service_id == service.id]
                service_endpoints += region_endpoints
            context['endpoints_forms'].append(endpoints_forms.UpdateEndpointsForm(request=self.request,
                                                                                  service=service,
                                                                                  endpoints_list=service_endpoints))
            context['services'].append(service)

        # Bootstrap classes for form rendering
        context['classes'] = {'label': 'col-sm-2',
                              'value': 'col-sm-10'}
        return context

    def dispatch(self, request, *args, **kwargs):
        if not utils.can_manage_endpoints(request):
            return redirect('horizon:user_home')
        return super(ManageEndpointsView, self).dispatch(request, *args, **kwargs)            


class UpdateEndpointsView(forms.ModalFormView):
    form_class = endpoints_forms.UpdateEndpointsForm
    template_name = 'endpoints_management/endpoints_management/endpoints.html'

    def get_form_kwargs(self):
        kwargs = super(UpdateEndpointsView, self).get_form_kwargs()

        service_name = self.kwargs.pop('service_name')
        services = fiware_api.keystone.service_list(self.request)
        service_object = next((s for s in services if s.name == service_name.lower()), None)
        
        endpoints = fiware_api.keystone.endpoint_list(self.request)
        service_endpoints = []
        for region in self.request.session['endpoints_allowed_regions']:
            region_endpoints = [e for e in endpoints if e.region_id == region and e.service_id == service_object.id]
            service_endpoints += region_endpoints

        kwargs['service'] = service_object
        kwargs['endpoints_list'] = service_endpoints
        return kwargs


def disable_service_view(request, service_name):
    if not utils.can_manage_endpoints(request):
        return redirect('horizon:user_home')

    services = fiware_api.keystone.service_list(request)
    endpoints = fiware_api.keystone.endpoint_list(request)
    region = request.session['endpoints_user_region']

    service_object = next((s for s in services if s.name == service_name), None)

    try:
        LOG.debug('Disabling service {0}...'.format(service_name))
        
        # delete service account
        fiware_api.keystone.delete_service_account(request, service=service_name, region=region)

        for endpoint in [e for e in endpoints if region.capitalize() in e.region_id and e.service_id == service_object.id]:
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
