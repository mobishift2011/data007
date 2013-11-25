#coding:utf-8



from debouncing import get_update_bin, can_update, pack_bin, unpack_bin, replace_old

    
import random
import unittest

class test_pack_bin(unittest.TestCase):
    def setUp(self):
        self.sbin = pack_bin(1234567890, 100, 0)
    def test_model(self):
        rets = unpack_bin(self.sbin)
        self.assertListEqual(list(rets), [1234567890, 100, 0], msg='pack, unpack, err')
        

class test_offset(unittest.TestCase):
    def setUp(self):
        self.sbin = pack_bin(1234567890, 100, 0)
    def test_model(self):
        self.assertEqual(self.unchange_days(1), 1)
        self.assertEqual(self.unchange_days(2), 2)
        self.assertEqual(self.unchange_days(3), 4)
        self.assertEqual(self.unchange_days(4), 8)
        self.assertEqual(self.unchange_days(5), 15)
        self.assertEqual(self.unchange_days(6), 15)
    def unchange_days(self, num):
        bin = self.sbin
        for i in range(0, num):
            info = {'num_instock':100}
            bin = get_update_bin(bin, info)
        return unpack_bin(bin)[2]
        
    def tearDown(self):
        print "tearDown"

import random
from functools import partial
import time
now = int(time.time())
def later_time(num):
    return now + 86400*num

class test_debouncing(unittest.TestCase):
    def setUp(self):
        self.instock = 100
        self.sbin = pack_bin(int(now), self.instock, 0)
        
    def test_model(self):
        for i in [1, 3, 7, 15, 20, 30, 60]:
            self.setUp()
            print "====================================%s" % i
            self.unchange_days(i)
            print "====================================%s days unchange instock." % i

    def test_model2(self):
        print "~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~"
        for i, n in enumerate([(30, 3), (30, 5), (30, 7)]): # (days, ch_day)
            self.setUp()
            print "====================================%s, (%s, %s)" % (i, n[0], n[1])
            self.unchange_days_chday(*n)
            print "====================================%s, (%s, %s) days unchange instock." % (i, n[0], n[1])


    def unchange_days(self, num):
        for i in range(1, num+1):
            time.time = partial(later_time, i)
            if can_update(self.sbin):
                info = {'num_instock':self.instock}
                self.sbin = get_update_bin(self.sbin, info)
                print "{}  to__crawl".format(i)
            else:
                print "{}  deboucing".format(i)
                

    def unchange_days_chday(self, num, chd):
        for i in range(1, num+1):
            if chd == i:
                self.instock += 1            
            time.time = partial(later_time, i)
            if can_update(self.sbin):
                info = {'num_instock':self.instock}
                self.sbin = get_update_bin(self.sbin, info)
                print "{}  to__crawl".format(i)
            else:
                print "{}  deboucing".format(i)


    
if __name__ == "__main__":
    unittest.main()
    
    
    
    
    
    
    
    
    
    