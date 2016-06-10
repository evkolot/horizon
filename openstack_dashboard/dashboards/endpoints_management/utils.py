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
    if _is_current_user_keystone_administrator(request):
        # save region in session
        request.session['endpoints_region'] = user.id.split('admin-')[1]
        return True
    else:
        return False

def _is_current_user_keystone_administrator(request):
    """ Checks if the current user is an administrator (in other words, if they have the
    admin role AND if their username starts with 'admin')
    """

    if 'admin' in request.user.id and request.user.id.index('admin') == 0:
        return _is_user_administrator(request, request.user.id)
    return False

def _is_user_administrator(request, user_id):
    admin_role = fiware_api.keystone.get_admin_role(request)
    user = fiware_api.keystone.user_get(request, user_id)
    return len(fiware_api.keystone.role_assignments_list(request, user=user, role=admin_role)) > 0
