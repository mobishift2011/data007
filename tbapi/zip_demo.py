#coding:utf-8


import zipfile
import json
import pymongo


conn = pymongo.Connection("oneandone.favbuy.org", port=37017)
conn.admin.authenticate("root", "chenfuzhi")


zfile = zipfile.ZipFile('download.zip','r')
for filename in zfile.namelist():
    if filename == "16":
        f = zfile.read(filename)
        data = json.loads(f)
        #print json.dumps(data, indent=4)
        for cate in data["childCategoryList"]:
            print cate.keys()
            conn.taobao.category.save(cate)
    print filename
    


