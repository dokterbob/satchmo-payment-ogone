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
    default = 'EUR'),

StringValue(PAYMENT_GROUP,
    'PSPID',
    description=_('PSPID'),
    help_text=_('Ogone account name')),

StringValue(PAYMENT_GROUP,
    'SHA_PRE_SECRET',
    description=_('Outgoing secret'),
    help_text=_('Secret used for outgoing payment requests.'),),

StringValue(PAYMENT_GROUP,
    'SHA_POST_SECRET',
    description=_('Incoming secret'),
    help_text=_('Secret used for incoming payment status updates.'),),

StringValue(PAYMENT_GROUP,
    'HASH_METHOD',
    description=_('Hash method'),
    help_text=_('Hashing algorithm used for signing messages.'),
    default='sha512'),


StringValue(PAYMENT_GROUP,
    'PROD_URL',
    description=_('Post URL'),
    help_text=_('The Ogone URL for real transaction posting.'),
    default="https://secure.ogone.com/ncol/prod/orderstandard.asp"),

StringValue(PAYMENT_GROUP,
    'TEST_URL',
    description=_('Ogone test URL'),
    help_text=_('The Ogone URL for test transaction posting.'),
    default="https://secure.ogone.com/ncol/test/orderstandard.asp"),

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
