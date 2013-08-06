# -*- coding: utf-8 -*-


'''

文档：http://open.taobao.com/doc/detail.htm?spm=0.0.0.0.sPgMuf&id=141


测试：
1.http://container.open.taobao.com/container?appkey=21524636
2.授权

http://www.51proxyip.com/?top_appkey=21431991&top_parameters=ZXhwaXJlc19pbj04NjQwMCZpZnJhbWU9MSZyMV9leHBpcmVzX2luPTg2NDAwJnIyX2V4cGlyZXNfaW49ODY0MDAmcmVfZXhwaXJlc19pbj04NjQwMCZyZWZyZXNoX3Rva2VuPTYxMDBiMzBkYjU0Y2FkZjYzMDRmNjllYjVmMjRiYmNmN2I2NGI3MTM5NjRiZjlkNTY3NzkzMzAmdHM9MTM2OTEyMTIwMDIyNCZ2aXNpdG9yX2lkPTU2Nzc5MzMwJnZpc2l0b3Jfbmljaz1jaGVuZnV6aGkxOTk5JncxX2V4cGlyZXNfaW49ODY0MDAmdzJfZXhwaXJlc19pbj04NjQwMA%3D%3D&top_session=6101430dd32a13641c86652521524ffad253e8123b0678456779330&agreement=true&agreementsign=21431991-22818685-56779330-18062B4A0AEBBB60B7F4C01476854131&top_sign=3mnFAJjjKU%2BygHBE%2BG3lMw%3D%3D
'''
import top.api

top.setDefaultAppInfo("21524636", "9f53602fff17846902ff5bfdf3010dda")


req=top.api.TradeFullinfoGetRequest()

req.fields="alipay_no,commission_fee,received_payment,buyer_alipay_no, num_iid"
req.tid=355458240202234
resp= req.getResponse("61017167ff05b2ffa34f396a14771d3187d73cb7a93828656779330")
print(resp)

#------------------------------------------------------------------------------ 
req=top.api.ItemGetRequest()
req.num_iid = 20739183144
req.fields = "detail_url, props_name, is_lightning_consignment"
resp= req.getResponse("61017167ff05b2ffa34f396a14771d3187d73cb7a93828656779330")
print(resp)







