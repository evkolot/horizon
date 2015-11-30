from django.conf.urls import patterns
from django.conf.urls import url

from openstack_dashboard.dashboards.settings.multisettings \
    import views as settings_views


urlpatterns = patterns('',
    url(r'^$', settings_views.MultiFormView.as_view(), name='index'),
    url(r'^accountstatus/$', settings_views.AccountStatusView.as_view(), name='status'),
)
