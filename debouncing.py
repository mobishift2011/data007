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
        31(ts), 21(num_sold30), 4(offset)
    '''
    if info.has_key('latest_buy_time'):
        latest_time = int(time.mktime(time.strptime(info['latest_buy_time'], '%Y-%m-%d %H:%M:%S'))) / 3600
    else:
        latest_time = 0
        
    ret_bin = replace_old(ret_bin)
    
    if ret_bin:
        cts, uts, offset = unpack_bin(int(ret_bin))
        print cts, uts, offset
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
            
        print "offset:%s" % offset
        return pack_bin(cts, uts, offset)
    else:
        return pack_bin(int(time.time()), latest_time, 0)
    
    
def can_update(store_bin):
    if store_bin is None:
        return True
    else:
        store_bin = replace_old(store_bin)
        cts, uts, offset = unpack_bin(store_bin)
        if offset == 0:
            offset = 80000
        else:
            offset *= 86400
        if cts + offset < int(time.time()):
            return True
    return False


def pack_bin(cts, uts, offset):
    '''
    latest_buy_time
                                                             
        31(ts), 19(update_ts), 4(offset)
    '''
    return (cts << 23) + (uts << 4) + offset
  
def unpack_bin(sbin):
    sbin = int(sbin)
    offset = sbin & 0xf
    uts = (sbin >> 4) & 0x7ffff
    cts = sbin >> 23
    return cts, uts, offset


import xdrlib


def main():
    p = xdrlib.Packer()
    p.pack_int(1111)
    p.pack_int(1111)
    p.pack_int(1111)
    
    unp = xdrlib.Unpacker(p.get_buf())
    print unp.get_buffer()


          
if __name__ == "__main__":
    main()                  
                        
                        
                        
                        
                        
                        