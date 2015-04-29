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

import os
import logging

from django.conf import settings
from django.core.urlresolvers import reverse, reverse_lazy

from horizon import exceptions
from horizon import forms
from horizon import tables
from horizon import tabs
from horizon.utils import memoized

from openstack_dashboard import api
from openstack_dashboard import fiware_api
from openstack_dashboard.local import local_settings
from openstack_dashboard.dashboards.idm import views as idm_views
from openstack_dashboard.dashboards.idm.users import tables as user_tables
from openstack_dashboard.dashboards.idm import utils as idm_utils
from openstack_dashboard.dashboards.idm.users.forms import  InfoForm, ContactForm, AvatarForm, CancelForm

from horizon import views

LOG = logging.getLogger('idm_logger')
LIMIT = getattr(local_settings, 'PAGE_LIMIT', 15)



class DetailUserView(tables.MultiTableView):
    template_name = 'idm/users/index.html'
    table_classes = (user_tables.OrganizationsTable,
                     user_tables.ApplicationsTable)

    
    def get_organizations_data(self):
        organizations = []
        index_org = self.request.GET.get('index_org', 0)
        LOG.debug(self.request.path)
        path = self.request.path
        user_id = path.split('/')[3]

        #domain_context = self.request.session.get('domain_context', None)
        try:
            organizations, self._more = api.keystone.tenant_list(
                self.request,
                user=user_id,
                admin=False)

            organizations = idm_utils.filter_default(sorted(organizations, key=lambda x: x.name.lower()))
        
            indexes = range(0, len(organizations), LIMIT)
            self._tables['organizations'].indexes = indexes
            self._tables['organizations'].index_act = int(index_org)
            organizations = idm_utils.paginate(self, organizations, index=index_org, limit=LIMIT)

            for org in organizations:
                users = idm_utils.get_counter(self, organization=org)
                setattr(org, 'counter', users)
        except Exception:
            self._more = False
            exceptions.handle(self.request,
                              ("Unable to retrieve organization information."))
        return organizations

    def get_applications_data(self):
        applications = []
        index_app = self.request.GET.get('index_app', 0)
        path = self.request.path
        user_id = path.split('/')[3]

        try:
            # TODO(garcianavalon) extract to fiware_api
            all_apps = fiware_api.keystone.application_list(self.request)
            apps_with_roles = [a.application_id for a 
                               in fiware_api.keystone.user_role_assignments(
                               self.request, user=user_id)]
            applications = [app for app in all_apps 
                            if app.id in apps_with_roles]
            applications = idm_utils.filter_default(
                            sorted(applications, key=lambda x: x.name.lower()))
        
            indexes = range(0, len(applications), LIMIT)
            self._tables['applications'].indexes = indexes
            self._tables['applications'].index_act = int(index_app)
            applications = idm_utils.paginate(self, applications, index=index_app, limit=LIMIT)

            for app in applications:
                users = idm_utils.get_counter(self, application=app)
                setattr(app, 'counter', users)
        except Exception:
            exceptions.handle(self.request,
                              ("Unable to retrieve application list."))
        return applications

    def _can_edit(self):
        # Allowed if its the same user
        return (self.request.user.id == self.kwargs['user_id']
            and self.request.organization.id == self.request.user.default_project_id)

    def get_context_data(self, **kwargs):
        context = super(DetailUserView, self).get_context_data(**kwargs)
        user_id = self.kwargs['user_id']
        user = api.keystone.user_get(self.request, user_id, admin=True)
        context['user'] = user
        if hasattr(user, 'img_original'):
            image = getattr(user, 'img_original')
            image = settings.MEDIA_URL + image
        else:
            image = settings.STATIC_URL + 'dashboard/img/logos/original/user.png'
        context['image'] = image
        context['index_app'] = self.request.GET.get('index_app', 0)
        context['index_org'] = self.request.GET.get('index_org', 0)
        if self._can_edit():
            context['edit'] = True
        return context

class BaseUsersMultiFormView(idm_views.BaseMultiFormView):
    template_name = 'idm/users/edit.html'
    forms_classes = [InfoForm, ContactForm, AvatarForm, CancelForm]
    
    def get_endpoint(self, form_class):
        """Override to allow runtime endpoint declaration"""
        endpoints = {
            InfoForm: reverse('horizon:idm:users:info', 
                                kwargs=self.kwargs),
            ContactForm: reverse('horizon:idm:users:contact', 
                                kwargs=self.kwargs),
            AvatarForm: reverse('horizon:idm:users:avatar', 
                                kwargs=self.kwargs),
            CancelForm: reverse('horizon:idm:users:cancel', 
                                kwargs=self.kwargs),
        }
        return endpoints.get(form_class)

    def get_object(self):
        try:
            return api.keystone.user_get(self.request, self.kwargs['user_id'])
        except Exception:
            redirect = reverse("horizon:idm:users:index")
            exceptions.handle(self.request, 
                    ('Unable to update user'), redirect=redirect)

    def get_initial(self, form_class):
        initial = super(BaseUsersMultiFormView, self).get_initial(form_class)  
        # Existing data from organizations
        initial.update({
            "userID": self.object.id,
            "name": getattr(self.object, 'name', ' '),
            "username": getattr(self.object, 'username', ' '),
            "description": getattr(self.object, 'description', ' '),    
            "city": getattr(self.object, 'city', ' '),
            "website": getattr(self.object, 'website', ' '),
        })
        return initial

    def get_context_data(self, **kwargs):

        context = super(BaseUsersMultiFormView, self).get_context_data(**kwargs)
        if hasattr(self.object, 'img_original'):
            image = getattr(self.object, 'img_original')
            image = settings.MEDIA_URL + image
        else:
            image = settings.STATIC_URL + 'dashboard/img/logos/original/user.png'
        context['image'] = image
        return context


class InfoFormHandleView(BaseUsersMultiFormView):    
    form_to_handle_class = InfoForm

class ContactFormHandleView(BaseUsersMultiFormView):
    form_to_handle_class = ContactForm
   
class AvatarFormHandleView(BaseUsersMultiFormView):
    form_to_handle_class = AvatarForm

class CancelFormHandleView(BaseUsersMultiFormView):
    form_to_handle_class = CancelForm

    def handle_form(self, form):
        """ Wrapper for form.handle for easier overriding."""
        return form.handle(self.request, form.cleaned_data, user=self.object)
