from django.conf.urls import patterns
from django.conf.urls import url

from openstack_dashboard.dashboards.help_about.help_about \
    import views as help_about_views


urlpatterns = patterns('',
    url(r'^$', help_about_views.MultiItemView.as_view(), name='index'),
)
