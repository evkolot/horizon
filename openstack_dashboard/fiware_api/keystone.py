# Copyright (C) 2014 Universidad Politecnica de Madrid
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

import datetime
import logging
import requests

from django.conf import settings
from django.core import exceptions as django_exceptions
from django.core.cache import cache

from openstack_dashboard import api
from openstack_dashboard.local import local_settings

from horizon import exceptions
from horizon.utils import functions as utils

from keystoneclient import exceptions as ks_exceptions
from keystoneclient import session
from keystoneclient.auth.identity import v3
from keystoneclient.v3 import client


LOG = logging.getLogger('idm_logger')
# NOTE(garcianavalon) time in seconds to cache the default roles
# and other objects
DEFAULT_OBJECTS_CACHE_TIME = 60 * 15

def internal_keystoneclient(request):
    """Creates a connection with keystone using the IdM account.

    The client is cached so that subsequent API calls during the same
    request/response cycle don't have to be re-authenticated.
    """
    cache_attr = "_internal_keystoneclient"
    keystoneclient = cache.get(cache_attr, None)
    if not keystoneclient:
        idm_user_session = _password_session(request)
        keystoneclient = client.Client(session=idm_user_session)
        cache.set(cache_attr, keystoneclient, DEFAULT_OBJECTS_CACHE_TIME)
    return keystoneclient

def _password_session(request):
    # TODO(garcianavalon) better domain usage
    domain = 'default'
    endpoint = getattr(settings, 'OPENSTACK_KEYSTONE_URL')
    # insecure = getattr(settings, 'OPENSTACK_SSL_NO_VERIFY', False)
    # cacert = getattr(settings, 'OPENSTACK_SSL_CACERT', None)
    credentials = getattr(settings, 'IDM_USER_CREDENTIALS')

    LOG.debug(
        ('Creating a new internal keystoneclient '
         'connection to %s.'),
        endpoint)
    
    auth = v3.Password(
        username=credentials['username'],
        password=credentials['password'],
        project_name=credentials['project'],
        user_domain_id=domain,
        project_domain_id=domain,
        #insecure=insecure,
        #cacert=cacert,
        auth_url=endpoint)
        #debug=settings.DEBUG)

    return session.Session(auth=auth)

# USER REGISTRATION
def _find_user(keystone, email=None, username=None):
    if email:
        user = keystone.users.find(name=email)
        return user
    elif username:
        user_list = keystone.users.list()
        for user in user_list:
            if hasattr(user, 'username') and user.username == username:
                return user
        # consistent behaviour with the keystoneclient api
        msg = "No user matching email=%s." % email
        raise ks_exceptions.NotFound(404, msg)

def get_trial_role_assignments(request, domain='default', use_idm_account=True):
    trial_role = get_trial_role(request, use_idm_account=True)
    if trial_role:
        manager = internal_keystoneclient(request).role_assignments
        return manager.list(role=trial_role.id, domain=domain)
    else:
        return []

def register_user(request, name, username, password):
    keystone = internal_keystoneclient(request)
    #domain_name = getattr(settings, 'OPENSTACK_KEYSTONE_DEFAULT_DOMAIN', 'Default')
    #default_domain = keystone.domains.find(name=domain_name)
    # TODO(garcianavalon) better domain usage
    default_domain = 'default'
    # if not (check_user(name) or check_email(email)):
    new_user = keystone.user_registration.users.register_user(
        name,
        domain=default_domain,
        password=password,
        username=username)
    return new_user

def activate_user(request, user, activation_key):
    keystone = internal_keystoneclient(request)
    user = keystone.user_registration.users.activate_user(user, activation_key)
    return user

def change_password(request, user_email, new_password):
    keystone = internal_keystoneclient(request)
    user = _find_user(keystone, email=user_email)
    user = keystone.users.update(user, password=new_password, enabled=True)
    return user

def check_username(request, username):
    keystone = internal_keystoneclient(request)
    user = _find_user(keystone, username=username)
    return user

def check_email(request, email):
    keystone = internal_keystoneclient(request)
    user = _find_user(keystone, email=email)
    return user

def get_reset_token(request, user):
    keystone = internal_keystoneclient(request)
    token = keystone.user_registration.token.get_reset_token(user)
    return token

def new_activation_key(request, user):
    keystone = internal_keystoneclient(request)
    activation_key = keystone.user_registration.activation_key.new_activation_key(user)
    return activation_key

def reset_password(request, user, token, new_password):
    keystone = internal_keystoneclient(request)

    user = keystone.user_registration.users.reset_password(user, token, new_password)
    return user

def user_delete(request, user):
    keystone = internal_keystoneclient(request)
    keystone.users.delete(user)

# validate token
def validate_keystone_token(request, token):
    # TODO(garcianavalon) figure out if this method belongs to keystone client or if
    # there is a better way to do it/structure this
    keystone_url = getattr(settings, 'OPENSTACK_KEYSTONE_URL')
    endpoint = '/auth/tokens'
    url = keystone_url + endpoint
    headers = {
        'X-Auth-Token': token,
    }
    LOG.debug('API_KEYSTONE: GET to %s', url)
    response = requests.get(url, headers=headers)
    return response


# ROLES
def role_get(request, role_id):
    manager = api.keystone.keystoneclient(request, admin=True).fiware_roles.roles
    return manager.get(role_id)

def role_list(request, user=None, organization=None, application=None):
    manager = api.keystone.keystoneclient(request, admin=True).fiware_roles.roles
    return manager.list(user=user,
                        organization=organization,
                        application_id=application)

def role_create(request, name, is_internal=False, application=None, **kwargs):
    manager = api.keystone.keystoneclient(request, admin=True).fiware_roles.roles
    return manager.create(name=name,
                          is_internal=is_internal,
                          application=application,
                          **kwargs)

def role_update(request, role, name=None, is_internal=False, 
                application=None, **kwargs):
    manager = api.keystone.keystoneclient(request, admin=True).fiware_roles.roles
    return manager.update(role,
                          name=name,
                          is_internal=is_internal,
                          application=application,
                          **kwargs)

def role_delete(request, role_id):
    manager = api.keystone.keystoneclient(request, admin=True).fiware_roles.roles
    return manager.delete(role_id)


# ROLE-USERS
def add_role_to_user(request, role, user, organization, 
                     application, use_idm_account=False):
    if use_idm_account:
        manager = internal_keystoneclient(request).fiware_roles.roles
    else:
        manager = api.keystone.keystoneclient(
            request, admin=True).fiware_roles.roles
    return manager.add_to_user(role, user, organization, application)

def remove_role_from_user(request, role, user, organization, application,
                          use_idm_account=False):
    if use_idm_account:
        manager = internal_keystoneclient(request).fiware_roles.roles
    else:
        manager = api.keystone.keystoneclient(
            request, admin=True).fiware_roles.roles
    return manager.remove_from_user(role, user, organization, application)

def user_role_assignments(request, user=None, organization=None,
                          application=None):    
    manager = api.keystone.keystoneclient(
        request, admin=True).fiware_roles.role_assignments
    return manager.list_user_role_assignments(user=user,
                                              organization=organization,
                                              application=application)
# ROLE-ORGANIZATIONS
def add_role_to_organization(request, role, organization, 
                             application, use_idm_account=False):
    if use_idm_account:
        manager = internal_keystoneclient(request).fiware_roles.roles
    else:
        manager = api.keystone.keystoneclient(
            request, admin=True).fiware_roles.roles
    return manager.add_to_organization(role, organization, application)

def remove_role_from_organization(request, role, organization, application):
    manager = api.keystone.keystoneclient(
        request, admin=True).fiware_roles.roles
    return manager.remove_from_organization(role, organization, application)

def organization_role_assignments(request, organization=None,
                                  application=None):    
    manager = api.keystone.keystoneclient(
        request, admin=True).fiware_roles.role_assignments
    return manager.list_organization_role_assignments(
        organization=organization, application=application)

# ALLOWED ACTIONS
def list_user_allowed_roles_to_assign(request, user, organization):
    manager = api.keystone.keystoneclient(
        request, admin=True).fiware_roles.allowed
    return manager.list_user_allowed_roles_to_assign(user, organization)

def list_organization_allowed_roles_to_assign(request, organization):
    manager = api.keystone.keystoneclient(
        request, admin=True).fiware_roles.allowed
    return manager.list_organization_allowed_roles_to_assign(organization)

def list_user_allowed_applications_to_manage(request, user, organization):
    manager = api.keystone.keystoneclient(
        request, admin=True).fiware_roles.allowed
    return manager.list_user_allowed_applications_to_manage(user, organization)

def list_organization_allowed_applications_to_manage(request, organization):
    manager = api.keystone.keystoneclient(
        request, admin=True).fiware_roles.allowed
    return manager.list_organization_allowed_applications_to_manage(organization)

def list_user_allowed_applications_to_manage_roles(request, user, organization):
    manager = api.keystone.keystoneclient(
        request, admin=True).fiware_roles.allowed
    return manager.list_user_allowed_applications_to_manage_roles(
        user, organization)

def list_organization_allowed_applications_to_manage_roles(request, organization):
    manager = api.keystone.keystoneclient(
        request, admin=True).fiware_roles.allowed
    return manager.list_organization_allowed_applications_to_manage_roles(
        organization)

# PERMISSIONS
def permission_get(request, permission_id):
    manager = api.keystone.keystoneclient(
        request, admin=True).fiware_roles.permissions
    return manager.get(permission_id)

def permission_list(request, role=None, application=None):
    manager = api.keystone.keystoneclient(request, admin=True).fiware_roles.permissions
    return manager.list(role=role,
                        application_id=application)

def permission_create(request, name, is_internal=False, application=None, **kwargs):
    manager = api.keystone.keystoneclient(
        request, admin=True).fiware_roles.permissions
    return manager.create(name=name,
                          is_internal=is_internal,
                          application=application,
                          **kwargs)

def permission_update(request, permission, name=None, is_internal=False, 
                      application=None, **kwargs):
    manager = api.keystone.keystoneclient(
        request, admin=True).fiware_roles.permissions
    return manager.update(permission,
                          name=name,
                          is_internal=is_internal,
                          application_=application,
                          **kwargs)

def permission_delete(request, permission_id):
    manager = api.keystone.keystoneclient(
        request, admin=True).fiware_roles.permissions
    return manager.delete(permission_id)

def add_permission_to_role(request, permission, role):
    manager = api.keystone.keystoneclient(
        request, admin=True).fiware_roles.permissions
    return manager.add_to_role(permission=permission, role=role)

def remove_permission_from_role(request, permission, role):
    manager = api.keystone.keystoneclient(
        request, admin=True).fiware_roles.permissions
    return manager.remove_from_role(permission=permission, role=role)

# APPLICATIONS/CONSUMERS
def application_create(request, name, redirect_uris, scopes=['all_info'],
                       client_type='confidential', description=None,
                       grant_type='authorization_code', **kwargs):
    """ Registers a new consumer in the Keystone OAuth2 extension.

    In FIWARE applications is the name OAuth2 consumers/clients receive.
    """
    manager = api.keystone.keystoneclient(request, admin=True).oauth2.consumers
    return manager.create(name=name,
                          redirect_uris=redirect_uris,
                          description=description,
                          scopes=scopes,
                          client_type=client_type,
                          grant_type=grant_type,
                          **kwargs)

def application_list(request, user=None):
    manager = api.keystone.keystoneclient(
        request, admin=True).oauth2.consumers
    return manager.list(user=user)

def application_get(request, application_id, use_idm_account=False):
    if use_idm_account:
        manager = internal_keystoneclient(request).oauth2.consumers
    else:
        manager = api.keystone.keystoneclient(request, admin=True).oauth2.consumers
    return manager.get(application_id)

def application_update(request, consumer_id, name=None, description=None, client_type=None, 
                       redirect_uris=None, grant_type=None, scopes=None, **kwargs):
    manager = api.keystone.keystoneclient(request, admin=True).oauth2.consumers
    return manager.update(consumer=consumer_id,
                          name=name,
                          description=description,
                          client_type=client_type,
                          redirect_uris=redirect_uris,
                          grant_type=grant_type,
                          scopes=scopes,
                          **kwargs)

def application_delete(request, application_id, use_idm_account=False):
    if use_idm_account:
        manager = internal_keystoneclient(request)
    else:
        manager = api.keystone.keystoneclient(request, admin=True)

    return manager.oauth2.consumers.delete(application_id)


# OAUTH2 FLOW
def get_user_access_tokens(request, user):
    """Gets all authorized access_tokens for the user"""
    manager = internal_keystoneclient(request).oauth2.access_tokens

    return manager.list_for_user(user=user)

def request_authorization_for_application(request, application, 
                                          redirect_uri, scope=['all_info'], state=None):
    """ Sends the consumer/client credentials to the authorization server to ask
    a resource owner for authorization in a certain scope.

    :returns: a dict with all the data response from the provider, use it to populate
        a nice form for the user, for example.
    """
    LOG.debug('Requesting authorization for application: {0} with redirect_uri: {1} \
        and scope: {2} by user {3}'.format(application, redirect_uri, scope, request.user))
    manager = api.keystone.keystoneclient(request, admin=True).oauth2.authorization_codes
    response_dict = manager.request_authorization(consumer=application,
                                                  redirect_uri=redirect_uri,
                                                  scope=scope,
                                                  state=state)
    return  response_dict

def check_authorization_for_application(request, application,
                                        redirect_uri, scope=['all_info']):
    """ Checks if the requesting application already got authorized by the user, so we don't
        need to make all the steps again.

        The logic is that if the application already has a (valid) access token for that
    user and the scopes and redirect uris are registered then we can issue a new token for
    it.
    """
    LOG.debug('Checking if application {0} was already authorized by user {1}'.format(
                                                                application, request.user))
    manager = api.keystone.keystoneclient(request, admin=True).oauth2.access_tokens
    # FIXME(garcianavalon) the keystoneclient is not ready yet

def authorize_application(request, application, scopes=['all_info'], redirect=False):
    """ Give authorization from a resource owner to the consumer/client on the
    requested scopes.

    Example use case: when the user is redirected from the application website to
    us, the provider/resource owner we present a nice form. If the user accepts, we
    delegate to our Keystone backend, where the client credentials will be checked an
    an authorization_code returned if everything is correct.

    :returns: an authorization_code object, following the same pattern as other
        keystoneclient objects
    """
    LOG.debug('Authorizing application: {0} by user: {1}'.format(application, request.user))
    manager = api.keystone.keystoneclient(request, admin=True).oauth2.authorization_codes
    authorization_code = manager.authorize(consumer=application,
                                           scopes=scopes,
                                           redirect=redirect)
    return authorization_code

def obtain_access_token(request, consumer_id, consumer_secret, code,
                        redirect_uri):
    """ Exchange the authorization_code for an access_token.

    This token can be later exchanged for a keystone scoped token using the oauth2
    auth method. See the Keystone OAuth2 Extension documentation for more information
    about the auth plugin.

    :returns: an access_token object
    """
    # NOTE(garcianavalon) right now this method has no use because is a wrapper for a
    # method intented to be use by the client/consumer. For the IdM is much more 
    # convenient to simply forward the request, see forward_access_token_request method
    LOG.debug('Exchanging code: {0} by application: {1}'.format(code, consumer_id))
    manager = internal_keystoneclient(request).oauth2.access_tokens
    access_token = manager.create(consumer_id=consumer_id,
                                  consumer_secret=consumer_secret,
                                  authorization_code=code,
                                  redirect_uri=redirect_uri)
    return access_token

def forward_access_token_request(request):
    """ Forwards the request to the keystone backend."""
    # TODO(garcianavalon) figure out if this method belongs to keystone client or if
    # there is a better way to do it/structure this
    auth = request.META.get('HTTP_AUTHORIZATION', None)
    if not auth:
        raise django_exceptions.PermissionDenied()

    headers = {
        'Authorization': auth,
        'Content-Type': request.META['CONTENT_TYPE'],
    }
    body = request.body
    keystone_url = getattr(settings, 'OPENSTACK_KEYSTONE_URL') + '/OS-OAUTH2/access_token'
    LOG.debug('API_KEYSTONE: POST to {0} with body {1} and headers {2}'.format(keystone_url,
                                                                            body, headers))
    response = requests.post(keystone_url, data=body, headers=headers)
    return response


# FIWARE-IdM API CALLS
def forward_validate_token_request(request):
    """ Forwards the request to the keystone backend."""
    # TODO(garcianavalon) figure out if this method belongs to keystone client or if
    # there is a better way to do it/structure this
    keystone_url = getattr(settings, 'OPENSTACK_KEYSTONE_URL')
    endpoint = '/access-tokens/{0}'.format(request.GET.get('access_token'))
    url = keystone_url + endpoint
    LOG.debug('API_KEYSTONE: GET to {0}'.format(url))
    response = requests.get(url)
    return response

# CALLS FORBIDDEN FOR THE USER THAT NEED TO USE THE IDM ACCOUNT
# USERS
def user_get(request, user_id):
    manager = internal_keystoneclient(request).users
    return manager.get(user_id)

def user_list(request, project=None, domain=None, group=None, filters=None):
    manager = internal_keystoneclient(request).users

    kwargs = {
        "project": project,
        "domain": domain,
        "group": group
    }
    if filters is not None:
        kwargs.update(filters)
    return manager.list(**kwargs)

def user_update(request, user, use_idm_account=False, **data):
    if use_idm_account:
        manager = internal_keystoneclient(request).users
    else:
        manager = api.keystone.keystoneclient(
            request, admin=True).users

    if not data['password']:
        data.pop('password')
    user = manager.update(user, **data)
    if data.get('password') and user.id == request.user.id:
        return utils.logout_with_message(
            request,
            "Password changed. Please log in again to continue."
        )

# PROJECTS
def project_get(request, project_id):
    manager = internal_keystoneclient(request).projects
    return manager.get(project_id)

def project_list(request, domain=None, user=None, filters=None):
    manager = internal_keystoneclient(request).projects
    kwargs = {
        "domain": domain,
        "user": user
    }
    if filters is not None:
        kwargs.update(filters)
    return manager.list(**kwargs)

def project_create(request, name, description=None, enabled=None,
                   domain=None, **kwargs):
    manager = internal_keystoneclient(request).projects
    return manager.create(name, domain,
                          description=description,
                          enabled=enabled, **kwargs)

def project_update(request, project, name=None, description=None,
                  enabled=None, domain=None, **kwargs):
    manager = internal_keystoneclient(request).projects
    return manager.update(project, name=name, description=description,
                          enabled=enabled, domain=domain, **kwargs)

def project_delete(request, project):
    manager = internal_keystoneclient(request).projects
    return manager.delete(project)

# ROLES
def add_domain_user_role(request, user, role, domain):
    manager = internal_keystoneclient(request).roles
    return manager.grant(role, user=user, domain=domain)

def remove_domain_user_role(request, user, role, domain):
    manager = internal_keystoneclient(request).roles
    return manager.revoke(role, user=user, domain=domain)

def role_assignments_list(request, project=None, user=None, role=None,
                          group=None, domain=None, effective=False):
    manager = internal_keystoneclient(request).role_assignments
    return manager.list(project=project, user=user, role=role, group=group,
                        domain=domain, effective=effective)


# REGIONS AND ENDPOINT GROUPS
def region_list(request, use_idm_account=False):
    if use_idm_account:
        manager = internal_keystoneclient(request).regions
    else:
        manager = api.keystone.keystoneclient(
            request, admin=True).regions
    return manager.list()

def endpoint_group_list(request, use_idm_account=False):
    if use_idm_account:
        manager = internal_keystoneclient(request).endpoint_groups
    else:
        manager = api.keystone.keystoneclient(
            request, admin=True).endpoint_groups
    return manager.list()

def add_endpoint_group_to_project(request, project, endpoint_group, 
                                  use_idm_account=False):
    if use_idm_account:
        manager = internal_keystoneclient(request).endpoint_groups
    else:
        manager = api.keystone.keystoneclient(
            request, admin=True).endpoint_groups
    return manager.add_endpoint_group_to_project(
        project=project,
        endpoint_group=endpoint_group)

def delete_endpoint_group_from_project(request, project, endpoint_group, 
                                       use_idm_account=False):
    if use_idm_account:
        manager = internal_keystoneclient(request).endpoint_groups
    else:
        manager = api.keystone.keystoneclient(
            request, admin=True).endpoint_groups
    return manager.delete_endpoint_group_from_project(
        project=project,
        endpoint_group=endpoint_group)

def check_endpoint_group_in_project(request, project, endpoint_group, 
                                    use_idm_account=False):
    if use_idm_account:
        manager = internal_keystoneclient(request).endpoint_groups
    else:
        manager = api.keystone.keystoneclient(
            request, admin=True).endpoint_groups
    return manager.check_endpoint_group_in_project(
        project=project,
        endpoint_group=endpoint_group)

# NOTE(garcianavalon) this is documented but not suported in keystone...
# def list_endpoint_groups_for_project(request, project, use_idm_account=False):
#     if use_idm_account:
#         manager = internal_keystoneclient(request).endpoint_groups
#     else:
#         manager = api.keystone.keystoneclient(
#             request, admin=True).endpoint_groups
#     return manager.list_endpoint_groups_for_project(
#         project=project)

# USER CATEGORIES
def update_to_trial(request, user, duration=None):
    trial_role = get_trial_role(request, use_idm_account=True)
    date = str(datetime.date.today())
    keystone = internal_keystoneclient(request)
    if not duration:
        duration = settings.FIWARE_DEFAULT_DURATION[trial_role.name]
    keystone.users.update(user, trial_started_at=date, trial_duration=duration)
    add_domain_user_role(
        request,
        user=user,
        role=trial_role.id,
        domain='default')

def update_to_community(request, user, duration=None):
    community_role = get_community_role(request, use_idm_account=True)
    date = str(datetime.date.today())
    keystone = internal_keystoneclient(request)
    if not duration:
        duration = settings.FIWARE_DEFAULT_DURATION[community_role.name]
    keystone.users.update(user, community_started_at=date, community_duration=duration)
    add_domain_user_role(
        request,
        user=user,
        role=community_role.id,
        domain='default')

def update_to_basic(request, user):
    basic_role = get_basic_role(request, use_idm_account=True)
    add_domain_user_role(
        request,
        user=user,
        role=basic_role.id,
        domain='default')

# SPECIAL ROLES
# TODO(garcianavalon) refactorize for better reuse
class PickleObject():
    """Extremely simple class that holds the very little information we need
    to cache. Keystoneclient resource objects are not pickable.
    """
    def __init__(self, **kwds):
        self.__dict__.update(kwds)

def get_owner_role(request, use_idm_account=False):
    """Gets the owner role object from Keystone and caches it.

    Since this is configured in settings and should not change from request
    to request. Supports lookup by name or id.
    """
    owner = getattr(local_settings, "KEYSTONE_OWNER_ROLE", None)
    if owner and cache.get('owner_role') is None:
        # TODO(garcianavalon) use filters to filter by name
        try:
            if use_idm_account:
                manager = internal_keystoneclient(request)
            else:
                manager = api.keystone.keystoneclient(request, admin=True)
            roles = manager.roles.list()
        except Exception:
            roles = []
            exceptions.handle(request)
        for role in roles:
            if role.id == owner or role.name == owner:
                pickle_role = PickleObject(name=role.name, id=role.id)
                cache.set('owner_role', pickle_role, DEFAULT_OBJECTS_CACHE_TIME)
                break
    return cache.get('owner_role')

def get_member_role(request, use_idm_account=False):
    """Gets the member role object from Keystone and caches it.

    Since this is configured in settings and should not change from request
    to request. Supports lookup by name or id.
    """
    member = getattr(local_settings, "OPENSTACK_KEYSTONE_DEFAULT_ROLE", None)
    if member and cache.get('member_role') is None:
        # TODO(garcianavalon) use filters to filter by name
        try:
            if use_idm_account:
                manager = internal_keystoneclient(request)
            else:
                manager = api.keystone.keystoneclient(request, admin=True)
            roles = manager.roles.list()
        except Exception:
            roles = []
            exceptions.handle(request)
        for role in roles:
            if role.id == member or role.name == member:
                pickle_role = PickleObject(name=role.name, id=role.id)
                cache.set('member_role', pickle_role, DEFAULT_OBJECTS_CACHE_TIME)
                break
    return cache.get('member_role')

def get_trial_role(request, use_idm_account=False):
    """Gets the trial role object from Keystone and caches it.

    Since this is configured in settings and should not change from request
    to request. Supports lookup by name or id.
    """
    trial = getattr(local_settings, "KEYSTONE_TRIAL_ROLE", None)
    if trial and cache.get('trial_role') is None:
        # TODO(garcianavalon) use filters to filter by name
        try:
            if use_idm_account:
                manager = internal_keystoneclient(request)
            else:
                manager = api.keystone.keystoneclient(request, admin=True)
            roles = manager.roles.list()
        except Exception:
            roles = []
            exceptions.handle(request)
        for role in roles:
            if role.id == trial or role.name == trial:
                pickle_role = PickleObject(name=role.name, id=role.id)
                cache.set('trial_role', pickle_role, DEFAULT_OBJECTS_CACHE_TIME)
                break
    return cache.get('trial_role')

def get_basic_role(request, use_idm_account=False):
    """Gets the basic role object from Keystone and caches it.

    Since this is configured in settings and should not change from request
    to request. Supports lookup by name or id.
    """
    basic = getattr(local_settings, "KEYSTONE_BASIC_ROLE", None)
    if basic and cache.get('basic_role') is None:
        # TODO(garcianavalon) use filters to filter by name
        try:
            if use_idm_account:
                manager = internal_keystoneclient(request)
            else:
                manager = api.keystone.keystoneclient(request, admin=True)
            roles = manager.roles.list()
        except Exception:
            roles = []
            exceptions.handle(request)
        for role in roles:
            if role.id == basic or role.name == basic:
                pickle_role = PickleObject(name=role.name, id=role.id)
                cache.set('basic_role', pickle_role, DEFAULT_OBJECTS_CACHE_TIME)
                break
    return cache.get('basic_role')

def get_community_role(request, use_idm_account=False):
    """Gets the community role object from Keystone and caches it.

    Since this is configured in settings and should not change from request
    to request. Supports lookup by name or id.
    """
    community = getattr(local_settings, "KEYSTONE_COMMUNITY_ROLE", None)
    if community and cache.get('community_role') is None:
        # TODO(garcianavalon) use filters to filter by name
        try:
            if use_idm_account:
                manager = internal_keystoneclient(request)
            else:
                manager = api.keystone.keystoneclient(request, admin=True)
            roles = manager.roles.list()
        except Exception:
            roles = []
            exceptions.handle(request)
        for role in roles:
            if role.id == community or role.name == community:
                pickle_role = PickleObject(name=role.name, id=role.id)
                cache.set('community_role', pickle_role, DEFAULT_OBJECTS_CACHE_TIME)
                break
    return cache.get('community_role')

def get_provider_role(request):
    """Gets the provider role object from Keystone and caches it.

    Since this is configured in settings and should not change from request
    to request. Supports lookup by name or id.
    """
    provider = getattr(local_settings, "FIWARE_PROVIDER_ROLE", None)
    if provider and cache.get('provider_role') is None:
        try:
            roles = api.keystone.keystoneclient(request, 
                admin=True).fiware_roles.roles.list()
        except Exception:
            roles = []
            exceptions.handle(request)
        for role in roles:
            if role.id == provider or role.name == provider:
                pickle_role = PickleObject(name=role.name, id=role.id)
                cache.set('provider_role', pickle_role, DEFAULT_OBJECTS_CACHE_TIME)
                break
    return cache.get('provider_role')

def get_purchaser_role(request, use_idm_account=False):
    """Gets the purchaser role object from Keystone and caches it.

    Since this is configured in settings and should not change from request
    to request. Supports lookup by name or id.
    """
    purchaser = getattr(local_settings, "FIWARE_PURCHASER_ROLE", None)
    if purchaser and cache.get('purchaser_role') is None:
        try:
            if use_idm_account:
                manager = internal_keystoneclient(request)
            else:
                manager = api.keystone.keystoneclient(request, admin=True)
            roles = manager.fiware_roles.roles.list()
        except Exception:
            roles = []
            exceptions.handle(request)
        for role in roles:
            if role.id == purchaser or role.name == purchaser:
                pickle_role = PickleObject(name=role.name, id=role.id)
                cache.set('purchaser_role', pickle_role, DEFAULT_OBJECTS_CACHE_TIME)
                break
    return cache.get('purchaser_role')

def get_default_cloud_role(request, cloud_app_id, use_idm_account=False):
    """Gets the default_cloud role object from Keystone and caches it.

    Since this is configured in settings and should not change from request
    to request. Supports lookup by name or id.
    """
    default_cloud = getattr(local_settings, "FIWARE_DEFAULT_CLOUD_ROLE", None)
    if default_cloud and cache.get('default_cloud_role') is None:
        try:
            if use_idm_account:
                manager = internal_keystoneclient(request)
            else:
                manager = api.keystone.keystoneclient(request, admin=True)
            roles = manager.fiware_roles.roles.list(
                application=cloud_app_id)
        except Exception:
            roles = []
            exceptions.handle(request)
        for role in roles:
            if role.id == default_cloud or role.name == default_cloud:
                pickle_role = PickleObject(name=role.name, id=role.id)
                cache.set('default_cloud_role', 
                          pickle_role, 
                          DEFAULT_OBJECTS_CACHE_TIME)
                break
    return cache.get('default_cloud_role')

def get_idm_admin_app(request):
    idm_admin = getattr(local_settings, "FIWARE_IDM_ADMIN_APP", None)
    if idm_admin and cache.get('idm_admin') is None:
        try:
            apps = api.keystone.keystoneclient(request, 
                admin=True).oauth2.consumers.list()
        except Exception:
            apps = []
            exceptions.handle(request)
        for app in apps:
            if app.id == idm_admin or app.name == idm_admin:
                pickle_app = PickleObject(name=app.name, id=app.id)
                cache.set('idm_admin', pickle_app, DEFAULT_OBJECTS_CACHE_TIME)
                break
    return cache.get('idm_admin')

def get_fiware_cloud_app(request, use_idm_account=False):
    cloud_app = getattr(local_settings, "FIWARE_CLOUD_APP", None)
    if cloud_app and cache.get('cloud_app') is None:
        try:
            if use_idm_account:
                manager = internal_keystoneclient(request)
            else:
                manager = api.keystone.keystoneclient(request, admin=True)
            apps = manager.oauth2.consumers.list()
        except Exception:
            apps = []
            exceptions.handle(request)
        for app in apps:
            if app.id == cloud_app or app.name == cloud_app:
                pickle_app = PickleObject(name=app.name, id=app.id)
                cache.set('cloud_app', pickle_app, DEFAULT_OBJECTS_CACHE_TIME)
                break
    return cache.get('cloud_app')

def get_fiware_default_app(request, app_name, use_idm_account=False):
    if cache.get(app_name) is None:
        try:
            if use_idm_account:
                manager = internal_keystoneclient(request)
            else:
                manager = api.keystone.keystoneclient(request, admin=True)
            apps = manager.oauth2.consumers.list()
        except Exception:
            apps = []
            exceptions.handle(request)
        for app in apps:
            if app.name == app_name:
                pickle_app = PickleObject(name=app.name, id=app.id)
                cache.set(app_name, pickle_app, DEFAULT_OBJECTS_CACHE_TIME)
                break
    return cache.get(app_name)

def get_fiware_default_apps(request, use_idm_account=False):
    default_apps_names = getattr(local_settings, "FIWARE_DEFAULT_APPS", [])
    default_apps = []
    for app_name in default_apps_names:
        app = get_fiware_default_app(request, app_name, use_idm_account)
        if app:
            default_apps.append(app)
    return default_apps