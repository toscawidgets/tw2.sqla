""" Copied from tw2.core """

import tw2.core as twc
from tw2.core.template import reset_engine_name_cache
import tw2.core.testbase.base as tw2test

twc.core.request_local = tw2test.request_local_tst
tw2test._request_local = {}

def setup():
    tw2test._request_local = {}
    tw2test._request_id = None
    reset_engine_name_cache()


def request(requestid, mw=None):
    global _request_id
    _request_id = requestid
    rl = twc.core.request_local()
    rl.clear()
    rl['middleware'] = mw
    return tw2test.request_local_tst()

