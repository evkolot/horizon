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
import requests

from django.conf import settings
from django.template.loader import render_to_string

LOG = logging.getLogger('idm_logger')

XACML_TEMPLATE = 'access_control/policy_set.xacml'

def policyset_update(app_id, role_permissions):
    """Gets all role's permissions and generates a xacml file to
    update the Access Control.
    """
    if not settings.ACCESS_CONTROL_URL:
        LOG.warning('ACCESS_CONTROL_URL setting is not set.')
        return

    if not settings.ACCESS_CONTROL_MAGIC_KEY:
        LOG.warning('ACCESS_CONTROL_MAGIC_KEY setting is not set.')
        return 

    context = {
        'policy_set_description': 'TODO',
        'role_permissions': role_permissions,
        'app_id': app_id,
    }

    xml = render_to_string(XACML_TEMPLATE, context)
    LOG.debug('XACML: %s', xml)

    headers = {
        'content-type': 'application/xml',
        'X-Auth-Token': settings.ACCESS_CONTROL_MAGIC_KEY
    }
    response = requests.put(
        settings.ACCESS_CONTROL_URL,
        data=xml,
        headers=headers,
        verify=False)

    LOG.debug('Response code from the AC GE: %s', response.status_code)

    return response
