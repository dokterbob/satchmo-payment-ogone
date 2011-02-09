import sys

from decimal import Decimal
from django.conf import settings
from django.core import urlresolvers
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.utils.http import urlencode
from django.utils.translation import ugettext as _
from django.views.decorators.cache import never_cache
from livesettings import config_get_group, config_value
from payment.config import gateway_live
from payment.utils import get_processor_by_key
from payment.views import payship
from payment.views.checkout import success as success_base, \
                                              failure as failure_base
from satchmo_store.shop.models import Cart
from satchmo_store.shop.models import Order, OrderPayment, \
                                      OrderAuthorization, OrderStatus
from satchmo_utils.dynamic import lookup_url, lookup_template
from sys import exc_info
from traceback import format_exception
import logging
import urllib2
from django.views.decorators.csrf import csrf_exempt

from satchmo_ogone.payment.modules.ogone.utils import get_ogone_request
from django_ogone import status_codes

log = logging.getLogger('satchmo_payment_ogone')

from django.contrib.sites.models import Site

from django_ogone.ogone import Ogone

def reverse_full_url(view, *args, **kwargs):
    current_site = Site.objects.get_current()
    protocol = kwargs.pop('secure', False) and 'https' or 'http'
    
    relative_url = urlresolvers.reverse(view, *args, **kwargs)
    
    return '%s://%s%s' % (protocol, current_site.domain, relative_url)

def get_ogone_settings():
    payment_module = config_get_group('PAYMENT_OGONE')

    class Settings(object):
        SHA_PRE_SECRET = payment_module.SHA_PRE_SECRET.value
        SHA_POST_SECRET = payment_module.SHA_POST_SECRET.value
        HASH_METHOD = payment_module.HASH_METHOD.value
        PRODUCTION = payment_module.LIVE.value
        PSPID = payment_module.PSPID.value
        CURRENCY = payment_module.CURRENCY_CODE.value
        TEST_URL = payment_module.TEST_URL.value
        PROD_URL = payment_module.PROD_URL.value
        
    return Settings

@never_cache
def pay_ship_info(request):
    return payship.base_pay_ship_info(request,
        config_get_group('PAYMENT_OGONE'), payship.simple_pay_ship_process_form,
        'shop/checkout/ogone/pay_ship.html')


@never_cache
def confirm_info(request):
    payment_module = config_get_group('PAYMENT_OGONE')

    try:
        order = Order.objects.from_request(request)
    except Order.DoesNotExist:
        url = lookup_url(payment_module, 'satchmo_checkout-step1')
        return HttpResponseRedirect(url)

    tempCart = Cart.objects.from_request(request)
    if tempCart.numItems == 0 and not order.is_partially_paid:
        template = lookup_template(payment_module, 'shop/checkout/empty_cart.html')
        return render_to_response(template,
                                  context_instance=RequestContext(request))

    # Check if the order is still valid
    if not order.validate(request):
        context = RequestContext(request,
                                 {'message': _('Your order is no longer valid.')})
        return render_to_response('shop/404.html', context_instance=context)

    template = lookup_template(payment_module, 'shop/checkout/ogone/confirm.html')

    processor_module = payment_module.MODULE.load_module('processor')
    processor = processor_module.PaymentProcessor(payment_module)
    
    pending_payment = processor.create_pending_payment(order=order)
    payment = pending_payment.capture
    
    log.debug('Creating payment %s for order %s', payment, order)
    
    success_url = reverse_full_url('OGONE_satchmo_checkout-success')
    failure_url = reverse_full_url('OGONE_satchmo_checkout-failure')
    homeurl = reverse_full_url('satchmo_shop_home')
    catalogurl = reverse_full_url('satchmo_category_index')
    
    # Get Ogone settings from Satchmo
    settings = get_ogone_settings()
    
    context = get_ogone_request(payment, 
                                settings,
                                accepturl=success_url,
                                cancelurl=failure_url,
                                declineurl=failure_url,
                                exceptionurl=failure_url,
                                homeurl=homeurl,
                                catalogurl=catalogurl,
                                language=getattr(request, 'LANGUAGE_CODE', 'en_US'))
    
    context.update({'order': order})
    
    return render_to_response(template, context, RequestContext(request))



@csrf_exempt
def order_status_update(request, order=None):
    '''
    Updates the order status with ogone data.
    There are two ways of reaching this flow
    
    - payment redirect (user gets redirected through this flow)
    - ogone server side call (in case of problems ogone will post to our server
    with an updated version ofo the payment status)
    '''

    log.debug('Attempting to update status information',
              extra={'request': request})

    params = request.GET or request.POST
    if params.get('orderID', False):
        # Get Ogone settings from Satchmo
        ogone = Ogone(params, settings=get_ogone_settings())
    
        # Make sure we check the data, and raise an exception if its wrong
        ogone.is_valid()

        # Fetch parsed params
        parsed_params = ogone.parse_params()   

        log.debug('We have found a valid status feedback message.',
                  extra={'data':{'parsed_params': parsed_params}})
    
        # Get the order 
        payment_id = ogone.get_order_id()
        
        try:
            ogone_payment = OrderPayment.objects.get(pk=payment_id)
        except OrderPayment.DoesNotExist:
            log.warning('Payment with payment_id=%d not found.', payment_id)
            
            return HttpResponse('')
        
        ogone_order = ogone_payment.order
        
        assert not order or (ogone_order.pk == order.pk), \
            'Ogone\'s order and my order are different objects.'
        
        log.debug('Found order %s for payment %s in processing feedback.',
                  ogone_order, ogone_payment)
        
        # Do order processing and status comparisons here
        processor = get_processor_by_key('PAYMENT_OGONE')    
        
        status_code = parsed_params['STATUS']
        status_num = int(status_code)
        
        assert status_num, 'No status number.'
        
        log.debug('Recording status: %s (%s)',
                  status_codes.STATUS_DESCRIPTIONS[status_num],
                  status_code)
        
        # Prepare parameters for recorder
        params = {'amount': Decimal(parsed_params['AMOUNT']),
                  'order': ogone_order,
                  'transaction_id': parsed_params['PAYID'],
                  'reason_code': status_code }
        
        if status_num in (9, 91):
            # Payment was captured
            try:
                authorization = OrderAuthorization.objects.get(order=ogone_order, \
                                                               transaction_id=parsed_params['PAYID'], \
                                                               complete=False)
                params.update({'authorization': authorization})
            except OrderAuthorization.DoesNotExist:
                pass
            
            processor.record_payment(**params)

            # Only change the status when it was empty or 'New' before.
            def _latest_status(order):
                    try:
                        curr_status = order.orderstatus_set.latest()
                        return curr_status.status
                    except OrderStatus.DoesNotExist:
                        return ''

            if _latest_status(order) in ('', 'New'):
                ogone_order.add_status(status='Billed', 
                    notes=_("Payment accepted by Ogone."))

            
        elif status_num in (5, 51):
            # Record authorization
            processor.record_authorization(**params)
        
        elif status_num in (4, 41):
            # We're still waiting
            ogone_order.add_status(status='New', 
                notes=_("Payment is being processed by Ogone."))
        
        else:
            # Record failure
            processor.record_failure(**params)
            
            if status_num in (1,):
                # Order cancelled

                ogone_order.add_status(status='Cancelled', 
                    notes=_("Order cancelled through Ogone."))

            elif status_num in (2, 93):
                # Payment declined

                ogone_order.add_status(status='Blocked', 
                    notes=_("Payment declined by Ogone."))
            
            elif status_num in (52, 92):
                log.warning('Payment of order %s (ID: %d) uncertain. Status: %s (%d)',
                    ogone_order, ogone_order.pk, 
                    status_codes.STATUS_DESCRIPTIONS[status_num], status_num)
            
            else:
                log.warning('Uknown status code %d found for order %s.',
                            status_num, 
                            ogone_order,
                            exc_info=sys.exc_info()
                           )
    else:
        log.warning('This response does not look valid, orderID not found.',
                    extra={'request': request})
    
    # Return an empty HttpResponse
    return HttpResponse('')


@csrf_exempt
def success(request):
    """ As we confirm to the user their payment has succeeded, we must make
        sure that their items are directly removed from the shopping cart
        as well.
        
        Also, we attempt to capture order status parameters here.
    """
        
    order_status_update(request)

    tempCart = Cart.objects.from_request(request)
    log.debug('Payment succesful, cleaning out shopping cart.',
              extra={'data': {'cart': tempCart}})

    tempCart.empty()    

    return success_base(request)


@csrf_exempt
def failure(request):
    """ Present some kind of specific failure feedback and process status
        codes. """

    order_status_update(request)
        
    return failure_base(request)

# @csrf_exempt
# def ipn(request):
#     """Ogone IPN (Instant Payment Notification)
#     Cornfirms that payment has been completed and marks invoice as paid.
#     Adapted from IPN cgi script provided at http://aspn.activestate.com/ASPN/Cookbook/Python/Recipe/456361"""
#     payment_module = config_get_group('PAYMENT_OGONE')
#     if payment_module.LIVE.value:
#         log.debug("Live IPN on %s", payment_module.KEY.value)
#         url = payment_module.POST_URL.value
#         account = payment_module.BUSINESS.value
#     else:
#         log.debug("Test IPN on %s", payment_module.KEY.value)
#         url = payment_module.POST_TEST_URL.value
#         account = payment_module.BUSINESS_TEST.value
#     PP_URL = url
# 
#     try:
#         data = request.POST
#         log.debug("Ogone IPN data: " + repr(data))
#         if not confirm_ipn_data(data, PP_URL):
#             return HttpResponse()
# 
#         if not 'payment_status' in data or not data['payment_status'] == "Completed":
#             # We want to respond to anything that isn't a payment - but we won't insert into our database.
#              log.info("Ignoring IPN data for non-completed payment.")
#              return HttpResponse()
# 
#         try:
#             invoice = data['invoice']
#         except:
#             invoice = data['item_number']
# 
#         gross = data['mc_gross']
#         txn_id = data['txn_id']
# 
#         if not OrderPayment.objects.filter(transaction_id=txn_id).count():
#             # If the payment hasn't already been processed:
#             order = Order.objects.get(pk=invoice)
# 
#             order.add_status(status='New', notes=_("Paid through Ogone."))
#             processor = get_processor_by_key('PAYMENT_OGONE')
#             payment = processor.record_payment(order=order, amount=gross, transaction_id=txn_id)
# 
#             if 'memo' in data:
#                 if order.notes:
#                     notes = order.notes + "\n"
#                 else:
#                     notes = ""
# 
#                 order.notes = notes + _('---Comment via Ogone IPN---') + u'\n' + data['memo']
#                 order.save()
#                 log.debug("Saved order notes from Ogone")
# 
#             # Run only if subscription products are installed
#             if 'product.modules.subscription' in settings.INSTALLED_APPS:
#                 for item in order.orderitem_set.filter(product__subscriptionproduct__recurring=True, completed=False):
#                     item.completed = True
#                     item.save()
# 
#             for cart in Cart.objects.filter(customer=order.contact):
#                 cart.empty()
# 
#     except:
#         log.exception(''.join(format_exception(*exc_info())))
# 
#     return HttpResponse()
# 
# def confirm_ipn_data(data, PP_URL):
#     # data is the form data that was submitted to the IPN URL.
# 
#     newparams = {}
#     for key in data.keys():
#         newparams[key] = data[key]
# 
#     newparams['cmd'] = "_notify-validate"
#     params = urlencode(newparams)
# 
#     req = urllib2.Request(PP_URL)
#     req.add_header("Content-type", "application/x-www-form-urlencoded")
#     fo = urllib2.urlopen(req, params)
# 
#     ret = fo.read()
#     if ret == "VERIFIED":
#         log.info("Ogone IPN data verification was successful.")
#     else:
#         log.info("Ogone IPN data verification failed.")
#         log.debug("HTTP code %s, response text: '%s'" % (fo.code, ret))
#         return False
# 
#     return True
