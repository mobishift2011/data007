from crawler.tbitem import get_item

def test_counters():
    # do not test this
    return
    data = get_counters(26215464026, 1097864591)
    assert 'num_views' in data and 'num_reviews' in data
    data = get_counters(19667991376, 519221282)
    assert 'num_views' in data and 'num_reviews' in data

def test_item():
    # do not test this
    return 
    for id in [15779110791, 19667991376, 21825059650, 19536353824, 19536097533, 19521682005, 19536509268]:
        data = get_item(id)
        assert data['id'] == id
        assert isinstance(data['price'], float)
