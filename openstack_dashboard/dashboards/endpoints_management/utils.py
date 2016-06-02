# Copyright (C) 2016 Universidad Politecnica de Madrid
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

from openstack_dashboard import fiware_api

def can_manage_endpoints(request):
    # Allowed to manage endpoints if username begins with 'admin'
    user = request.user
    if 'admin' in user.id and user.id.index('admin') == 0:
        # save region in session
        request.session['endpoints_region'] = user.id.split('admin-')[1]
        return True
    else:
        return False

def is_current_user_fiware_administrator(request):
    """ Checks if the current user is an administrator (in other words, if he
    has any roles in the idm_admin application) AND if he/she is a fiware admin user
    (that is, whether their username starts with 'admin')
    """

    if 'admin' in request.user.id and request.user.id.index('admin') == 0:
        return is_user_administrator(request, request.user.id)
    return False

def is_user_administrator(request, user_id):
    idm_admin = fiware_api.keystone.get_idm_admin_app(request)
    if not idm_admin:
        return False
    user_apps = [a.application_id for a
                 in fiware_api.keystone.user_role_assignments(
                     request, user=user_id, use_idm_account=True)]
    return idm_admin.id in user_apps