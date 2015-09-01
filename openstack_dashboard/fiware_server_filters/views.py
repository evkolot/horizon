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

import collections
import json
import logging
import six

from django import http
from django.core.cache import cache
from django.views import generic
from django.views.decorators.csrf import csrf_exempt

from horizon import exceptions

from openstack_dashboard import api
from openstack_dashboard import fiware_api
from openstack_dashboard.dashboards.idm import utils as idm_utils


LOG = logging.getLogger('idm_logger')

SHORT_CACHE_TIME = 20 # seconds


class AjaxKeystoneFilter(generic.View):
    """view to handle ajax filtering in modals. 
    Uses API filtering in Keystone.

    To use it set the filter key, for example:
    
        filter_key='name__contains'

    and the view will populate the filters dictionarywith the 
    ajax data sent.
    """
    http_method_names = ['post']
    filter_key = None

    @csrf_exempt
    def dispatch(self, request, *args, **kwargs):
        return super(AjaxKeystoneFilter, self).dispatch(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        # NOTE(garcianavalon) replace with JsonResponse when 
        # Horizon uses Django 1.7+
        filters = self.set_filter(request.POST['filter_by'])
        try:
            response_data = self.api_call(request, filters=filters)
            return http.HttpResponse(
                json.dumps(response_data), 
                content_type="application/json")
            
        except Exception as exc:
            LOG.error(str(exc))
            exceptions.handle(request, 'Unable to filter.')
    
    def set_filter(self, filter_by):
        if filter_by:
            filters = {}
            filters[self.filter_key] = filter_by
        else:
            filters = None
        return filters

    def api_call(self, request, filters=None):
        """Override to add the corresponding api call, for example:
            api.keystone.users_list(request, filters=filters)
        WARNING: the return object must be json-serializable
        """
        raise NotImplementedError


class UsersWorkflowFilter(AjaxKeystoneFilter):
    filter_key = 'username__startswith'

    def api_call(self, request, filters=None):
        json_users = self._get_json_users(request, filters)

        # now filter by username
        if not filters:
            return json_users

        filtered_users = self._apply_filters(json_users, filters)

        organization = request.POST.get('organization', None)
        if not organization:
            return filtered_users

        members = [a.user['id'] for a 
                   in api.keystone.role_assignments_list(request, project=organization)]

        return [u for u in filtered_users 
                if u['id'] in members]
        
    def _apply_filters(self, json_users, filters):
        filter_by = filters[self.filter_key]
        filtered_users = [u for u in json_users
                          if 'username' in u
                          and u['username'].startswith(filter_by)]

        return filtered_users
    
    def _get_json_users(self, request, filters):
        # NOTE(garcianavalon) because we chose to store the display
        # name in extra to use the email as name for login, we can't
        # use keystone filters, we need to filter locally.
        # We cache the query to save some petitions here
        json_users = cache.get('json_users')
        if json_users is None:
            filters.update({'enabled':True})
            users = fiware_api.keystone.user_list(request, filters=filters)
            attrs = [
                'id',
                'username',
                'img_small',
                'name' # for no-username users
            ]
            temp_json_users = [idm_utils.obj_to_jsonable_dict(u, attrs) 
                               for u in users]
            # add MEDIA_URL to avatar paths or the default avatar
            json_users = []
            for user in temp_json_users:
                user['img_small'] = idm_utils.get_avatar(user, 
                    'img_small', idm_utils.DEFAULT_USER_SMALL_AVATAR)
                json_users.append(user)

            cache.set('json_users', json_users, SHORT_CACHE_TIME)

        return json_users

class UsersAndKeystoneAdminsWorkflowFilter(UsersWorkflowFilter):
    """Don't filter by username so it also shows Keystone users and admins."""
    def _apply_filters(self, json_users, filters):
        filter_by = filters[self.filter_key]
        filtered_users = [u for u in json_users
                          if u.get('username', u['name']).startswith(filter_by)]

        return filtered_users


class OrganizationsWorkflowFilter(AjaxKeystoneFilter):
    filter_key = 'name__startswith'

    def api_call(self, request, filters=None):
        organizations = fiware_api.keystone.project_list(request, 
            filters=filters)
        organizations = idm_utils.filter_default(organizations)
        attrs = [
            'id',
            'name',
            'img_small'
        ]
        # add MEDIA_URL to avatar paths or the default avatar
        json_orgs = []
        for org in organizations:
            json_org = idm_utils.obj_to_jsonable_dict(org, attrs) 
            json_org['img_small'] = idm_utils.get_avatar(json_org, 
                'img_small', idm_utils.DEFAULT_ORG_SMALL_AVATAR)
            json_orgs.append(json_org)
        return json_orgs


class ComplexAjaxFilter(generic.View):
    """Base view for complex ajax filtering, for example in pagination.
    Supports multiple filters and pagination markers. Uses API filtering
    and pagination in Keystone when possible or implements custom filters.

    The filters should be included as query parameters of the URL.

    .. attribute:: custom_filter_keys

        A dictionary with custom filters that should be handled here and a
        weight to set order of filtering (lower numbers go first). The rest 
        of the filters will be forwarded to the api call. For each custom
        key a function with name [custom_key_name_filter] should be 
        implemented. This function gets executed AFTER the api call.
        Default is an empty dict (``{}``).
    """
    http_method_names = ['get']
    custom_filter_keys = {}

    def get(self, request, *args, **kwargs):
        # NOTE(garcianavalon) replace with JsonResponse when 
        # Horizon uses Django 1.7+
        filters = request.GET.items()
        try:
            response_data = self.load_data(request, filters=filters)
            return http.HttpResponse(
                json.dumps(response_data), 
                content_type="application/json")
            
        except Exception as exc:
            LOG.error(str(exc))
            exceptions.handle(request, 'Unable to filter.')

    def api_call(self, request, filters):
        """Override to add the corresponding api call, for example:
            api.keystone.users_list(request, filters=filters)
        WARNING: the return object must be json-serializable
        """
        raise NotImplementedError

    def _separate_filters(self, filters):
        """Returns a dictionary with all the custom
        filters present in the received filters dictionary and
        a dictionary with all the non-custom filters.
        """
        custom_filters = {}
        api_filters = {}
        for key, value in filters:
            if key in self.custom_filter_keys.keys():
                custom_filters[key] = value
            else:
                api_filters[key] = value

        ordered_custom_filters = collections.OrderedDict(
            sorted(custom_filters.items(), key=lambda t: self.custom_filter_keys[t[0]]))

        return ordered_custom_filters, api_filters

    def load_data(self, request, filters):
        custom_filters, api_filters = self._separate_filters(filters)

        data = self.api_call(request, filters=api_filters)

        for key, value in six.iteritems(custom_filters):
            data = getattr(self, key + '_filter')(request, data, value)


        return data


class OrganizationsComplexFilter(ComplexAjaxFilter):
    custom_filter_keys = {
        'page': 99, # it should always go last!
        'application_id': 5,
    }


    def page_filter(self, request, json_orgs, page_number):
        page_size = 4 # TODO(garcianavalon) setting
        return idm_utils.paginate_list(json_orgs, int(page_number), page_size)

    def application_id_filter(self, request, json_orgs, application_id):
        role_assignments = fiware_api.keystone.organization_role_assignments(
            request, application=application_id)

        authorized_organizations = set([a.organization_id for a in role_assignments])
        organizations = [org for org in json_orgs if org['id']
                 in authorized_organizations]

        # organizations = idm_utils.filter_default(
        #    sorted(organizations, key=lambda x: x['name'].lower()))
        
        return organizations

    def api_call(self, request, filters):
        organizations = fiware_api.keystone.project_list(
            request, 
            filters=filters)

        organizations = idm_utils.filter_default(
            sorted(organizations, key=lambda x: x.name.lower()))

        attrs = [
            'id',
            'name',
            'img_small',
            'description',
        ]

        # add MEDIA_URL to avatar paths or the default avatar
        json_orgs = []
        for org in organizations:
            json_org = idm_utils.obj_to_jsonable_dict(org, attrs) 
            json_org['img_small'] = idm_utils.get_avatar(json_org, 
                'img_small', idm_utils.DEFAULT_ORG_SMALL_AVATAR)
            json_orgs.append(json_org)
            
        return json_orgs


class UsersComplexFilter(ComplexAjaxFilter):
    custom_filter_keys = {
        'page': 99, # it should always go last!
        'application_id': 5,
    }

    def page_filter(self, request, json_users, page_number):
        page_size = 4 # TODO(garcianavalon) setting
        return idm_utils.paginate_list(json_users, int(page_number), page_size)

    def application_id_filter(self, request, json_users, application_id):
        role_assignments = fiware_api.keystone.user_role_assignments(
            request, application=application_id)
        
        authorized_users = []
        added_users = []
        for assignment in role_assignments:
            if assignment.user_id in added_users:
                # NOTE(garcianavalon) we can't use a set because
                # user is a dictionary for json-paring later
                continue
            user = next((user for user in json_users
                        if user['id'] == assignment.user_id), None)
            if user and user['default_project_id'] == assignment.organization_id:
                authorized_users.append(user)

        return authorized_users

    def api_call(self, request, filters):
        # NOTE(garcianavalon) because we chose to store the display
        # name in extra to use the email as name for login, we can't
        # use keystone filters, we need to filter locally.
        # We cache the query to save some petitions here
        json_users = cache.get('json_users')

        if json_users is None:
            filters.update({'enabled':True})
            users = fiware_api.keystone.user_list(request, filters=filters)

            users = sorted(users, key=lambda x: getattr(x, 'username', x.name).lower())

            attrs = [
                'id',
                'username',
                'default_project_id',
                'img_small',
                'name' # for no-username users
            ]

            # add MEDIA_URL to avatar paths or the default avatar
            json_users = []
            for user in users:
                json_user = idm_utils.obj_to_jsonable_dict(user, attrs) 
                json_user['img_small'] = idm_utils.get_avatar(user, 
                    'img_small', idm_utils.DEFAULT_USER_SMALL_AVATAR)
                json_users.append(json_user)

            cache.set('json_users', json_users, SHORT_CACHE_TIME)

        return json_users
