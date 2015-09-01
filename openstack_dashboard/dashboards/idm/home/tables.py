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

from horizon import tables
from openstack_dashboard.dashboards.idm import utils as idm_utils
from openstack_dashboard.dashboards.idm import tables as idm_tables


class CreateOrganization(tables.LinkAction):
    name = "create_organization"
    verbose_name = "Create"
    url = "horizon:idm:organizations:create"


class RegisterApplication(tables.LinkAction):
    name = "register_application"
    verbose_name = "Register"
    url = "horizon:idm:myApplications:create"


class OrganizationsTable(tables.DataTable):
    avatar = tables.Column(lambda obj: idm_utils.get_avatar(
        obj, 'img_medium', idm_utils.DEFAULT_ORG_MEDIUM_AVATAR))
    name = tables.Column('name', verbose_name=('Name'))
    description = tables.Column(lambda obj: getattr(obj, 'description', ''))
    switch = tables.Column(lambda obj: idm_utils.get_switch_url(obj))
    view_all_url = 'horizon:idm:organizations:index'

    class Meta:
        name = "organizations"
        verbose_name = 'Organizations'
        table_actions = (CreateOrganization,)
        multi_select = False
        row_class = idm_tables.OrganizationClickableRow
        template = 'idm/home/_data_table.html'


class ApplicationsTable(tables.DataTable):
    avatar = tables.Column(lambda obj: idm_utils.get_avatar(
        obj, 'img_medium', idm_utils.DEFAULT_APP_MEDIUM_AVATAR))
    name = tables.Column('name', verbose_name=('Name'))
    url = tables.Column(lambda obj: getattr(obj, 'url', ''))
    view_all_url = 'horizon:idm:myApplications:index'

    class Meta:
        name = "applications"
        verbose_name = ("Applications")
        table_actions = (RegisterApplication,)
        multi_select = False
        row_class = idm_tables.ApplicationClickableRow
        template = 'idm/home/_data_table.html'

