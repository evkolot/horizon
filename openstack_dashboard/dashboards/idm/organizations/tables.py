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

from django.core import urlresolvers
from django.utils.http import urlencode
from django.utils import http

from horizon import tables

from openstack_dashboard import api
from openstack_dashboard import fiware_api
from openstack_dashboard.local import local_settings as settings
from openstack_dashboard.dashboards.idm import utils as idm_utils
from openstack_dashboard.dashboards.idm import tables as idm_tables


LOG = logging.getLogger('idm_logger')
LIMIT = getattr(settings, 'PAGE_LIMIT', 15)


class NextPage(tables.LinkAction):
    name = "nextpage"
    verbose_name = ("Next Page")
    classes = ("ajax-update",)

    def get_marker(self):
        """Returns the index for the last object in the list of organizations.
        """
        LOG.debug('Next Page get_marker')
        if self.table.request.GET.get('index', None):
            index = int(self.table.request.GET.get('index', None)) + LIMIT
        else:
            index = LIMIT - 1
        return index

    def get_link_url(self):
        base_url = urlresolvers.reverse('horizon:idm:organizations:index')
        index = self.get_marker()
        param = urlencode({"index": index})
        LOG.debug('NextPage get_link_url')
        url = "?".join([base_url, param])
        return url


class PreviousPage(tables.LinkAction):
    name = "prevpage"
    verbose_name = ("Previous Page")
    classes = ("ajax-update",)

    def get_prev_marker(self):
        """Returns the index for the first object in the current data set
        for APIs that use marker/limit-based paging.
        """
        index = self.table.request.GET.get('index', None)
        if index:
            index = int(index) - LIMIT

        return index

    def get_link_url(self):
        base_url = urlresolvers.reverse('horizon:idm:organizations:index')
        index = self.get_prev_marker()
        param = urlencode({"index": index}) #, "prev": "true"})
        LOG.debug('PreviousPage get_link_url')
        if index > 0:
            url = "?".join([base_url, param])
        else:
            url = base_url
        return url

    def allowed(self, request, datum):
        """Determine whether this action is allowed for the current request.

        This method is meant to be overridden with more specific checks.
        """
        index = self.get_prev_marker()
        if (index is None or index < -1):
            return False
        return True


class OtherOrganizationsTable(tables.DataTable):
    avatar = tables.Column(lambda obj: idm_utils.get_avatar(
        obj, 'img_medium', idm_utils.DEFAULT_ORG_MEDIUM_AVATAR))
    name = tables.Column('name', verbose_name=('Name'))
    description = tables.Column(lambda obj: getattr(obj, 'description', ''),
                                verbose_name=('Description'))
    counter = tables.Column('counter')

    class Meta:
        name = "other_organizations"
        verbose_name = ("")
        table_actions = (PreviousPage, NextPage, )
        row_class = idm_tables.OrganizationClickableRow


class OwnedOrganizationsTable(tables.DataTable):
    avatar = tables.Column(lambda obj: idm_utils.get_avatar(
        obj, 'img_medium', idm_utils.DEFAULT_ORG_MEDIUM_AVATAR))
    name = tables.Column('name', verbose_name=('Name'))
    description = tables.Column(lambda obj: getattr(obj, 'description', ''),
                                verbose_name=('Description'))
    switch = tables.Column(lambda obj: idm_utils.get_switch_url(
        obj, check_switchable=False))
    counter = tables.Column('counter')

    class Meta:
        name = "owned_organizations"
        verbose_name = ("")
        row_class = idm_tables.OrganizationClickableRow


class MemberOrganizationsTable(tables.DataTable):
    avatar = tables.Column(lambda obj: idm_utils.get_avatar(
        obj, 'img_medium', idm_utils.DEFAULT_ORG_MEDIUM_AVATAR))
    name = tables.Column('name', verbose_name=('Name'))
    description = tables.Column(lambda obj: getattr(obj, 'description', None),
                                verbose_name=('Description'))


    class Meta:
        name = "member_organizations"
        verbose_name = ("")
        row_class = idm_tables.OrganizationClickableRow



class ManageMembersLink(tables.LinkAction):
    name = "manage_members"
    verbose_name = ("Manage")
    url = "horizon:idm:organizations:members"
    classes = ("ajax-modal",)
    icon = "cogs"

    def allowed(self, request, user):
        # Allowed if he is an owner in the organization
        # TODO(garcianavalon) move to fiware_api
        org_id = self.table.kwargs['organization_id']
        user_roles = api.keystone.roles_for_user(
            request, request.user.id, project=org_id)
        owner_role = fiware_api.keystone.get_owner_role(request)
        return owner_role.id in [r.id for r in user_roles]

    def get_link_url(self, datum=None):
        org_id = self.table.kwargs['organization_id']
        return  urlresolvers.reverse(self.url, args=(org_id,))


class MembersTable(tables.DataTable):
    avatar = tables.Column(lambda obj: idm_utils.get_avatar(
        obj, 'img_medium', idm_utils.DEFAULT_USER_MEDIUM_AVATAR))
    username = tables.Column('username', verbose_name=('Members'))
    

    class Meta:
        name = "members"
        verbose_name = ("Members")
        table_actions = (tables.FilterAction, ManageMembersLink, )
        multi_select = False
        row_class = idm_tables.UserClickableRow


class AuthorizingApplicationsTable(tables.DataTable):
    avatar = tables.Column(lambda obj: idm_utils.get_avatar(
        obj, 'img_medium', idm_utils.DEFAULT_APP_MEDIUM_AVATAR))
    name = tables.Column('name', verbose_name=('Applications'))
    url = tables.Column(lambda obj: getattr(obj, 'url', ''))
    counter = tables.Column('counter')

    class Meta:
        name = "applications"
        verbose_name = ("Authorizing Applications")
        row_class = idm_tables.ApplicationClickableRow
        table_actions = (tables.FilterAction,)
