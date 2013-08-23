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


mongo_conn = pymongo.Connection('192.168.2.201', 27017)

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

    def run(self):
        global mongo_conn
        global AWS_ACCESS_KEY, AWS_SECRET_KEY
        
        while 1:
            rows = mongo_conn.taobao.e_c2__schd.find({"enable":True})
            rows = list(rows)
            print rows
            
            for row in rows:
                log.msg("begin schd %s" % row)
                
                now = int(time.time())
                schd_time = int(row['schd_time'])
                
                latest_schd = time.mktime(row['latest_schd'].timetuple())
                
                print "###############", now, schd_time, latest_schd
                
                if (now - latest_schd) > schd_time:
                    conn = boto.ec2.connect_to_region(row['ec2_region'], aws_access_key_id=AWS_ACCESS_KEY, aws_secret_access_key=AWS_SECRET_KEY)
                    
                    rows = mongo_conn.taobao.e_c2__instance.find({"ec2_region" : row['ec2_region']})
                    for rrr in rows:
                        mongo_conn.taobao.e_c2__instance.remove({"_id":rrr["_id"]})
                            
                    running_ids = []
                    terminate_ids = []
                    instance_ids = []
                        
                    for res in conn.get_all_instances(filters={'image-id':row['image_id']}):
                        log.msg("get res:{}".format(res))
                        for i in res.instances:
                            log.msg("get instances:{}".format(i.id))
                            instance_ids.append(i.id)
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
                            
                            if (row['live_time'] > -1):
                                launch_time = int(time.mktime(time.strptime(i.launch_time, "%Y-%M-%dT%H:%I:%S.000Z")))
                                now_time = int(time.time())
                                log.msg("check live_time,now:{}, launch_time:{}".format(now_time, launch_time))
                                
                                if (int(time.time()) - i.launch_time) > row['live_time']:
                                    terminate_ids.append(i.id)
                                    
                            if i.state in ["running", "pending"]:
                                running_ids.append(i.id)
                                
                    log.msg('finish##,get instances:'.format(len(instance_ids)))
                    
                    print int(row['instance_num']), len(instance_ids)
                    run_instances = int(row['instance_num']) - len(running_ids)
                    if run_instances > 0:
                        print "run_instances", run_instances
                        ret = conn.run_instances(
                            row['image_id'],
                            min_count = run_instances,
                            max_count = run_instances,
                            #key_name='favbuykey', 
                            #security_groups=['sg-5d0b7d5c'], 
                            security_group_ids = ['sg-5d0b7d5c'], 
                            #instance_profile_name = "aa",
                            instance_type = row['instance_type'], 
                            user_data = row['script_code']
                        )
                        log.msg("run_instances:{}".format(ret))
                    else:
                        print running_ids[int(row['instance_num']):]
                        term_ids = running_ids[int(row['instance_num']):]
                        if len(term_ids) > 0:
                            ret = conn.terminate_instances(instance_ids=term_ids)
                            log.msg("terminate_instances:{}".format(ret))
                        
                        

                    if len(terminate_ids) > 0:
                        ret = conn.terminate_instances(instance_ids=terminate_ids)
                        log.msg("terminate_instances:{}".format(ret))
            
            log.msg("sleep is 3 second.")
            time.sleep(3)
        
        
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
    reactor.callWhenRunning(start)
    application = service.Application('ec2_schd')
    
    