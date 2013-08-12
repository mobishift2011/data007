from crawler.session import get_session
import threading
from collections import Counter

def test_session():
    """ test taobao is ok with this session
       
    we use 20 threads fetching 500 pages in total,
    without headers and cookie, taobao will return error page
    """

    num_threads = 5
    num_fetchs_per_thread = 50
    url = 'http://item.taobao.com/item.htm?id=26215464026'
    response_sizes = Counter()
    session = get_session()

    def work():
        for _ in range(num_fetchs_per_thread):
            try:
                response_sizes[ len(session.get(url).content) ] += 1
            except:
                pass

    def joinall(tasks):
        for task in tasks:
            task.join()
    
    def startall(tasks):
        for task in tasks:
            task.start()
        return tasks
    
    joinall(startall([ threading.Thread(target=work) for _ in range(num_threads) ]))

    for size, count in response_sizes.most_common():
        assert size > 10000, "taobao refuse session requests"
