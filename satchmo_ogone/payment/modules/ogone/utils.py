cd import logging

from django_ogone.ogone import Ogone

def get_ogone_request(payment, settings, language,
                      accepturl='NONE', cancelurl='NONE', homeurl='NONE',
                      catalogurl='NONE', declineurl='NONE', 
                      exceptionurl='NONE'):    
    
    order = payment.order

    init_data = {
        'PSPID': settings.PSPID,
        'orderID': payment.pk,
        'amount': u'%d' % (order.balance*100), 
        'language': language,
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
        
    return {'action': Ogone.get_action(settings=settings), 
            'form': Ogone.get_form(init_data, settings=settings)}
    