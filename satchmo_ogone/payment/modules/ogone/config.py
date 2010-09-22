from livesettings import *
from django.utils.translation import ugettext_lazy as _

PAYMENT_GROUP = ConfigurationGroup('PAYMENT_OGONE',
    _('Ogone Payment Module Settings'),
    ordering = 101)

config_register_list(

StringValue(PAYMENT_GROUP,
    'CURRENCY_CODE',
    description=_('Currency Code'),
    help_text=_('Currency code for Ogone transactions.'),
    default = 'USD'),

StringValue(PAYMENT_GROUP,
    'POST_URL',
    description=_('Post URL'),
    help_text=_('The Ogone URL for real transaction posting.'),
    default="https://www.ogone.com/cgi-bin/webscr"),

StringValue(PAYMENT_GROUP,
    'POST_TEST_URL',
    description=_('Post URL'),
    help_text=_('The Ogone URL for test transaction posting.'),
    default="https://www.sandbox.ogone.com/cgi-bin/webscr"),

StringValue(PAYMENT_GROUP,
    'BUSINESS',
    description=_('Ogone account email'),
    help_text=_('The email address for your ogone account'),
    default=""),

StringValue(PAYMENT_GROUP,
    'BUSINESS_TEST',
    description=_('Ogone test account email'),
    help_text=_('The email address for testing your ogone account'),
    default=""),

StringValue(PAYMENT_GROUP,
    'RETURN_ADDRESS',
    description=_('Return URL'),
    help_text=_('Where Ogone will return the customer after the purchase is complete.  This can be a named url and defaults to the standard checkout success.'),
    default="satchmo_checkout-success"),

BooleanValue(PAYMENT_GROUP,
    'LIVE',
    description=_("Accept real payments"),
    help_text=_("False if you want to be in test mode"),
    default=False),

ModuleValue(PAYMENT_GROUP,
    'MODULE',
    description=_('Implementation module'),
    hidden=True,
    default = 'satchmo_ogone.payment.modules.ogone'),

StringValue(PAYMENT_GROUP,
    'KEY',
    description=_("Module key"),
    hidden=True,
    default = 'OGONE'),

StringValue(PAYMENT_GROUP,
    'LABEL',
    description=_('English name for this group on the checkout screens'),
    default = 'Ogone',
    help_text = _('This will be passed to the translation utility')),

StringValue(PAYMENT_GROUP,
    'URL_BASE',
    description=_('The url base used for constructing urlpatterns which will use this module'),
    default = '^ogone/'),

BooleanValue(PAYMENT_GROUP,
    'EXTRA_LOGGING',
    description=_("Verbose logs"),
    help_text=_("Add extensive logs during post."),
    default=False)
)

PAYMENT_GROUP['TEMPLATE_OVERRIDES'] = {
    'shop/checkout/confirm.html' : 'shop/checkout/ogone/confirm.html',
}
