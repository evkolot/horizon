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
from django.core.urlresolvers import reverse_lazy
from django.contrib.auth.decorators import login_required  # noqa
from django.shortcuts import redirect
from django.template.loader import render_to_string
from django.views.generic.base import TemplateView
from django.views.generic.edit import FormView

from keystoneclient import exceptions as ks_exceptions

from horizon import messages
from horizon import exceptions

from openstack_auth import views as openstack_auth_views

from openstack_dashboard import fiware_api
from openstack_dashboard.fiware_auth import forms as fiware_forms

from openstack_dashboard.local import local_settings

LOG = logging.getLogger('idm_logger')
EMAIL_HTML_TEMPLATE = 'email/base_email.html'
EMAIL_TEXT_TEMPLATE = 'email/base_email.txt'

RESET_PASSWORD_HTML_TEMPLATE = 'email/reset_password.html'
RESET_PASSWORD_TXT_TEMPLATE = 'email/reset_password.txt'

ACTIVATION_HTML_TEMPLATE = 'email/activation.html'
ACTIVATION_TXT_TEMPLATE = 'email/activation.txt'


class TemplatedEmailMixin(object):
    # TODO(garcianavalon) as settings
    
    def send_html_email(self, to, from_email, subject, **kwargs):
        LOG.debug('Sending email to %s with subject %s', to, subject)
        text_content = render_to_string(EMAIL_TEXT_TEMPLATE, dictionary=kwargs)
        html_content = render_to_string(EMAIL_HTML_TEMPLATE, dictionary=kwargs)
        msg = EmailMultiAlternatives(subject, text_content, from_email, to)
        msg.attach_alternative(html_content, "text/html")
        msg.send()

class _RequestPassingFormView(FormView, TemplatedEmailMixin):
    """
    A version of FormView which passes extra arguments to certain
    methods, notably passing the HTTP request nearly everywhere, to
    enable finer-grained processing.
    
    """
    def post(self, request, *args, **kwargs):
        # Pass request to get_form_class and get_form for per-request
        # form control.
        form_class = self.get_form_class(request)
        form = self.get_form(form_class)
        if form.is_valid():
            # Pass request to form_valid.
            return self.form_valid(request, form)
        else:
            return self.form_invalid(form)

    def get_form_class(self, request=None):
        return super(_RequestPassingFormView, self).get_form_class()

    def get_form_kwargs(self, request=None, form_class=None):
        return super(_RequestPassingFormView, self).get_form_kwargs()

    def get_initial(self, request=None):
        return super(_RequestPassingFormView, self).get_initial()

    def get_success_url(self, request=None, user=None):
        # We need to be able to use the request and the new user when
        # constructing success_url.
        return super(_RequestPassingFormView, self).get_success_url()

    def form_valid(self, form, request=None):
        return super(_RequestPassingFormView, self).form_valid(form)

    def form_invalid(self, form, request=None):
        return super(_RequestPassingFormView, self).form_invalid(form)


class RegistrationView(_RequestPassingFormView):
    """Creates a new user in the backend. Then redirects to the log-in page.
    Once registered, defines the URL where to redirect for activation
    """
    form_class = fiware_forms.RegistrationForm
    http_method_names = ['get', 'post', 'head', 'options', 'trace']
    success_url = reverse_lazy('login')
    template_name = 'auth/registration/registration.html'

    def dispatch(self, request, *args, **kwargs):
        if request.user.username:
            return redirect('horizon:user_home')
        return super(RegistrationView, self).dispatch(request, *args, **kwargs)
    
    def get_form_kwargs(self, request=None, form_class=None):
        kwargs = super(RegistrationView, self).get_form_kwargs()
        kwargs['request'] = request
        return kwargs
        
    def form_valid(self, request, form):
        new_user = self.register(request, **form.cleaned_data)
        if new_user:
            success_url = self.get_success_url(request, new_user)
            # success_url must be a simple string, no tuples
            return redirect(success_url)
        # TODO(garcianavalon) do something if new_user is None like
        # redirect to login or to sign_up

    # We have to protect the entire "cleaned_data" dict because it contains the
    # password and confirm_password strings.
    def register(self, request, **cleaned_data):
        LOG.info('Singup user %s.', cleaned_data['username'])
        # delegate to the manager to create all the stuff
        try:
            new_user = fiware_api.keystone.register_user(
                request,
                name=cleaned_data['email'],
                password=cleaned_data['password1'],
                username=cleaned_data['username'])
            LOG.debug('user %s created.', 
                cleaned_data['username'])

            # Grant trial or basic role in the domain
            if cleaned_data['trial']:
                fiware_api.keystone.update_to_trial(
                    request, new_user.id)
            else:
                fiware_api.keystone.update_to_basic(
                    request, new_user.id)

            # Grant purchaser to user's cloud organization in all 
            # default apps. If trial requested, also in Cloud
            default_apps = fiware_api.keystone.get_fiware_default_apps(request)

            if cleaned_data['trial']:
                cloud_app = fiware_api.keystone.get_fiware_cloud_app(
                    request, use_idm_account=True)
                default_apps.append(cloud_app)

            purchaser = fiware_api.keystone.get_purchaser_role(
                request, use_idm_account=True)

            for app in default_apps:
                fiware_api.keystone.add_role_to_organization(
                    request, 
                    role=purchaser, 
                    organization=new_user.cloud_project_id,
                    application=app.id, 
                    use_idm_account=True)
                LOG.debug('Granted purchaser to org %s in app %s',
                          new_user.cloud_project_id,
                          app.id)    

            # Grant a public role in cloud app to user in his/her
            # cloud organization if trial requested
            # and activate the Spain2 region
            if cleaned_data['trial']:
                default_cloud_role = \
                    fiware_api.keystone.get_default_cloud_role(
                        request, cloud_app, use_idm_account=True)

                if default_cloud_role:
                    fiware_api.keystone.add_role_to_user(
                        request, 
                        role=default_cloud_role.id, 
                        user=new_user.id,
                        organization=new_user.cloud_project_id, 
                        application=cloud_app.id, 
                        use_idm_account=True)
                    LOG.debug('granted default cloud role')
                else:
                    LOG.debug('default cloud role not found')

                # TODO(garcianavalon) as setting!
                region_id = 'Spain2'
                endpoint_groups = fiware_api.keystone.endpoint_group_list(
                    request, use_idm_account=True)
                region_group = next(group for group in endpoint_groups
                    if group.filters.get('region_id', None) == region_id)

                if not region_group:
                    messages.error(
                        request, 'There is no endpoint group defined for that region')
                    return
        
                fiware_api.keystone.add_endpoint_group_to_project(
                    request,
                    project=new_user.cloud_project_id,
                    endpoint_group=region_group,
                    use_idm_account=True)

            self.send_activation_email(new_user)

            msg = ('Account created succesfully, check your email for'
                ' the confirmation link.')
            messages.success(request, msg)
            return new_user

        except Exception:
            msg = ('Unable to create user.')
            LOG.warning(msg)
            messages.error(request, msg)
            exceptions.handle(request, msg)

    def send_activation_email(self, user):
        # TODO(garcianavalon) subject, message and from_email as settings/files
        subject = '[FIWARE Lab] Welcome to FIWARE'
        # Email subject *must not* contain newlines
        subject = ''.join(subject.splitlines())
        context = {
            'activation_url':('{0}/activate/?activation_key={1}&user={2}'
                '').format(_get_current_domain(),user.activation_key, user.id),
            'user_name':user.username,
        }
        text_content = render_to_string(ACTIVATION_TXT_TEMPLATE, 
                                        dictionary=context)
        html_content = render_to_string(ACTIVATION_HTML_TEMPLATE, 
                                        dictionary=context)
        #send a mail for activation
        self.send_html_email(
            to=[user.name],
            from_email='no-reply@account.lab.fiware.org',
            subject=subject,
            content={'text': text_content, 'html': html_content})

class ActivationView(TemplateView):
    http_method_names = ['get']
    template_name = 'auth/activation/activate.html'
    success_url = reverse_lazy('login')

    def dispatch(self, request, *args, **kwargs):
        if request.user.username:
            return redirect('horizon:user_home')
        return super(ActivationView, self).dispatch(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        activated_user = self.activate(request, *args, **kwargs)
        if activated_user:
            return redirect(self.success_url)
        return super(ActivationView, self).get(request, *args, **kwargs)

    def activate(self, request):
        activation_key = request.GET.get('activation_key')
        user = request.GET.get('user')
        LOG.info('Requested activation for key %s.', activation_key)
        try:
            activated_user = fiware_api.keystone.activate_user(
                request, user, activation_key)
            LOG.debug('user %s was successfully activated.', 
                      activated_user.username)
            messages.success(request, 
                             ('User "%s" was successfully activated.') 
                             %activated_user.username)
            return activated_user
        except Exception:
            msg = ('Unable to activate user.')
            LOG.warning(msg)
            exceptions.handle(request, msg)

class RequestPasswordResetView(_RequestPassingFormView):
    form_class = fiware_forms.EmailForm
    template_name = 'auth/password/request.html'
    success_url = reverse_lazy('login')

    def dispatch(self, request, *args, **kwargs):
        if request.user.username:
            return redirect('horizon:user_home')
        return super(RequestPasswordResetView, self).dispatch(
            request, *args, **kwargs)

    def form_valid(self, request, form):
        success = self._create_reset_password_token(request, 
            form.cleaned_data['email'])
        if success:
            return super(RequestPasswordResetView, self).form_valid(form)
        else:
            return self.get(request) # redirect to itself

    def _create_reset_password_token(self, request, email):
        LOG.info('Creating reset token for {0}.'.format(email))
        try:
            user = fiware_api.keystone.check_email(request, email)

            if not user.enabled:
                msg = ('The email address you have specific is registered but not '
                    'activated. Please check your email for the activation link '
                    'or request a new one. If your problem '
                    'persits, please contact: fiware-lab-help@lists.fiware.org')
                raise messages.error(request, msg)

            reset_password_token = fiware_api.keystone.get_reset_token(request, user)
            token = reset_password_token.id
            user = reset_password_token.user
            self.send_reset_email(email, token, user)
            messages.success(request, ('Reset email send to %s') % email)
            return True

        except ks_exceptions.NotFound:
            LOG.debug('email address %s is not registered', email)
            msg = ('Sorry. You have specified an email address that is not '
                'registered to any our our user accounts. If your problem '
                'persits, please contact: fiware-lab-help@lists.fiware.org')
            messages.error(request, msg)

        except Exception:
            msg = ('An error occurred, try again later.')
            messages.error(request, msg)
            
        return False

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
            from_email='no-reply@account.lab.fiware.org',
            subject=subject, 
            content={'text': text_content, 'html': html_content})


class ResetPasswordView(_RequestPassingFormView):
    form_class = fiware_forms.ChangePasswordForm
    template_name = 'auth/password/reset.html'
    success_url = reverse_lazy('login')

    def dispatch(self, request, *args, **kwargs):
        if request.user.username:
            return redirect('horizon:user_home')
        self.token = request.GET.get('token')
        self.email = request.GET.get('email')
        return super(ResetPasswordView, self).dispatch(
            request, *args, **kwargs)
    
    def get_context_data(self, **kwargs):
        context = super(ResetPasswordView, self).get_context_data(**kwargs)
        context['token'] = self.token
        context['email'] = self.email
        return context

    def form_valid(self, request, form):
        password = form.cleaned_data['password1']
        token = self.token
        user = self._reset_password(request, token, password)
        if user:
            return super(ResetPasswordView, self).form_valid(form)
        return self.get(request) # redirect to itself

    def _reset_password(self, request, token, password):
        LOG.info('Reseting password for token {0}.'.format(token))
        user_email = self.email
        try:
            user = fiware_api.keystone.check_email(request, user_email)
            user = fiware_api.keystone.reset_password(request, user, token, password)
            if user:
                messages.success(request, ('password successfully changed.'))
                return user
        except Exception:
            msg = ('Unable to change password.')
            LOG.warning(msg)
            exceptions.handle(request, msg)
        return None

class ResendConfirmationInstructionsView(_RequestPassingFormView):
    form_class = fiware_forms.EmailForm
    template_name = 'auth/registration/confirmation.html'
    success_url = reverse_lazy('login')

    def dispatch(self, request, *args, **kwargs):
        if request.user.username:
            return redirect('horizon:user_home')
        return super(ResendConfirmationInstructionsView, self).dispatch(
            request, *args, **kwargs)

    def form_valid(self, request, form):
        success = self._resend_confirmation_email(request, 
            form.cleaned_data['email'])
        if success:
            return super(ResendConfirmationInstructionsView, self).form_valid(form)
        else:
            return self.get(request) # redirect to itself
            
    def _resend_confirmation_email(self, request, email):
        try:
            user = fiware_api.keystone.check_email(request, email)

            if user.enabled:
                msg = ('Email was already confirmed, please try signing in')
                LOG.debug('email address %s was already confirmed', email)
                messages.error(request, msg)
                return False

            activation_key = fiware_api.keystone.new_activation_key(request, user)

            self.send_reactivation_email(user, activation_key)
            msg = ('Resended confirmation instructions to %s') %email
            messages.success(request, msg)
            return True

        except ks_exceptions.NotFound:
            LOG.debug('email address %s is not registered', email)
            msg = ('Sorry. You have specified an email address that is not '
                'registered to any our our user accounts. If your problem '
                'persits, please contact: fiware-lab-help@lists.fiware.org')
            messages.error(request, msg)

        except Exception:
            msg = ('An error occurred, try again later.')
            messages.error(request, msg)
        
        return False

    def send_reactivation_email(self, user, activation_key):
        # TODO(garcianavalon) subject, message and from_email as settings/files
        subject = '[FIWARE Lab] Welcome to FIWARE'
        # Email subject *must not* contain newlines
        subject = ''.join(subject.splitlines())
        context = {
            'activation_url':('{0}/activate/?activation_key={1}&user={2}'
                '').format(_get_current_domain(),activation_key.id, user.id),
            'user_name':user.username,
        }
        text_content = render_to_string(ACTIVATION_TXT_TEMPLATE, 
                                        dictionary=context)
        html_content = render_to_string(ACTIVATION_HTML_TEMPLATE, 
                                        dictionary=context)
        #send a mail for activation
        self.send_html_email(
            to=[user.name],
            from_email='no-reply@account.lab.fiware.org',
            subject=subject, 
            content={'text': text_content, 'html': html_content})

@login_required
def switch(request, tenant_id, **kwargs):
    """Wrapper for ``openstack_auth.views.switch`` to add a message
    for the user.
    """
    user_organization = request.user.default_project_id
    response = openstack_auth_views.switch(request, tenant_id, **kwargs)
    if tenant_id != user_organization:
        organization_name = next(o.name for o in request.organizations 
                         if o.id == tenant_id)
        msg = ("Your identity has changed. Now you are acting on behalf "
               "of the \"{0}\" organization. Use the top-right menu to " 
               "regain your identity as individual user.").format(
               organization_name)
        messages.info(request, msg)
    return response

def _get_current_domain():
    if getattr(local_settings, 'ALLOWED_HOSTS', None):
        return 'https://'+local_settings.ALLOWED_HOSTS[0]
    else: 
        return 'http://0.0.0.0:8000'