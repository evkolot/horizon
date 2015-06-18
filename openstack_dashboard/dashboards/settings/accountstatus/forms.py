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
from django.conf import settings

from horizon import exceptions
from horizon import forms
from horizon import messages
from horizon.utils import functions as utils

from openstack_dashboard import api
from openstack_dashboard import fiware_api
from openstack_dashboard.dashboards.idm_admin.user_accounts \
    import forms as user_accounts_forms


LOG = logging.getLogger('idm_logger')

class UpgradeForm(forms.SelfHandlingForm, user_accounts_forms.UserAccountsLogicMixin):

    def handle(self, request, data):

        try:
            user_id = request.user.id
            role_id = fiware_api.keystone.get_trial_role(request).id
            regions = ['Spain2']
            default_durations = getattr(settings, 'FIWARE_DEFAULT_DURATION', None)
            if default_durations:
                duration = default_durations['trial']
            else:
                duration = 14

            self.update_account(request, user_id, role_id, regions, duration)
            messages.success(request, 'Updated account to Trial succesfully.')

            return shortcuts.redirect('logout')
        except Exception:
            messages.error(request, 'An error ocurred. Please try again later.')

        

        