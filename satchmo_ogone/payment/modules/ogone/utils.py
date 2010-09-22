from ogone.conf import settings
from ogone.forms import DynOgoneForm
from security import create_hash

def get_action():
    if settings.PRODUCTION == True:
        return settings.PROD.URL
    else:
        return settings.TEST_URL


def get_ogone_request(order, currency, language,
                      accepturl='NONE', cancelurl='NONE', homeurl='NONE',
                      catalogurl='NONE', declineurl='NONE', 
                      exceptionurl='NONE'):    

    init_data = {
        'PSPID': settings.PSPID,
        'orderID': order.id,
        'amount': u'%d' % (order.balance*100), 
        'cn': order.bill_addressee,
        'email': order.contact.email,
        'owneraddress': order.bill_street1,
        'ownerstate': order.bill_street2,
        'ownertown': order.bill_city,
        'ownerzip': order.bill_postal_code,
        'ownercty': order.bill_country_name,
        'com': unicode(order),
        'currency': currency,
        'language': language,
        # URLs need an appended slash!
        'accepturl': accepturl,
        'cancelurl': cancelurl,
        'declineurl': declineurl,
        'exceptionurl': exceptionurl,
        'homeurl': homeurl,
        'catalogurl': catalogurl,
    }
    
    signature = create_hash(init_data, settings.SHA1_PRE_SECRET)
    
    init_data.update({'SHASign': signature})
    
    form = DynOgoneForm(initial_data=init_data, auto_id=False)
    return {'action': get_action(), 'form': form}
    