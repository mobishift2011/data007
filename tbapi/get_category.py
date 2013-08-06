#coding:utf-8


import top.api
top.setDefaultAppInfo("21524636", "9f53602fff17846902ff5bfdf3010dda")


req=top.api.TopatsItemcatsGetRequest()

req.cids="16"
req.output_format="json"
req.type=1
try:
#     resp= req.getResponse("6102520efc5536b01243abd766b61a722318e853f9dadac56779330")
#     print(resp)
    req = top.api.TopatsResultGetRequest()
    req.task_id = 173104758
    resp= req.getResponse("6102520efc5536b01243abd766b61a722318e853f9dadac56779330")
    print(resp)
    
except Exception, e:
    print(e)

