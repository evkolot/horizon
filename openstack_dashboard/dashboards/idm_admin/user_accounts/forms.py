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

def get_account_choices():
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
    regions = fiware_api.keystone.region_list(None, use_idm_account=True)
    for region in regions:
        choices.append((region.id, region.id))
    return choices

class UpdateAccountForm(forms.SelfHandlingForm):
    user_id = forms.CharField(
        widget=forms.HiddenInput(), required=True)

    account_type = forms.ChoiceField(
        required=True,
        label=("Account type"),
        choices=get_account_choices())

    region = forms.ChoiceField(
        required=False,
        label=("Cloud region"),
        choices=get_regions())

    def clean_account_type(self):
        """ Validate that there are trial users accounts left"""
        account_type = self.cleaned_data['account_type']
        if (account_type != fiware_api.keystone.get_trial_role(
                self.request).id):
            return account_type

        if self._max_trial_users_reached(self.request):
            raise forms.ValidationError(
                'There are no trial accounts left.',
                code='invalid')
        
        return account_type

    def clean(self):
        cleaned_data = super(UpdateAccountForm, self).clean()

        # TODO(garcianavalon) find a better solution to this
        role_name = next(choice[1] for choice in get_account_choices()
            if choice[0] == cleaned_data['account_type'])
        
        region = cleaned_data.get('region', None)

        allowed_regions = getattr(settings, 'FIWARE_ALLOWED_REGIONS', None)
        if not allowed_regions:
            raise forms.ValidationError(
                'FIWARE_ALLOWED_REGIONS is not properly configured',
                code='invalid')
        
        if not allowed_regions[role_name]:
            if region:
                messages.info(self.request, 
                    'The account type selected is not allowed any region')

            cleaned_data['region'] = None
            return cleaned_data

        if not region in allowed_regions[role_name]:
            if not region:
                msg = 'You must choose a region for this accout type.'
            else:
                msg = 'The region {0} is not allowed for that account type.'.format(region)
            raise forms.ValidationError(
                msg,
                code='invalid')

        return cleaned_data


    def _max_trial_users_reached(self, request):
        trial_users = len(
            fiware_api.keystone.get_trial_role_assignments(request))
        return trial_users >= getattr(settings, 'MAX_TRIAL_USERS', 0)

    def handle(self, request, data):
        try:
            user_id = data['user_id']
            role_id = data['account_type']
            region_id = data['region']

            activate_cloud = (
                role_id != fiware_api.keystone.get_basic_role(
                    request).id
            )

            self._update_account(request, user_id, role_id,
                region_id=region_id, activate_cloud=activate_cloud)

            messages.success(request,
                'User account upgraded succesfully')
        except Exception:
            raise

    def _update_account(self, request, user_id, role_id, 
                         region_id=None, activate_cloud=False):
        user = api.keystone.user_get(request, user_id)

        # clean previous status
        self._clean_roles(request, user_id)
        self._clean_endpoint_groups(request, user.cloud_project_id)

        # grant the selected role
        api.keystone.add_domain_user_role(request,
            user=user_id, role=role_id, domain='default')

        # cloud
        if activate_cloud:
            self._activate_cloud(request, user_id, user.cloud_project_id)
        else:
            self._deactivate_cloud(request, user_id, user.cloud_project_id)
        
        # assign endpoint group for the selected region
        if region_id:
            pass

        # done!

    def _clean_roles(self, request, user_id):
        # TODO(garcianavalon) find a better solution to this
        user_roles = api.keystone.role_assignments_list(self.request, 
            user=user_id, domain='default')
        account_roles = [
            fiware_api.keystone.get_basic_role(None,
                use_idm_account=True).id,
            fiware_api.keystone.get_trial_role(None,
                use_idm_account=True).id,
            fiware_api.keystone.get_community_role(None,
                use_idm_account=True).id,
        ]
        current_account = next((a.role['id'] for a in user_roles 
            if a.role['id'] in account_roles), None)
        if current_account:
            api.keystone.remove_domain_user_role(request,
                user=user_id, role=current_account, domain='default')

    def _activate_cloud(self, request, user_id, cloud_project_id):
        # grant purchaser in cloud app to cloud org
        # and Member to the user
        purchaser = fiware_api.keystone.get_purchaser_role(request)
        cloud_app = fiware_api.keystone.get_fiware_cloud_app(request)
        cloud_role = fiware_api.keystone.get_default_cloud_role(request, cloud_app)
        
        fiware_api.keystone.add_role_to_organization(
            request,
            role=purchaser.id,
            organization=cloud_project_id,
            application=cloud_app.id)

        fiware_api.keystone.add_role_to_user(
            request,
            role=cloud_role.id,
            user=user_id,
            organization=cloud_project_id,
            application=cloud_app.id)

    def _deactivate_cloud(self, request, user_id, cloud_project_id):
        # remove purchaser from user cloud project
        purchaser = fiware_api.keystone.get_purchaser_role(request)
        cloud_app = fiware_api.keystone.get_fiware_cloud_app(request)

        fiware_api.keystone.remove_role_from_user(
            request,
            role=purchaser.id,
            user=user_id,
            organization=cloud_project_id,
            application=cloud_app.id)

    def _clean_endpoint_groups(self, request, cloud_project_id):
        pass

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
            user = user[0]
            return shortcuts.redirect(
                'horizon:idm_admin:user_accounts:update',
                user_id=user.id)

        except Exception:
            messages.error(request, 
                'An unexpected error ocurred. Try again later')