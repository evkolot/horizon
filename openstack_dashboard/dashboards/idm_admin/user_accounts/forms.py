# Copyright (C) 2014 Universidad Politecnica de Madrid
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

from django import forms
from django import shortcuts
from django.conf import settings

from horizon import exceptions
from horizon import forms
from horizon import messages

from openstack_dashboard import api
from openstack_dashboard import fiware_api

from openstack_dashboard.dashboards.idm \
    import utils as idm_utils

LOG = logging.getLogger('idm_logger')

def get_account_types():
    """Loads all FIWARE account roles."""
    choices = []
    # TODO(garcianavalon) find a better solution to this
    account_roles = [
        fiware_api.keystone.get_basic_role(None,
            use_idm_account=True),
        fiware_api.keystone.get_trial_role(None,
            use_idm_account=True),
        fiware_api.keystone.get_community_role(None,
            use_idm_account=True),
    ]

    for role in account_roles:
        if not role:
            continue
        choices.append((role.id, role.name)) 

    return choices

def get_regions():
    """Loads all posible regions for the FIWARE cloud portal"""
    choices = [
        ('', 'No region'),
    ]
    return choices

class UpdateAccountForm(forms.SelfHandlingForm):
    user_id = forms.CharField(
        widget=forms.HiddenInput(), required=True)

    account_type = forms.ChoiceField(
        required=True,
        label=("Account type"),
        choices=get_account_types())

    region = forms.ChoiceField(
        label=("Cloud region"),
        choices=get_regions())

    def clean_account_type(self):
        """ Validate that there are trial users accounts left"""
        account_type = self.cleaned_data['account_type']
        if (account_type != fiware_api.keystone.get_trial_role(
                self.request)):
            return account_type

        trial_users = len(
            fiware_api.keystone.get_trial_role_assignments(self.request))
        if trial_users >= getattr(settings, 'MAX_TRIAL_USERS', 0):
            raise forms.ValidationError(
                'There are no trial accounts left.',
                code='invalid')
        
        return account_type

    def handle(self, request, data):
        try:
            user_id = data['user_id']
            role_id = data['account_type']

            self._clean_roles(request, )

            # grant the selected role
            api.keystone.add_domain_user_role(request,
                user=user_id, role=role_id)


        except Exception:
            raise

    def _clean_roles(self, request, user_id):
        account_roles = [
            fiware_api.keystone.get_basic_role(request),
            fiware_api.keystone.get_trial_role(request),
            fiware_api.keystone.get_community_role(request),
        ]
        for role in account_roles:
            if not role:
                continue

            api.keystone.remove_domain_user_role(request,
                user=user_id, role=role.id)


class FindUserByEmailForm(forms.SelfHandlingForm):
    email = forms.EmailField(label=("E-mail"),
                             required=True)

    def handle(self, request, data):
        try:
            user = api.keystone.user_list(request,
                filters={'name':data['email']})
            if not user:
                return False

            # NOTE(garcianavalon) there is no users.find binding
            # in api.keystone so we use list filtering
            # because we are using the list filtering option
            # we need to unpack it.
            request.session['account_user'] = (
                idm_utils.PickleObject(**user[0].__dict__))

            return shortcuts.redirect(
                'horizon:idm_admin:user_accounts:update')

        except Exception:
            messages.error(request, 
                'An unexpected error ocurred. Try again later')