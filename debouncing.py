#coding:utf-8


import time


def replace_old(ret_bin):
    try:
        if len(bin(int(ret_bin))) != 58:
            ret_bin = None
    except:
        ret_bin = None
    return ret_bin
        
def get_update_bin(ret_bin, info):
    '''
    latest_buy_time
             56
        31(timestamp), 21(num_sold30), 4(offset)
    '''
    if info.has_key('num_instock'):
        latest_time = int(info['num_instock'])
    else:
        latest_time = 0
    ret_bin = replace_old(ret_bin)
    
    if ret_bin:
        cts, uts, offset = unpack_bin(int(ret_bin))
        if latest_time == uts:
            if offset == 0:
                offset = 1
            elif offset == 8:
                offset = 15
            elif offset == 15:
                offset = 15
            else:
                offset *= 2
        else:
            offset = 0
        #print "offset:%s" % offset
        return pack_bin(int(time.time()), latest_time, offset)
    else:
        offset = 0
        # this is a new item
        # initialize offset according to solds
        # if the item isn't sold that good
        # we biased and offset it larger than 0 initially
        if 'num_sold30' in info:
            ns = int(info.get('num_sold30', 0))
            if ns == 0:
                offset = 4
            elif ns < 30:
                offset = 1
        return pack_bin(int(time.time()), latest_time, offset)
    
    
def can_update(store_bin):
    if store_bin is None:
        return True
    else:
        store_bin = replace_old(store_bin)
        cts, uts, offset = unpack_bin(store_bin)
        if offset == 0:
            offset = 80000
        else:
            offset = (offset + 1)*86400
        if cts + offset < int(time.time()):
            return True
    return False

def pack_bin(cts, uts, offset):
    '''
    latest_buy_time
                     31+21+4=56                                        
        31(ts), 21(update_ts), 4(offset)
    '''
    return (cts << 25) + (uts << 4) + offset

def unpack_bin(sbin):
    try:
        sbin = int(sbin)
        offset = sbin & 0xf
        uts = (sbin >> 4) & 0x1fffff
        cts = sbin >> 25
        return cts, uts, offset
    except:
        return 0, 0, 0


import random
import unittest

class TestFunctions(unittest.TestCase):

    def setUp(self):
        print "setUp"
        self.seq = range(10)
    
    def test_shuffle(self):
        random.shuffle(self.seq)
        self.seq.sort()

    def test_choice(self):
        element = random.choice(self.seq)
        self.assertTrue(element in self.seq)

    def test_error(self):
        element = random.choice(self.seq)
        self.assertTrue(element not in self.seq)

    def tearDown(self):
        print "tearDown"

if __name__ == "__main__":
    unittest.main()











