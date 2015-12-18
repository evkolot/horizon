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
EMAIL_HTML_TEMPLATE = 'email/base_email.html'
EMAIL_TEXT_TEMPLATE = 'email/base_email.txt'

RESET_PASSWORD_HTML_TEMPLATE = 'email/reset_password.html'
RESET_PASSWORD_TXT_TEMPLATE = 'email/reset_password.txt'

ACTIVATION_HTML_TEMPLATE = 'email/activation.html'
ACTIVATION_TXT_TEMPLATE = 'email/activation.txt'


def send_html_email(to, subject, from_email=None, **kwargs):
    LOG.debug('Sending email to %s with subject %s', to, subject)
    text_content = render_to_string(EMAIL_TEXT_TEMPLATE, dictionary=kwargs)
    html_content = render_to_string(EMAIL_HTML_TEMPLATE, dictionary=kwargs)
    
    msg = EmailMultiAlternatives(subject, text_content, from_email, to)
    msg.attach_alternative(html_content, "text/html")
    msg.send()

def send_activation_email(self, user):
    # TODO(garcianavalon) subject, message and from_email as settings/files
    subject = '[FIWARE Lab] Welcome to FIWARE'
    # Email subject *must not* contain newlines
    subject = ''.join(subject.splitlines())
    context = {
        'activation_url':('{0}/activate/?activation_key={1}&user={2}'
            '').format(_get_current_domain(), user.activation_key, user.id),
        'user_name':user.username,
    }
    text_content = render_to_string(ACTIVATION_TXT_TEMPLATE, 
                                    dictionary=context)
    html_content = render_to_string(ACTIVATION_HTML_TEMPLATE, 
                                    dictionary=context)
    #send a mail for activation
    self.send_html_email(
        to=[user.name],
        subject=subject,
        content={'text': text_content, 'html': html_content})


def send_reactivation_email(self, user, activation_key):
    # TODO(garcianavalon) subject and message as settings/files
    subject = '[FIWARE Lab] Welcome to FIWARE'
    # Email subject *must not* contain newlines
    subject = ''.join(subject.splitlines())
    context = {
        'activation_url':('{0}/activate/?activation_key={1}&user={2}'
            '').format(_get_current_domain(), activation_key.id, user.id),
        'user_name':user.username,
    }
    text_content = render_to_string(ACTIVATION_TXT_TEMPLATE, 
                                    dictionary=context)
    html_content = render_to_string(ACTIVATION_HTML_TEMPLATE, 
                                    dictionary=context)
    #send a mail for activation
    self.send_html_email(
        to=[user.name],
        subject=subject, 
        content={'text': text_content, 'html': html_content})

def send_reset_email(self, email, token, user):
    # TODO(garcianavalon) subject, message and from_email as settings/files
    subject = '[FIWARE Lab] Reset password instructions'
    # Email subject *must not* contain newlines
    subject = ''.join(subject.splitlines())
    context = {
        'reset_url':('{0}/password/reset/?token={1}&email={2}'
            '').format(_get_current_domain(),token, email),
        'user_name':user['username'],
    }
    text_content = render_to_string(RESET_PASSWORD_TXT_TEMPLATE, 
                                    dictionary=context)
    html_content = render_to_string(RESET_PASSWORD_HTML_TEMPLATE, 
                                    dictionary=context)
    #send a mail for activation
    self.send_html_email(
        to=[email], 
        subject=subject, 
        content={'text': text_content, 'html': html_content})

        
def _get_current_domain():
    if getattr(local_settings, 'EMAIL_URL', None):
        return local_settings.EMAIL_URL
    else:
        LOG.warning(
            'EMAIL_URL not found in local_settings.py. Using fallback value.')
        return 'http://localhost:8000'
