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

from horizon import exceptions

from django.conf import settings
from django.core import urlresolvers

from openstack_dashboard import api
from openstack_dashboard import fiware_api


LOG = logging.getLogger('idm_logger')
DEFAULT_ORG_MEDIUM_AVATAR = 'dashboard/img/logos/medium/group.png'
DEFAULT_APP_MEDIUM_AVATAR = 'dashboard/img/logos/medium/app.png'
DEFAULT_USER_MEDIUM_AVATAR = 'dashboard/img/logos/medium/user.png'

def filter_default(items):
    """Remove from a list the automated created project for a user. This project
    is created during the user registration step and is needed for the user to be
    able to perform operations in the cloud, as a work around the Keystone-OpenStack
    project behaviour. We don't want the user to be able to do any operations to this 
    project nor even notice it exists.

    Also filters other default items we dont want to show, like internal
    applications.
    """
    filtered = [i for i in items if not getattr(i, 'is_default', False)]
    return filtered

def check_elements(elements, valid_elements):
    """Checks a list of elements are present in an allowed elements list"""
    invalid_elements = [k for k in elements if k not in valid_elements]
    if invalid_elements:
        raise TypeError('The elements {0} are not defined \
            in {1}'.format(invalid_elements, valid_elements))

def swap_dict(old_dict):
    """Returns a new dictionary in wich the keys are all the values of the old
    dictionary and the values are lists of keys that had that value.
    
    Example: 
    d = { 'a':['c','v','b'], 's':['c','v','d']} 
    swap_dict(d) -> {'c': ['a', 's'], 'b': ['a'], 'd': ['s'], 'v': ['a', 's']}
    """
    new_dict = {}
    for key in old_dict:
        for value in old_dict[key]:
            new_dict[value] = new_dict.get(value, [])
            new_dict[value].append(key)
    return new_dict


def get_avatar(obj, avatar_type, default_avatar):
    """Gets the object avatar or a default one."""
    avatar = getattr(obj, avatar_type, None)
    if avatar:
        return settings.MEDIA_URL + avatar
    else:
        return settings.STATIC_URL + default_avatar


def get_switch_url(organization, check_switchable=True):
    if check_switchable and not getattr(organization, 'switchable', False):
        return False
    return urlresolvers.reverse('switch_tenants',
                                kwargs={'tenant_id': organization.id})


def get_counter(self, organization=None, application=None):
    users = []
    # NOTE(garcianavalon) Get all the users' ids that belong to
    # the application (they have one or more roles in their default
    # organization)
    all_users = api.keystone.user_list(self.request)
    users_with_roles = set()
    if organization:
        role_assignments = api.keystone.get_project_users_roles(
            self.request, project=organization)
        for user in all_users:
            for a in role_assignments:
                if (user.id == a):
                    users_with_roles.add(user.id)
    elif application:
        role_assignments = fiware_api.keystone.user_role_assignments(
            self.request, application=application)
        for user in all_users:
            for a in role_assignments:
                if (user.id == a.user_id
                    and user.default_project_id == a.organization_id):
                        users_with_roles.add(user.id)
    users = [user for user in all_users
             if user.id in users_with_roles]

    return len(users)

def paginate(self, list_pag, index, limit):
    try:
        index = int(index)
        LOG.debug('index: {0}'.format(index))
    except ValueError as e:
        LOG.error("Invalid index. {0}".format(e))
        exceptions.handle(self.request,
                          ("Invalid index. \
                            Error message: {0}".format(e)))

    if len(list_pag) <= limit:
        final_list = list_pag
    else:
        if index == (len(list_pag)-1):
            final_list = list_pag[(index-limit+1):len(list_pag)]
        elif index <= 0:
            final_list = list_pag[0:limit]
        elif (index > (len(list_pag)-1)):
            final_list = list_pag[len(list_pag)-limit+1:len(list_pag)]
        elif (index + limit) > (len(list_pag)-1):
            final_list = list_pag[index:len(list_pag)]
        else:
            final_list = list_pag[(index):(index+limit)]

    return final_list
