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
from django.template.loader import render_to_string

LOG = logging.getLogger('idm_logger')

# TODO(garcianavalon) extract as conf options
AC_URL = 'http://10.0.64.5/authzforce/\
        domains/5e022256-6d0f-4eb8-aa9d-77db3d4ad141/pap/policySet'
XACML_TEMPLATE = 'access_control/policy_set.xacml'

def policies_update(application, roles_permisions):
    """Gets all role's permissions and generates a xacml file to
    update the Access Control.
    """
    context = {
        'policy_set_description': 'TODO',
        'roles': roles_permisions,
        'app': application,
    }
    xml = render_to_string(XACML_TEMPLATE, context)
    LOG.debug('XACML: %s', xml)

    headers = {
        'content-type': 'application/xml'
    }
    response = requests.put(
        AC_URL, data=xml, headers=headers)
    LOG.debug('Response code from the AC GE: %s', response.status_code)

    return response

def policy_delete(role_id):

    # TODO(garcianavalon) send the id
    response = requests.delete(AC_URL)

    LOG.debug('Response code from the AC GE: %s', response.status_code)
    return response
