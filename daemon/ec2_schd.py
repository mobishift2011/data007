#!/usr/bin/env python
# -*- coding: utf-8 -*-


from twisted.python import log
from twisted.internet import reactor, defer

from twisted.application import internet, service
import os
import time
import traceback
import threading
import time
import boto.ec2
import pymongo
import sys
import datetime


mongo_conn = pymongo.Connection('localhost', 27017)

AWS_ACCESS_KEY = 'AKIAIQC5UD4UWIJTBB2A'
AWS_SECRET_KEY = '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'

#conn = boto.ec2.connect_to_region(REGION, aws_access_key_id=AWS_ACCESS_KEY, aws_secret_access_key=AWS_SECRET_KEY)


class EC2Monitor(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
    
    def start(self):
        while 1:
            try:
                self.run()
            except Exception, e:
                traceback.print_exc()
                time.sleep(3)

    def check_live_time(self, live_time, instance):
        import dateutil.parser
        print type(instance.launch_time), instance.launch_time
        if (live_time > -1):
            dt = dateutil.parser.parse(instance.launch_time)
            launch_time = int(time.mktime(dt.timetuple()))
            now_time = int(time.time())
            log.msg("check live_time,now:{}, launch_time:{}".format(now_time, launch_time))
            if (now_time - launch_time) > int(live_time):
                log.msg('%s:running time is longer then live_time.' % instance.id)
                return True
        return False
    
                
    def run(self):
        global mongo_conn
        global AWS_ACCESS_KEY, AWS_SECRET_KEY
        
        while 1:
            rows = mongo_conn.taobao.e_c2__schd.find({"enable":True})
            rows = list(rows)
            print rows
            
            for row in rows:
                log.msg("begin schd %s" % row)
                
                tag_name = "%s-%s" % (str(row['_id']), row['name'])
                
                now = int(time.time())
                schd_time = int(row['schd_time'])
                
                latest_schd = time.mktime(row['latest_schd'].timetuple())
                
                print "###############", now, schd_time, latest_schd
                
                if (now - latest_schd) > schd_time:
                    conn = boto.ec2.connect_to_region(row['ec2_region'], aws_access_key_id=AWS_ACCESS_KEY, aws_secret_access_key=AWS_SECRET_KEY)
                    
                    rows = mongo_conn.taobao.e_c2__instance.find({"ec2_region" : row['ec2_region']})
                    for rrr in rows:
                        mongo_conn.taobao.e_c2__instance.remove({"_id":rrr["_id"]})
#------------------------------------------------------------------------------ 
                    req_list = []
                    instance_list = []
                    for res in conn.get_all_instances(filters={'tag:Name': tag_name, 'image-id':row['image_id']}):
                        log.msg("get res:{}".format(res))
                        for i in res.instances:
                            log.msg("get instances:{}".format(i.id))
                            dict_i = {
                                      'state':i.state,
                                      'ip_address':i.ip_address,
                                      'instance_type': i.instance_type,
                                      'ec2_region':row['ec2_region'],
                                      'image_id' : i.image_id,
                                      'launch_time': i.launch_time,
                                      }
                            mongo_conn.taobao.e_c2__instance.update({'instance_id': i.id}, 
                                                                   {'$set':dict_i},
                                                                   upsert=True)
                            instance_list.append(i)
                    
                    for req in conn.get_all_spot_instance_requests(filters={'tag:Name': tag_name, 'state':['open', 'active', 'cancelled', 'failed']}):
                        print req.id, req.state
                        req_list.append(req)
                    
                    print "!!!!!!!!!!!!aaaaaaaaaaaaa", [x.id for x in req_list], len(req_list)
                    print len(req_list)
                    
                    count = len(req_list)
                    page_size = 100
                    page_num = (count / page_size) + (1 if (count % page_size) else 0)
                    for page in range(page_num):
                        print page_size, page_num, count, page
                        for res in conn.get_all_instances(filters={'spot-instance-request-id':[x.id for x in req_list[page*page_size:page_size]],
                                                                    'image-id':row['image_id']}):
                            for i in res.instances:
                                if i.id not in [x.id for x in instance_list]:
                                    instance_list.append(i)
                                    i.add_tag("Name", tag_name)
                                    print "add_tag", i.id
                        
                    
                    log.msg('finish##,get instance_list:'.format(len(instance_list)))
                    
                    print "running-set:", int(row['instance_num']), "instance_list:", len(instance_list)
                    run_instances = int(row['instance_num']) - len([x.id for x in instance_list if x.state in ["running", "pending"]]) - len([x.id for x in req_list if x.state == "open"])
                    if run_instances > 0:
                        print "run_instances,need", run_instances
                        if run_instances > 3:
                            run_instances = 3
                        
                        print "run_instances,real", run_instances
                        rets = conn.request_spot_instances(
                            row['price'],
                            row['image_id'],
                            count=run_instances,
                            #key_name='favbuykey', 
                            #security_groups=['sg-5d0b7d5c'], 
                            #security_group_ids = map(str, row['security_group_ids']), 
                            #instance_profile_name = row['name'],
                            #instance_profile_name = "aa",
                            #security_groups = ['general'],
                            security_group_ids = map(str, row['security_group_ids']), 
                            instance_type = row['instance_type'], 
                            user_data = row['script_code']
                        )
                        log.msg("run_instances:{}".format(rets))
                        
                        try:
                            for ret in rets:
                                ret.add_tag('Name', tag_name)
                        except:
                            pass
                        
                        
                        while 1:
                            reqs = conn.get_all_spot_instance_requests(filters={'tag:Name': tag_name,
                                                                                'spot-instance-request-id':[x.id for x in rets]
                                                                                })
                            if len(rets) == len(reqs):
                                break
                            else:
                                log.msg('wait to request finish!!')
                                time.sleep(1)
                            
                    else:
                        #instance is more then setting.
                        running_ids = [x.id for x in instance_list if x.state in ["running", "pending"]]
                        print running_ids[int(row['instance_num']):]
                        term_ids = running_ids[int(row['instance_num']):]
                        if len(term_ids) > 0:
                            ret = conn.terminate_instances(instance_ids=term_ids)
                            log.msg("terminate_instances:{}".format(ret))
                            
                    active_list = [x for x in instance_list if x.state in ['running']]
                    term_ids = [x.id for x in active_list if self.check_live_time(row['live_time'], x)]
                    log.msg("terminate_instances:{}".format(term_ids)) 
                    if len(term_ids) > 0:
                        conn.terminate_instances(instance_ids=term_ids)
            
            log.msg("sleep is 10 second.")
            time.sleep(10)
        
        
def start():
    t = EC2Monitor()
    t.start()


def main():
    for r in conn.get_all_instances():
        for i in r.instances:
            print "##############################"
            print i.tags
            if not i.tags.has_key('Name'):
                i.add_tag("Name","taobao_%s" % i)
    #ret = request_instances()
    print "finish!!!"
    #conn.create_tags(['r-75625877'], {'Name':'aaaaaaaaa'})
    
def request_instances():
    ret = conn.run_instances(
        "ami-a579efa4", 
        min_count = 1,
        max_count = 1,
        #key_name='favbuykey', 
        #security_groups=['sg-5d0b7d5c'], 
        security_group_ids = ['sg-5d0b7d5c'], 
        #instance_profile_name = "aa",
        instance_type="t1.micro", 
        #user_data=get_init_script(*(NUMS.get(itype, (10, 10))),burst=burst)
    )
    return ret


if __name__ == "__main__":
    log.startLogging(sys.stdout)
    reactor.callWhenRunning(start)
    reactor.run()
    
if __name__ == "__builtin__":
    from twisted.python.log import ILogObserver, FileLogObserver
    from twisted.python.logfile import DailyLogFile, LogFile
    reactor.callWhenRunning(start)
    application = service.Application('ec2_schd')
    logfile = LogFile("ec2_schd.log", "/var/log/", rotateLength=100000000000)
    application.setComponent(ILogObserver, FileLogObserver(logfile).emit)
    