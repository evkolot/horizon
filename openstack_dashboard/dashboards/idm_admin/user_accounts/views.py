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
from django.conf import settings
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
        context['user'] = fiware_api.keystone.user_get(self.request, 
            self.kwargs['user_id'])

        context['allowed_regions'] = json.dumps(
            getattr(settings, 'FIWARE_ALLOWED_REGIONS', None))
        return context

    def get_initial(self):
        initial = super(UpdateAccountView, self).get_initial()
        user_id = self.kwargs['user_id']
        user_roles = fiware_api.keystone.role_assignments_list(self.request, 
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
            #'regions': '',
            'account_type': current_account,
        })
        return initial


class UpdateAccountEndpointView(View, user_accounts_forms.UserAccountsLogicMixin):
    """ Upgrade account logic with out the form"""
    http_method_names = ['post']
    use_idm_account = True
    
    @csrf_exempt
    def dispatch(self, request, *args, **kwargs):
        # Check there is a valid keystone token in the header
        token = request.META.get('HTTP_X_AUTH_TOKEN', None)
        if not token:
            return http.HttpResponse('Unauthorized', status=401)

        response = fiware_api.keystone.validate_keystone_token(request, token)
        if response.status_code != 200:
            return http.HttpResponse('Unauthorized', status=401)
        return super(UpdateAccountEndpointView, self).dispatch(request, *args, **kwargs)


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

            regions = data.get('regions', None)

            if (role_id != fiware_api.keystone.get_basic_role(
                    request).id
                and not regions):

                return http.HttpResponseBadRequest()

            self.update_account(request, user_id, role_id, regions)

            return http.HttpResponse()

        except Exception:
            return http.HttpResponseServerError()
