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

from openstack_dashboard.fiware_api import keystone

from horizon import forms
from openstack_dashboard.dashboards.endpoints_management.endpoints_management import forms as endpoints_forms
from openstack_dashboard.dashboards.endpoints_management import utils


LOG = logging.getLogger('idm_logger')

# NOTE @(federicofdez) Move to local_settings.py
AVAILABLE_SERVICES = [
    {'name': 'Keystone',
     'type': 'Identity',
     'description': 'Provides an authentication and authorization service for other OpenStack services. Provides a catalog of endpoints for all OpenStack services.'},
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

        self.services = keystone.service_list(self.request)
        self.endpoints = keystone.endpoint_list(self.request, region=self.request.session['endpoints_region'])
        
        kwargs['services'] = self.services
        kwargs['endpoints'] = self.endpoints

        return kwargs

    def get_context_data(self, **kwargs):
        context = super(EndpointsView, self).get_context_data(**kwargs)

        context['available_services'] = AVAILABLE_SERVICES
        context['endpoints'] = self.endpoints
        context['endpoints_region'] = self.request.session['endpoints_region']

        services_passwords = self.request.session.pop('services_passwords', None)
        if services_passwords:
            context['services_passwords'] = simplejson.dumps(services_passwords)

        return context

    def dispatch(self, request, *args, **kwargs):
        if utils.can_manage_endpoints(request):
            return super(EndpointsView, self).dispatch(request, *args, **kwargs)
        else:
            return redirect('horizon:user_home')


class DisableServiceView(forms.ModalFormView):
    form_class = endpoints_forms.DisableServiceForm
    template_name = 'endpoints_management/endpoints_management/disable_service.html'

    def get_initial(self):
        initial_data = {
            "service_name": self.kwargs['service_name'],
        }
        return initial_data

    def dispatch(self, request, *args, **kwargs):
        if utils.can_manage_endpoints(request):
            return super(DisableServiceView, self).dispatch(request, *args, **kwargs)
        else:
            return redirect('horizon:user_home')


def enable_service_view(request, service_name):
    region = request.session['endpoints_region']
    password = uuid.uuid4().hex
    service_account = keystone.register_service(request=request,
                                                    password=password,
                                                    service=service_name,
                                                    region=region)
    request.session['services_passwords'][service_name] = password
    return redirect('horizon:endpoints_management:endpoints_management:index')