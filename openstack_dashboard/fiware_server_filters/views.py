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

import json

from django import http
from django.core.cache import cache
from django.views import generic
from django.views.decorators.csrf import csrf_exempt

from horizon import exceptions

from openstack_dashboard import api
from openstack_dashboard.dashboards.idm import utils as idm_utils

SHORT_CACHE_TIME = 10 # seconds

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
            
        except Exception:
            exceptions.handle(self.request,
                              'Unable to filter.')
    
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

    def _obj_to_jsonable_dict(self, obj, attrs):
        """converts a object into a json-serializable dict, geting the
        specified attributes.
        """
        as_dict = {}
        for attr in attrs:
            if hasattr(obj, attr):
                as_dict[attr] = getattr(obj, attr)
        return as_dict


class UsersWorkflowFilter(AjaxKeystoneFilter):
    filter_key = 'username__startswith'

    def api_call(self, request, filters=None):
        # NOTE(garcianavalon) because we chose to store the display
        # name in extra to use the email as name for login, we can't
        # use keystone filters, we need to filter locally.
        # We cache the query to save some petitions here
        json_users = cache.get('json_users')
        if json_users is None:
            users = api.keystone.user_list(request, filters=filters)
            attrs = [
                'id',
                'username',
                'img_small'
            ]
            json_users = [self._obj_to_jsonable_dict(u, attrs) for u in users]
            cache.set('json_users', json_users, SHORT_CACHE_TIME)
        # now filter by username
        if filters:
            filter_by = filters[self.filter_key]
            return [u for u in json_users 
                if u['username'].startswith(filter_by)]
        else:
            return json_users

class OrganizationsWorkflowFilter(AjaxKeystoneFilter):
    filter_key = 'name__startswith'

    def api_call(self, request, filters=None):
        organizations, more = api.keystone.tenant_list(request, 
            filters=filters)
        organizations = idm_utils.filter_default(organizations)
        attrs = [
            'id',
            'name',
            'img_small'
        ]
        return [self._obj_to_jsonable_dict(o, attrs) for o in organizations]