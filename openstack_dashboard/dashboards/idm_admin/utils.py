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

from django.conf import settings

from openstack_dashboard import fiware_api


def is_current_user_administrator(request):
    """ Checks if the current user is an administrator. In other words, if he
    has any roles in the idm_admin application.
    """
    idm_admin = fiware_api.keystone.get_idm_admin_app(request)
    if not idm_admin:
        return False
    user_apps = [a.application_id for a
                 in fiware_api.keystone.user_role_assignments(
                     request, user=request.user.id)]
    return idm_admin.id in user_apps