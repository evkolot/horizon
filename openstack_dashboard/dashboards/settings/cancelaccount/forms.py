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

class BasicCancelForm(forms.SelfHandlingForm):

    def handle(self, request, data):
        try:
            user = api.keystone.user_get(request, request.user.id)
            delete_orgs = self._get_orgs_to_delete(request, user)
            delete_apps = self._get_apps_to_delete(request, user)

            
            # NOTE(garcianavalon) here we need to use the idm
            # account to delete all the stuff to avoid problems
            # with user rights, tokens, etc.

            for org_id in delete_orgs:
                fiware_api.keystone.project_delete(request, org_id)

            for app_id in delete_apps:
                fiware_api.keystone.application_delete(request, 
                    app_id, use_idm_account=True)

            # finally delete the user
            fiware_api.keystone.user_delete(request, user.id)

            messages.success(request, ("Account canceled succesfully"))
            return shortcuts.redirect('logout')

        except Exception as e:   
            exceptions.handle(request,
                              ('Unable to cancel account.'))
            LOG.error(e)
            return False

    def _get_orgs_to_delete(self, request, user):
        # TODO(garcianavalon) not working, fix it
        # all orgs where the user is the only owner
        # and user specific organizations
        delete_orgs = []
        user_specific_orgs = [
            user.default_project_id,
            user.cloud_project_id
        ]
        owner_role = fiware_api.keystone.get_owner_role(request)
        # NOTE(garcianavalon) the organizations the user is owner
        # are already in the request object by the middleware
        for org in request.organizations:
            if org.id in user_specific_orgs:
                delete_orgs.append(org.id)
                continue

            owners = set([
                a.user_id for a 
                in api.keystone.role_assignments_list(
                    request,
                    role=owner_role.id,
                    project=org.id)
                if hasattr(a, 'user_id')
            ])

            if len(owners) == 1:
                delete_orgs.append(org.id)

        return delete_orgs

    def _get_apps_to_delete(self, request, user):
        # TODO(garcianavalon) not working, fix it
        # all the apps where the user is the only provider
        delete_apps = []
        provider_role = fiware_api.keystone.get_provider_role(request)

        provided_apps = [
            a.application_id for a
            in fiware_api.keystone.user_role_assignments(request, 
                                                         user=user.id)
            if a.role_id == provider_role.id
        ]

        for app_id in provided_apps:
            providers = set([
                a.user_id for a 
                in fiware_api.keystone.user_role_assignments(
                    request,
                    application=app_id)
                if a.role_id == provider_role.id
            ])

            if len(providers) == 1:
                delete_apps.append(app_id)

        return delete_apps