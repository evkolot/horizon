# Copyright (C) 2015 Universidad Politecnica de Madrid
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import logging

from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string

from horizon import exceptions

from openstack_dashboard.local import local_settings


LOG = logging.getLogger('idm_logger') 


def send_html_email(to, subject, text_template, html_template,
                    from_email=None, **kwargs):
    LOG.debug('Sending email to %s with subject %s', to, subject)
    text_content = render_to_string(text_template, dictionary=kwargs)
    html_content = render_to_string(html_template, dictionary=kwargs)
    
    msg = EmailMultiAlternatives(subject, text_content, from_email, to)
    msg.attach_alternative(html_content, "text/html")
    msg.send()

def send_activation_email(self, user, activation_key):
    content = {
        'activation_url':('{0}/activate/?activation_key={1}&user={2}'
            '').format(_get_current_domain(), activation_key, user.id),
        'user_name':user.username,
    }

    self.send_html_email(
        to=[user.name],
        subject='Welcome to FIWARE',
        text_template='email/activation.txt',
        html_template='email/activation.html',
        content=content)

def send_reset_email(self, email, token, user):
    content = {
        'reset_url':('{0}/password/reset/?token={1}&email={2}'
            '').format(_get_current_domain(), token, email),
        'user_name':user['username'],
    }

    self.send_html_email(
        to=[email], 
        subject='Reset password instructions',
        text_template='email/reset_password.txt',
        html_template='email/reset_password.html',
        content=content)

        
def _get_current_domain():
    if getattr(local_settings, 'EMAIL_URL', None):
        return local_settings.EMAIL_URL
    else:
        LOG.warning(
            'EMAIL_URL not found in local_settings.py. Using fallback value.')
        return 'http://localhost:8000'
