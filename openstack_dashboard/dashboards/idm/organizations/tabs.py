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
from horizon import tabs

from openstack_dashboard import api
from openstack_dashboard.dashboards.idm import utils as idm_utils
from openstack_dashboard.dashboards.idm.organizations \
    import tables as organization_tables

LOG = logging.getLogger('idm_logger')


class OtherOrganizationsTab(tabs.TableTab):
    name = ("Other Organizations")
    slug = "other_organizations_tab"
    table_classes = (organization_tables.OtherOrganizationsTable,)
    template_name = ("horizon/common/_detail_table.html")
    preload = False

    def get_marker(self, table):
        LOG.debug(self._tables.get(table.name)._marker)
        return self._tables.get(table.name)._marker

    def get_other_organizations_data(self):
        organizations = []
        limit = 5
        marker_id = self.request.GET.get('marker', None)
        LOG.debug(marker_id)
        try:
            organizations_full, self._more = api.keystone.tenant_list(
                self.request, admin=False)
            my_organizations, self._more = api.keystone.tenant_list(
                self.request, user=self.request.user.id, admin=False)
            organizations_full = idm_utils.filter_default([t for t in
                                                           organizations_full
                                                           if not t in
                                                           my_organizations])
            if marker_id:
                marker = organizations_full.index(api.keystone.tenant_get(
                    self.request, marker_id))
                LOG.debug('marker_id (index): {0}'.format(marker))
            else:
                marker = 0
                LOG.debug('marker_id (index): {0}'.format(marker))

            if (marker + limit) >= len(organizations_full):
                organizations = organizations_full[marker:len(organizations_full)]
                self._tables.get('other_organizations')._marker = None
            else:
                organizations = organizations_full[marker:(marker+limit)]
                self._tables.get('other_organizations')._marker = organizations[marker + limit + 1].id
                mark = self._tables.get('other_organizations')._marker
                LOG.debug('marker_id (actualizado): {0}'.format(mark))
                LOG.debug('maker index: {0}'.format(organizations_full.index(api.keystone.tenant_get(self.request,mark))))
            for org in organizations:
                users = idm_utils.get_counter(self, organization=org)
                setattr(org, 'counter', users)
        except Exception as e:
            self._more = False
            exceptions.handle(self.request,
                              ("Unable to retrieve organization list. \
                                    Error message: {0}".format(e)))
        return organizations


class OwnedOrganizationsTab(tabs.TableTab):
    name = ("Owner")
    slug = "owned_organizations_tab"
    table_classes = (organization_tables.OwnedOrganizationsTable,)
    template_name = ("horizon/common/_detail_table.html")
    preload = False

    def get_owned_organizations_data(self):
        organizations = []
        try:
            # NOTE(garcianavalon) the organizations the user is owner(admin)
            # are already in the request object by the middleware
            organizations = self.request.organizations
            self._more = False
            for org in organizations:
                users = idm_utils.get_counter(self, organization=org)
                setattr(org, 'counter', users)
        except Exception:
            self._more = False
            exceptions.handle(self.request,
                              ("Unable to retrieve organization information."))
        return idm_utils.filter_default(organizations)


class MemberOrganizationsTab(tabs.TableTab):
    name = ("Member")
    slug = "member_organizations_tab"
    table_classes = (organization_tables.MemberOrganizationsTable,)
    template_name = ("horizon/common/_detail_table.html")
    preload = False

    def get_member_organizations_data(self):
        organizations = []
        try:
            my_organizations, self._more = api.keystone.tenant_list(
                self.request, user=self.request.user.id, admin=False)
            owner_organizations = [org.id for org in self.request.organizations]
            organizations = [o for o in my_organizations 
                             if not o.id in owner_organizations]
        except Exception:
            self._more = False
            exceptions.handle(self.request,
                              ("Unable to retrieve organization information."))
        return idm_utils.filter_default(organizations)


class PanelTabs(tabs.TabGroup):
    slug = "panel_tabs"
    tabs = (OwnedOrganizationsTab, MemberOrganizationsTab, OtherOrganizationsTab)
    sticky = True