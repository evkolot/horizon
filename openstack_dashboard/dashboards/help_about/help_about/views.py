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

from horizon import forms
from horizon import views

from django.views.generic import TemplateView


LOG = logging.getLogger('idm_logger')

class MultiItemView(views.APIView):
    template_name = 'help_about/help_about/index.html'

    def get_context_data(self, **kwargs):
        context = super(MultiItemView, self).get_context_data(**kwargs)
        context['items'] = [AboutView(), DocumentationView(), ToursView()]

        return context


# Handeling views
class AboutView(views.APIView):
    template_name = 'help_about/help_about/about.html'
    description = 'About FIWARE Accounts'
    icon = 'fa fa-info-circle'

class DocumentationView(views.APIView):
    template_name = 'help_about/help_about/documentation.html'
    description = 'Documentation'
    icon = 'fa fa-book'

class ToursView(views.APIView):
    template_name = 'help_about/help_about/tours.html'
    description = 'Learning Tours'
    icon = 'fa fa-graduation-cap'
