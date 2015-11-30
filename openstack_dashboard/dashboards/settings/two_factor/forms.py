# Copyright (C) 2014 Universidad Politecnica de Madrid
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

import logging

from django import shortcuts

from horizon import exceptions
from horizon import forms
from horizon import messages

from openstack_dashboard import api
from openstack_dashboard import fiware_api

LOG = logging.getLogger('idm_logger')

class ManageTwoFactorForm(forms.SelfHandlingForm):
    action = 'two_factor/'
    description = 'Manage two factor authentication'
    template = 'settings/multisettings/_collapse_form.html'

    def handle(self, request, data):
        try:
            LOG.info('enabled two factor authentication')

            messages.success(request, "success")
            return True

        except Exception as e:   
            exceptions.handle(request, 'error')
            LOG.error(e)
            return False
