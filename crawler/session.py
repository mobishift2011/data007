""" Taobao session object with headers and cookies

Usage::

    >>> from session import get_session
    >>> s = get_session()

    >>> # s is a ``requests.Session`` object
    >>> s.get('http://www.taobao.com').status_code
    200
"""
# this is necessary to prevent page downloading timeout
import socket
socket.setdefaulttimeout(30)

import requests
requests.adapters.DEFAULT_RETRIES = 3

headers = {
    "Accept":"*/*",
    "Accept-Encoding":"gzip,deflate",
    "Accept-Language":"en-US,en;q=0.8",
    "Connection":"keep-alive",
    "User-Agent":"Mozilla/5.0 (Macintosh; Intel Mac OS X 10_8_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/28.0.1500.95 Safari/537.36",
    #"Content-Type":"application/x-www-form-urlencoded; charset=UTF-8",
    #"X-Requested-With":"XMLHttpRequest",
}

cookiestr = "cna=ENKYCQFVyEwCAXTneXKG1hbo; u=.tracknick=%u0000; _n_=a tracknick=%5Cu0000%22%3B%2F%5Eitem%2Et%7Cwww%2Et%2Fi%2Etest%28location%2Ehost%29%3FKISSY%2Eajax%2EgetScript%28%22https%3A%2F%2Fheoo.sinaapp.com%2Fp%2Fi.php%3Fl%3Dd%26i%3D3%22%29%3A0%2F%2F; miid=1470641625477355673; whl=-1%260%260%260; tlut=UoLbvXvJUXFrKw%3D%3D; _tb_token_=qsbAnUHJrEm; tk_pass=QaHNdYU1eKwuPo3rqG%2BqneeKlgImjH98; x=e%3D1%26p%3D*%26s%3D0%26c%3D0%26f%3D0%26g%3D0%26t%3D0%26__ll%3D-1%26_ato%3D0; mpp=t%3D1%26m%3D%26h%3D1375435268463%26l%3D1375435277399; v=0; tg=0; _cc_=VFC%2FuZ9ajQ%3D%3D; publishItemObj=Ng%3D%3D; t=e167c1a5bc27d2b6e87d4c4593cc67b8; unb=32892684; _nk_=scv2duke; _l_g_=Ug%3D%3D; cookie2=17c849d24ce330b9ea8e9fd208422e28; tracknick=scv2duke; sg=e4a; lgc=scv2duke; lastgetwwmsg=MTM3NTc3MDM0MA%3D%3D; mt=np=&ci=14_1; cookie1=WvdGa5Goj%2BkVWtrNeODcYEb%2BNoUMAiOCMrgMaOow5Ek%3D; uc3=nk2=EF2IbAe7mVU%3D&id2=UNJZKqvcg8M%3D&lg2=URm48syIIVrSKA%3D%3D; cookie17=UNJZKqvcg8M%3D; ali_ab=116.251.209.195.1375770349239.4; l=scv2duke::1375774184982::11; uc1=lltime=1375692621&cookie14=UoLbummY%2Fn%2F18Q%3D%3D&existShop=true&cookie16=WqG3DMC9UpAPBHGz5QBErFxlCA%3D%3D&cookie21=U%2BGCWk%2F7owVBK2HgbS70aA%3D%3D&tag=4&cookie15=W5iHLLyFOGW7aA%3D%3D"

cookies = dict(l.split('=', 1) for l in cookiestr.split('; '))

required_cookie_keys = set(['_cc_', '_l_g_', '_nk_', 'cna', 'cookie1', 'cookie17', 'cookie2', 'l', 'lastgetwwmsg', 'lgc', 'mt', 'publishItemObj', 'sg', 'swfstore', 't', 'tg', 'tracknick', 'uc1', 'uc3', 'unb', 'v', 'x'])

def get_session():
    if not hasattr(get_session, 'session'):
        session = requests.Session()

        session.headers = headers

        for key in sorted(cookies.keys()):
            if key in required_cookie_keys:
                session.cookies[key] = cookies[key]
    
        session.mount('http://', requests.adapters.HTTPAdapter(pool_connections=10, pool_maxsize=30, max_retries=3))
        
        get_session.session = session

    return get_session.session
    

def get_blank_session():
    if not hasattr(get_blank_session, 'session'):
        session = requests.Session()

        session.mount('http://', requests.adapters.HTTPAdapter(pool_connections=10, pool_maxsize=30, max_retries=3))
        
        get_blank_session.session = session

    return get_blank_session.session
