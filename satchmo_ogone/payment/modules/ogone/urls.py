from django.conf.urls.defaults import patterns
from satchmo_store.shop.satchmo_settings import get_satchmo_setting

ssl = get_satchmo_setting('SSL', default_value=False)

urlpatterns = patterns('',
     (r'^$', 'satchmo_ogone.payment.modules.ogone.views.pay_ship_info', {'SSL': ssl}, 'OGONE_satchmo_checkout-step2'),
     (r'^confirm/$', 'satchmo_ogone.payment.modules.ogone.views.confirm_info', {'SSL': ssl}, 'OGONE_satchmo_checkout-step3'),
     (r'^success/$', 'payment.views.checkout.success', {'SSL': ssl}, 'OGONE_satchmo_checkout-success'),
     # (r'^status/$', 'satchmo_ogone.payment.modules.ogone.views.status', {'SSL': ssl}, 'OGONE_satchmo_checkout-status'),
     (r'^confirmorder/$', 'payment.views.confirm.confirm_free_order',
         {'SSL' : ssl, 'key' : 'OGONE'}, 'OGONE_satchmo_checkout_free-confirm')
)
