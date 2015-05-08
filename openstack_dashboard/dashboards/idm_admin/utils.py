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
from openstack_dashboard.local import local_settings

NUM_PAGES = getattr(local_settings, 'NUM_PAGES', 10)



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
