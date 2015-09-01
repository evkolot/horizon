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
from django.conf.urls import patterns
from django.conf.urls import url

from openstack_dashboard.fiware_server_filters import views


urlpatterns = patterns(
    '',
    url(r'^users$', 
        views.UsersWorkflowFilter.as_view(), 
        name='fiware_server_filters_users'),
    url(r'^admins$', 
        views.UsersAndKeystoneAdminsWorkflowFilter.as_view(), 
        name='fiware_server_filters_admins'),
    url(r'^organizations$', 
        views.OrganizationsWorkflowFilter.as_view(), 
        name='fiware_server_filters_organizations'),

    url(r'^complex/organizations$', 
        views.OrganizationsComplexFilter.as_view(), 
        name='fiware_complex_server_filters_organizations'),

    url(r'^complex/users$', 
        views.UsersComplexFilter.as_view(), 
        name='fiware_complex_server_filters_users'),
)

