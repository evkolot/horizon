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
    
    if not is_current_user_keystone_administrator(request):
        return False
    
    _store_allowed_regions(request)
    return True

def is_current_user_keystone_administrator(request):
    """ Checks if the current user is an administrator (in other words, if they have the
    admin role AND if their username starts with 'admin')
    """

    user = fiware_api.keystone.user_get(request, request.user.id)
    if 'admin' in user.name and user.name.index('admin') == 0:
        return _is_user_administrator(request, request.user.id)
    return False

def _is_user_administrator(request, user_id):
    admin_role = fiware_api.keystone.get_admin_role(request)
    user = fiware_api.keystone.user_get(request, user_id)
    return len(fiware_api.keystone.role_assignments_list(request, user=user, role=admin_role)) > 0

def _store_allowed_regions(request):
    # save allowed regions in session
    user = fiware_api.keystone.user_get(request, request.user.id)
    user_region = user.name.split('admin-')[1]
    regions = fiware_api.keystone.region_list(request)
    allowed_regions = [r.id for r in regions if user_region in r.id.lower()]

    request.session['endpoints_allowed_regions'] = allowed_regions
    request.session['endpoints_user_region'] = user_region

def _is_service_account_shared(request, service_account_name):
    service, region = service_account_name.split('-')

    # let's check first if the service_account could be potentially shared
    # i.e. there is another service of the same type
    services_IDs = [s.id for s in fiware_api.keystone.service_list(request) if service in s.name]
    if len(services_IDs) < 1:
        return False

    # let's check now if more than one of those services is enabled
    endpoints = [e for e in fiware_api.keystone.endpoint_list(request) if e.region_id == region.capitalize() and \
                                                                           e.service_id in services_IDs]
    if len(endpoints) > 3:
        return True
    
    return False
