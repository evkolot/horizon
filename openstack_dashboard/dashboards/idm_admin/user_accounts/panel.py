from django.utils.translation import ugettext_lazy as _

import horizon

from openstack_dashboard.dashboards.idm_admin import dashboard


class User_Accounts(horizon.Panel):
    name = _("User_Accounts")
    slug = "user_accounts"


dashboard.Idm_Admin.register(User_Accounts)
