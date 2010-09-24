import logging

from django_ogone import forms as ogone_forms
from django_ogone.ogone import Ogone
from django_ogone import ogone_settings  


def get_ogone_request(payment, currency, language,
                      accepturl='NONE', cancelurl='NONE', homeurl='NONE',
                      catalogurl='NONE', declineurl='NONE', 
                      exceptionurl='NONE'):    
    
    order = payment.order

    init_data = {
        'PSPID': ogone_settings.PSPID,
        'orderID': order.pk,
        'amount': u'%d' % (order.balance*100), 
        'language': language,
        'currency': currency,
        'cn': order.bill_addressee,
        'email': order.contact.email,
        'owneraddress': order.bill_street1,
        'ownerstate': order.bill_street2,
        'ownertown': order.bill_city,
        'ownerzip': order.bill_postal_code,
        'ownercty': order.bill_country,
        'com': unicode(order),
        # URLs need an appended slash!
        'accepturl': accepturl,
        'cancelurl': cancelurl,
        'declineurl': declineurl,
        'exceptionurl': exceptionurl,
        'homeurl': homeurl,
        'catalogurl': catalogurl,
    }
    
    init_data['SHASign'] = Ogone.sign(init_data)

    logging.debug('Sending the following data to Ogone: %s', init_data)
    form = ogone_forms.OgoneForm(init_data)
    
    return {'action': Ogone.get_action(), 'form': form}
    