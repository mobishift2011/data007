from crawler.aggregator import aggregate_items, aggregate_shops
from aggres import ShopIndex, AggInfo
from queues import aa1, aa2
from datetime import datetime, timedelta
import time

def clear(date):
    print 'clearing'
    aa1.clear()
    aa2.clear() 
    AggInfo(date).clear()
    ShopIndex(date).clear()
    print 'cleared'

def doagg(type):
    print("agg {}".format(type))
    step = 2**64/100000 if type == "item" else 2**64/10000
    q = aa1 if type == 'item' else aa2
    count = 0
    for start in range(-2**63, 2**63, step):
        end = start + step
        q.put((start, end))
        count += 1
        if count % 1000 == 0:
            print("queued {} jobs".format(count))

def waitforfinish(date, type):
    ai = AggInfo(date)
    while ai.task_left(type) > 0:
        print('{} {}slice left'.format(ai.task_left(type), type))
        time.sleep(3)

def main():
    date = (datetime.utcnow() + timedelta(hours=-16)).strftime("%Y-%m-%d")
    clear(date)
    doagg('item')
    waitforfinish(date, 'item')
    doagg('shop')
    waitforfinish(date, 'shop')

if __name__ == '__main__':
    main()
