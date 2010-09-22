from ogone.conf import settings
from ogone.forms import DynOgoneForm
from security import create_hash

def get_action():
    if settings.PRODUCTION == True:
        return settings.PROD.URL
    else:
        return settings.TEST_URL



def get_ogone_request(order_id, amount, currency, language,
                      accepturl='NONE', cancelurl='NONE', homeurl='NONE',
                      catalogurl='NONE', declineurl='NONE', 
                      exceptionurl='NONE'):    

    init_data = {
        'PSPID': settings.PSPID,
        'orderID': order_id,
        'amount': amount,
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
    