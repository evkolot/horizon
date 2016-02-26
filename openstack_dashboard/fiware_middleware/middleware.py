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

from django import http
from django.conf import settings
from django.core.urlresolvers import reverse
from django import shortcuts

from horizon import exceptions
from horizon.utils import functions as utils
from horizon import middleware

from keystoneclient.openstack.common.apiclient \
    import exceptions as kc_exceptions

from openstack_dashboard import api
from openstack_dashboard import fiware_api


LOG = logging.getLogger('idm_logger')

# TODO(garcianavalon) all the logout and unauthorized stuff could go
# into its own middleware

def _is_static_or_media_requests(self, path):
    # NOTE(garcianavalon) In development (and I'm not sure if
    # in producction too, I hope Apache is doing it right) django 
    # executes this middleware on every request, including media
    # or static elements like images. This makes it sometimes hard
    # to debug when looking at Keystone logs and slows down the portal
    if path.startswith('/media') or path.startswith('/static'):
        LOG.debug(
            'Skiping %(middleware)s for path %(path)s',
            {'middleware': self.__class__.__name__, 'path': path})
        return True
        

class UserInfoMiddleware(object):
    """Adds more user info to the request object for convenience."""

    def process_request(self, request):
        path = request.META['PATH_INFO']

        if _is_static_or_media_requests(self, path):
            return

        if (reverse('logout') == path
            or not hasattr(request, 'user') 
            or not request.user.is_authenticated()):
            return

        try:
            user_data = api.keystone.user_get(request, request.user.id)
            LOG.debug(str(user_data) + 'for user %s', request.user.id)
            # setattr(user_data, 'username', user_data.name)
            for attr, value in user_data.__dict__.iteritems():
                setattr(request.user, attr, value)
        except (kc_exceptions.Unauthorized, exceptions.NotAuthorized):
            response = http.HttpResponseRedirect(settings.LOGOUT_URL)
            msg = ("Session expired")
            LOG.debug(msg + 'for user %s', request.user.id)
            utils.add_logout_reason(request, response, msg)
            return response
        

class OrganizationInfoMiddleware(object):
    """Adds organization info to the request object for convenience."""

    def process_request(self, request):
        path = request.META['PATH_INFO']

        if _is_static_or_media_requests(self, path):
            return

        if (reverse('logout') == path
            or not hasattr(request, 'user') 
            or not request.user.is_authenticated()):
            return
            
        current_organization = request.user.token.project['id']

        # TODO(garcianavalon) lazyloading and caching
        request.organization = fiware_api.keystone.project_get(
            request, current_organization)


class SwitchMiddleware(object):
    """Adds all the possible organizations the user can switch to."""

    def process_request(self, request):
        # Allowed if he is an admin in the organization
        path = request.META['PATH_INFO']

        if _is_static_or_media_requests(self, path):
            return

        if (reverse('logout') == path
            or not hasattr(request, 'user')
            or not request.user.is_authenticated()
            or not hasattr(request, 'organization')):
            return

        organizations = []
        try:
            # TODO(garcianavalon) lazyloading and caching
            # TODO(garcianavalon) move to fiware_api
            owner_role = fiware_api.keystone.get_owner_role(request)
            assignments = api.keystone.role_assignments_list(
                request, user=request.user.id, role=owner_role.id)
            
            switch_orgs = set([a.scope['project']['id'] for a in assignments 
                           if a.scope['project']['id'] != request.organization.id])
            
            for org_id in switch_orgs:
                organizations.append(fiware_api.keystone.project_get(request, org_id))

        except (kc_exceptions.Unauthorized, exceptions.NotAuthorized) as e:
            LOG.warning("Problem with Switch Middleware")
            LOG.warning(e)

        request.organizations = organizations


class CustomHorizonMiddleware(middleware.HorizonMiddleware):
    """ Redirect to logout instead of login when user is not authenticated, to
        make sure that session cookie is deleted """

    def process_exception(self, request, exception):
        """Catches internal Horizon exception classes such as NotAuthorized,
        NotFound and Http302 and handles them gracefully.
        """
        if isinstance(exception, (exceptions.NotAuthorized,
                                  exceptions.NotAuthenticated)):

            response = http.HttpResponseRedirect(settings.LOGOUT_URL)
            msg = ("Session expired")
            LOG.debug(msg + 'for user %s', request.user.id)
            utils.add_logout_reason(request, response, msg)

            if request.is_ajax():
                response_401 = http.HttpResponse(status=401)
                response_401['X-Horizon-Location'] = response['location']
                return response_401

            return response

        # If an internal "NotFound" error gets this far, return a real 404.
        if isinstance(exception, exceptions.NotFound):
            raise http.Http404(exception)

        if isinstance(exception, exceptions.Http302):
            # TODO(gabriel): Find a way to display an appropriate message to
            # the user *on* the login form...
            return shortcuts.redirect(exception.location)
