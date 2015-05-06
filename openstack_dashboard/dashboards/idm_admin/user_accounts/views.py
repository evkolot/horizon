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
import json

from django import http
from django.shortcuts import redirect
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import View

from horizon import forms

from openstack_dashboard import api
from openstack_dashboard import fiware_api
from openstack_dashboard.dashboards.idm_admin.user_accounts \
    import forms as user_accounts_forms
from openstack_dashboard.dashboards.idm_admin \
    import utils as idm_admin_utils

LOG = logging.getLogger('idm_logger')

class FindUserView(forms.ModalFormView):
    form_class = user_accounts_forms.FindUserByEmailForm
    template_name = 'idm_admin/user_accounts/index.html'

    def dispatch(self, request, *args, **kwargs):
        if idm_admin_utils.is_current_user_administrator(request):
            return super(FindUserView, self).dispatch(request, *args, **kwargs)
        else:
            return redirect('horizon:user_home')


class UpdateAccountView(forms.ModalFormView):
    form_class = user_accounts_forms.UpdateAccountForm
    template_name = 'idm_admin/user_accounts/update.html'
    success_url = 'horizon:idm_admin:user_accounts:update'

    def dispatch(self, request, *args, **kwargs):
        if idm_admin_utils.is_current_user_administrator(request):
            return super(UpdateAccountView, self).dispatch(request, *args, **kwargs)
        else:
            return redirect('horizon:user_home')

    def get_context_data(self, **kwargs):
        context = super(UpdateAccountView, self).get_context_data(**kwargs)
        context['user'] = api.keystone.user_get(self.request, 
            self.kwargs['user_id'])
        return context

    def get_initial(self):
        initial = super(UpdateAccountView, self).get_initial()
        user_id = self.kwargs['user_id']
        user_roles = api.keystone.role_assignments_list(self.request, 
            user=user_id, domain='default')
        # TODO(garcianavalon) find a better solution to this
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

        initial.update({
            'user_id': user_id,
            #'region': '',
            'account_type': current_account,
        })
        return initial


class UpdateAccountEndpointView(View, user_accounts_forms.UserAccountsLogicMixin):
    """ Upgrade account logic with out the form"""
    http_method_names = ['post', 'get']
    use_idm_account = True
    
    @csrf_exempt
    def dispatch(self, request, *args, **kwargs):
        return super(UpdateAccountEndpointView, self).dispatch(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        try:
            import os
            __location__ = os.path.realpath(
                os.path.join(os.getcwd(), os.path.dirname(__file__)))
            categories = json.load(open(os.path.join(__location__, 'categories.json')))
            for data in categories:
                user_id = data['user_id']
                role_id = data['role_id']
                region_id = data.get('region_id', None)
                errors = []
                if (role_id == fiware_api.keystone.get_trial_role(
                        request, use_idm_account=True).id
                    and not region_id):

                    region_id = 'Spain2'

                if (role_id == fiware_api.keystone.get_community_role(
                        request, use_idm_account=True).id
                    and not region_id):

                    errors.append('ERROR: ' + user_id + ' community with no region')
                    

                self.update_account(request, user_id, role_id, region_id)

            return http.HttpResponse(content='errors')

        except Exception:
            return http.HttpResponseServerError(content="ERROR 500")
    def post(self, request, *args, **kwargs):
        try:
            data = json.loads(request.body)
            user_id = data['user_id']
            role_id = data['role_id']

            if (role_id == fiware_api.keystone.get_trial_role(
                request).id):

                trial_left = self._max_trial_users_reached(request)
                if not trial_left:
                    return http.HttpResponseNotAllowed()

            region_id = data.get('region_id', None)

            if (role_id != fiware_api.keystone.get_basic_role(
                    request).id
                and not region_id):

                return http.HttpResponseBadRequest()

            self.update_account(request, user_id, role_id, region_id)

            return http.HttpResponse()

        except Exception:
            return http.HttpResponseServerError()
