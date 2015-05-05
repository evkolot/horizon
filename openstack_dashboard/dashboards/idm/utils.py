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
from openstack_dashboard.local import local_settings


LOG = logging.getLogger('idm_logger')
DEFAULT_ORG_MEDIUM_AVATAR = 'dashboard/img/logos/medium/group.png'
DEFAULT_APP_MEDIUM_AVATAR = 'dashboard/img/logos/medium/app.png'
DEFAULT_USER_MEDIUM_AVATAR = 'dashboard/img/logos/medium/user.png'
DEFAULT_ORG_SMALL_AVATAR = 'dashboard/img/logos/small/group.png'
DEFAULT_APP_SMALL_AVATAR = 'dashboard/img/logos/small/app.png'
DEFAULT_USER_SMALL_AVATAR = 'dashboard/img/logos/small/user.png'
NUM_PAGES = getattr(local_settings, 'NUM_PAGES', 10)

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
    if type(obj) == dict:
        avatar = obj.get(avatar_type, None)
    else:
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
    if organization:
        role_assignments = api.keystone.get_project_users_roles(
            self.request, project=organization)
        users = role_assignments.keys()
    elif application:
        # NOTE(garcianavalon) careful, this endpoint also returns
        # the ids of disabled users if they still have roles!
        role_assignments = fiware_api.keystone.user_role_assignments(
            self.request, application=application)
        users = set([a.user_id for a in role_assignments])
    return len(users)

def return_pagination(self, index, indexes, numbers):
    if len(indexes)>NUM_PAGES:
        ind = int(indexes.index(index))
        if (ind - NUM_PAGES + 1) < 0:
            indexes = indexes[0:NUM_PAGES]
            numbers = numbers[0:NUM_PAGES]
        elif (ind + NUM_PAGES) > len(indexes):
            indexes = indexes[len(indexes)-NUM_PAGES:len(indexes)]
            numbers = numbers[len(numbers)-NUM_PAGES:len(numbers)]
        else:
            div_1 = int(round(NUM_PAGES/2, 0))
            div_2 = int(NUM_PAGES - div_1)
            indexes = indexes[ind-div_1:ind+div_2]
            numbers = numbers[ind-div_1:ind+div_2]
    return indexes, numbers

def paginate(self, list_pag, index, limit, table_name):
    try:
        index = int(index)
    except ValueError as e:
        LOG.error("Invalid index. {0}".format(e))
        exceptions.handle(self.request,
                          ("Invalid index. \
                            Error message: {0}".format(e)))

    indexes = range(0, len(list_pag), limit)
    numbers = [(u/limit)+1 for u in indexes]
    self._tables[table_name].index_act = int(index)
    # import pdb
    # pdb.set_trace()
    if len(indexes) > 0:
        self._tables[table_name].index_first = int(indexes[0])
        self._tables[table_name].index_last = int(indexes[-1])
        indexes, numbers = return_pagination(self, index, indexes, numbers)
        self._tables[table_name].indexes = zip(indexes, numbers)
        LOG.debug(indexes)
    final_list = []

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

class PickleObject():
    """Extremely simple class that holds the very little information we need
    to cache. Keystoneclient resource objects are not pickable.
    """
    def __init__(self, **kwds):
        self.__dict__.update(kwds)
