from ogone.conf import settings
from ogone.forms import DynOgoneForm
from ogone.security import create_hash

def get_action():
    if settings.PRODUCTION == True:
        return settings.PROD.URL
    else:
        return settings.TEST_URL

def get_ogon_request(order_id, amount, currency, language=settings.LANGUAGE):    
    signature = create_hash(order_id, amount, currency, settings.PSPID, 
        settings.SHA1_PRE_SECRET)
        
    init_data = {
        'orderID': order_id,
        'amount': amount,
        'currency': currency,
        'language': language,
        'SHASign': signature,
        # URLs need an appended slash!
        'accepturl': 'http://localhost:8000/checkout/ogone/accepted/', # make this a reverse lookup?
        'cancelurl': 'http://localhost:8000/checkout/ogone/status/',
        # 'declineurl': 'http://localhost:8000/checkout/ogone/status/',
        # 'exceptionurl': 'http://localhost:8000/checkout/ogone/status/',
        'homeurl': 'NONE', # needed to remove the 'back to web shop' button
        'catalogurl': 'NONE', # needed to remove the 'back to web shop' button
    }
    
    form = DynOgoneForm(initial_data=init_data, auto_id=False)
    return {'action': get_action(), 'form': form}