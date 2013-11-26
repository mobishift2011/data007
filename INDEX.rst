Redis索引指南
=============

Redis连接
---------
    
由于索引量太大, 单个Redis无论从容量还是运算量都无法满足我们的需要, 我们采用了客户端Sharding的方式, 把内容均匀地分不到若干台Redis上去

全部Redis的信息见``settings.py``中的``AGGRE_URIS``部分

Redis客户端调用封装在``shardredis.py``中::

    >>> from aggregator.indexes import conn
    >>> conn.get('test') # 正常redis调用函数

shardredis会自动根据调用的key, 运用consistent hashing算法, 正确调用匹配的redis

在索引计算时, 我们需要同一个类目下的索引都在同一个redis下面, 这时我们可以通过指定一个shard key来实现这一点::

    >>> conn.set('test', skey='myshardkey') # 在正常redis调用中加入skey=XXXX即可


通用字段说明
------------

如无特殊情况, 本说明中所用到的符号取值如下:

    * 任意字段均为utf-8编码
    * date = %Y-%m-%d类型的日期, e.g. 2013-11-11
    * cate1 = 一级分类id, e.g. 16
    * cate2 = 二级分类id, e.g. 50008563, 如无二级分类则取值为'all'
    * monorday = 按日统计/按月统计, e.g. day/mon



店铺索引
--------

1. shopindex_{date}_{cate1}_{cate2}_{field}_{monorday}:
    * sortedset: (shopid, value)
    * 指定分类、指定字段、指定周期下的各店铺排行
    * fields = 排序字段, e.g. sales/deals/active_index/credit_score/worth/score
        - sales: 销售额
        - deals: 成交笔数
        - active_index: 活跃指数
        - credit_score: 信用评分(1-20)
        - worth: 店铺估值(不同分类下估值一致)
        - score: 店铺评分, 用于生成默认排序的一种打分

2. shopinfo_{date}_{cate1}_{cate2}_{monorday}_{shopid}:
    * hash: (field, value)
    * 指定分类、指定周期下, 指定店铺的各类信息
    * shopid = 店铺id
    * hash的fields可取值为: sales/deals/active_index/delta_sales/delta_active_index 
        - delta_sales: 最近两个周期sales的差值(最近-次近)
        - delta_active_index: 同上以此类推

3. shopcates_{date}_{shopid}:
    * set: pack(cate1,cate2)
    * 指定店铺所含商品的分类情况
        - 解包需要用 msgpack.unpackb

4. shopbase_{date}_{shopid}:
    * hash: (field, value)
    * 指定店铺的各项统计情况
        - name: 店铺名称
        - logo: 店铺logo地址
        - credit_score: 店铺信用等级(1-20)
        - worth: 店铺估值
        - sales_mon: 店铺月销售额
        - sales_day: 店铺日销售额
        - deals_mon: 店铺月成交笔数
        - deals_day: 店铺日成交笔数
        - active_index_mon: 店铺月活跃指数
        - active_index_day: 店铺日活跃指数

5. shophotitems_{date}_{shopid}:
    * sorted set: (itemid, sales)
    * 指定店铺热门商品排行(按销量), 最多10个
    
6. shopcatescount_{date}_{shopid}:
    * hash: (cate2, counts)
    * 指定店铺品类(二级分类)所售商品数
    
7. shopbrandinfo_{date}_{shopid}_{field}_{monorday}
    * hash: (brand -> value)
    * 指定店铺、指定字段、指定周期下, 品牌占比情况
    * field = 指定店铺字段:
        - sales: 品牌销量汇总
        - deals: 品牌成交笔数汇总


商品索引
--------

1. itemindex_{date}_{cate1}_{cate2}_{field}_{monorday}
    * sorted set: (itemid, value)
    * 指定分类、指定字段、指定周期下, 各店铺的排行, 最多1000位
    * field = 店铺排序字段, 可取值为:
        - sales: 店铺销量
        - 其他排行表计算量太大, 未计算
    

2. iteminfo_{date}_{itemid}
    * hash: (field, value)
    * 指定商品的各汇总属性
    * field可取值为:
        - name: 商品名称
        - image: 商品缩略图地址
        - shopid: 商品所对应的店铺id
        - brand: 商品所属品牌
        - sales_day: 商品日销售额
        - sales_mon: 商品月销售额
        - deals_day: 商品日成交笔数
        - deals_mon: 商品月成交笔数

3. itemcatescount_{date}
    * hash: (pack(cate1,cate2), count)
    * 各个分类下商品的数目

4. itemcatessales_{date}
    * hash: (pack(cate1,cate2), sales)
    * 各个分类下商品的销量


品牌索引
--------

1. brand_{date}_{brand}_{cate1}_{cate2}
    * set: shopid
    * 指定品牌在指定分类下的店铺个数
    * brand = 品牌

2. brandinfo_{date}_{brand}_{cate1}_{cate2}
    * hash: (field, value)
    * 指定品牌在指定分类下的统计信息
    * field取值如下:
        - items: 商品个数
        - deals: (月)成交笔数
        - sales: (月)成交额
        - delta_sales: 成交额变换量(本月-上月)
        - share: 品牌销量占(分类总销量)比, 浮点数
        
3. brandcates_{date}_{brand}
    * set: pack(cate1, cate2)
    * 指定品牌的全部分类情况

4. brands_{date}
    * set: brand
    * 所有品牌

5. brandindex_{date}_{cate1}_{cate2}_{field}
    * sorted set: (brand, value)
    * 指定分类、指定字段下, 商品的排行情况, 最多1000位
    * field取值情况:
        - sales: 按销售额排序
        - 其他排行表计算量太大, 未计算

6. brandhotitems_{date}_{brand}_{cate2}
    * sorted set: (itemid, sales)
    * 指定品牌在指定品类(二级分类)下的热销商品
    
7. brandhotshops_{date}_{brand}_{cate2}
    * sorted set: (shopid, sales)
    * 指定品牌在指定品类(二级分类)下的热销店铺
    

分类索引
--------

1. categoryinfo_{date}_{cate1}_{cate2}_{monorday}
    * hash: (field, value)
    * 指定分类、指定周期的统计数据
    * field取值可为:
        - sales: 销量
        - deals: 成交笔数
        - delta_sales: 销量变化量(本期-上期)
        - items: 商品总数
        - brands: 品牌总数
        - shops: 店铺总数
        - search_index: 搜索指数(未实现)

2. categorybrands_{date}_{cate1}_{cate2}
    * set: brand
    * 指定分类下品牌集合

3. categoryindex_{date}_{cate1}_{field}_{monorday}
    * sorted set: (cate2, sales)
    * 指定分类、指定周期下, 分类汇总的销售额排名

4. categorycredits_{date}_{cate1}_{cate2}
    * hash: (credit, count)
    * 指定分类下各个信用等级的店铺的数量


时间序列字段说明
----------------

世界序列数据量太大, 无法保存在redis里, 只能保存在cassandra里面.
Cassandra的Schema结构见文件schema.cql

Cassandra读取的连接池实现在``cqlutils.py``,  一般调用如下::

    >>> from models import db
    >>> query = 'select * from ataobao2.item_by_date where id=:itemid'
    >>> params = dict(itemid=1234567)
    >>> r = db.execute(query, params, result=True)
    >>> print r.columns
    >>> print r.results

1. 商品时间序列:
    * 表名: item_by_date
    * 字段:
        - price, 价格
        - num_sold30, 月成交笔数
    * 计算:
        - price = price
        - delas = num_sold30//30
        - sales = price*deals

2. 店铺时间序列:
    * 表名: shop_by_date
    * 字段:
        - rank: 行业排名, json格式的dict, (cid, rank)
        - worth: 店铺估值
        - sales: 成交额

3. 品牌时间序列:
    * 表名: brand_by_date 
    * 字段:
        - sales: 成交额
        - share: 市场占比
        - shops: 店铺数量
