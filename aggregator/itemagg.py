#!/usr/bin/env python
# -*- coding: utf-8 -*-
from aggregator.models import getdb
from aggregator.indexes import ShopIndex, ItemIndex, BrandIndex, CategoryIndex
from aggregator.processes import Process
from aggregator.blacklist import in_blacklist

from settings import ENV
from datetime import datetime, timedelta
from collections import defaultdict

from crawler.cates import cates

import re
import time
import random
import struct
import calendar
import traceback

def clean_brand(brand):
    brand = brand.strip()

    aliases = {
        u'Nalone': u'Nalone/诺兰',
        u'Music travels': u'MUSIC TRAVELS/游乐者',
        u'詹姆斯战靴': u'詹姆斯篮球鞋',
        u'周林频谱': u'Zhoulin/周林频谱',
        u'官方NK': u'Nike/耐克',
        u'阿迪达斯': u'Adidas/阿迪达斯',
        u'尚牌': u'Elasun/尚牌',
        u'JUMBOUGG': u'UGG',
        u'骆驼牌': u'Camel/骆驼',
        u'放纵地带': u'Funzone∕放纵地带',
        u'红双喜': u'DHS/红双喜',
        u'优朗': u'U－BRIGHT/优朗',
        u'Nike Air Jordan': u'乔丹',
        u'三叶草': u'Adidas/阿迪达斯',
        u'Aveeno': u'Aveeno/艾维诺',
        u'ROYAL CANIN/皇家': u'ROYAL CANIN/皇家宠物食品',
        u'阿迪': u'Adidas/阿迪达斯',
        u'CaliforniaBaby': u'CaliforniaBaby/加州宝宝',
        u'红双喜(乒乓球)': u'DHS/红双喜',
        u'AD': u'Adidas/阿迪达斯',
        u'Adidas/三叶草': u'Adidas/阿迪达斯',
        u'红蜻蜓': u'RED DRAGONFLY/红蜻蜓',
        u'NK': u'Nike/耐克',
        u'冈本OK': u'冈本',
        u'神火': u'SureFire/神火',
        u'澳洲冠能': u'冠能',
        u'特步': u'XTEP/特步',
        u'AJ4': u'AJ',
        u'美国冠能': u'冠能',
        u'ＪＯＲＤＡＮ': u'乔丹',
        u'Nutrilon/诺优能(牛栏)': u'Nutrilon/诺优能',
        u'诺瑞': u'Nory/诺瑞',
        u'杜蕾斯': u'Durex/杜蕾斯',
        u'香港雷霆': u'雷霆',
        u'2h2d': u'丸荣2h2d',
        u'李宁': u'Lining/李宁',
        u'美国svakom': u'svakom',
        u'上海凤凰': u'Phoenix/凤凰',
        u'Bridestowe': u'Bridestowe Lavender',
        u'Friso/美素佳儿': u'FRISO/美素',
        u'第6感': u'SIXSEX/第6感',
        u'columbia': u'Columbia/哥伦比亚',
        u'日本黑豹': u'黑豹',
        u'LELO': u'瑞典LELO',
        u'詹姆斯11代篮球鞋': u'詹姆斯篮球鞋',
        u'凤凰': u'Phoenix/凤凰',
        u'乐高': u'LEGO/乐高',
        u'NOW': u'NOW! Grain Free',
        u'喜安智': u'babikins/喜安智',
        u'森森': u'SUNSUN/森森',
        u'Gucci': u'Gucci/古奇',
        u'哥弟': u'Girdear/哥弟',
        u'childlife': u'Childlife/童年时光',
        u'迪士尼': u'Disney/迪士尼',
        u'361°': u'361°/361度',
        u'alpha': u'alpha industries',
        u'黛安芬': u'Triumph/黛安芬',
        u'骆驼': u'Camel/骆驼',
        u'新光饰品': u'新光',
        u'manmiao': u'MANMIAO漫渺',
        u'闽江水族': u'闽江',
        u'Abckids': u'ABC',
        u'Burberry': u'Burberry/巴宝莉',
        u'多威': u'do－win/多威',
        u'AIR JORDAN': u'乔丹',
        u'花王': u'花王/妙而舒',
        u'喜宝': u'Hipp/喜宝',
        u'狼爪': u'Jack wolfskin/狼爪',
        u'耐克': u'Nike/耐克',
        u'上海故事': u'Story Of Shanghai/上海故事',
        u'大嘴猴': u'Paul Frank/大嘴猴',
        u'布朗博士': u'Dr Brown’s Natural Flow/布朗博士好流畅',
        u'澳洲雪地靴': u'雪地靴',
        u'万代': u'Bandai/万代',
        u'杜兰特6代': u'杜兰特',
        u'加拿大Swan': u'swan',
        u'英氏': u'YEEHOO/英氏',
        u'韩国zini': u'ZINI',
        u'海洋之星': u'Fish4Dogs/海洋之星',
        u'安奈儿': u'Annil/安奈儿',
        u'喵星人': u'喵星人MeWare',
        u'she’s': u'She’s silk/西丝娘娘',
        u'complus': u'complus/卡玛仕',
        u'papago': u'papago/趴趴狗',
        u'HUNYDON': u'HUNYDON/现代',
        u'宝马': u'BMW/宝马',
        u'carcony': u'carcony/卡康尼',
        u'酷斯特': u'kust/酷斯特',
        u'圣玛帝诺': u'St.mary tino/圣玛帝诺',
        u'bresh': u'bresh/柏瑞仕',
        u'icalife': u'icalife/愉家',
        u'BHM 贝汉美': u'BHM/贝汉美',
        u'MIZ': u'MIZ/米子',
        u'racekish': u'racekish/芮诗凯诗',
        u'kiss dear': u'kiss dear/卡丝迪尔',
        u'贝汉美': u'BHM/贝汉美',
        u'诺奇': u'N&Q/诺奇',
        u'七匹狼': u'septwolves/七匹狼',
        u'abercrombie fitch': u'abercrombie fitch/阿贝尔克隆比&费奇',
        u'moncler': u'moncler/蒙口',
        u'金利来/goldlion': u'goldlion/金利来',
        u'骆驼': u'camel/骆驼',
        u'雅戈尔': u'youngor/雅戈尔',
        u'思诺依维': u'snowimage/思诺依维',
        u'mosonny tee': u'mosonny/墨森尼',
        u'deepocean': u'deepocean/深海',
        u'艾莱依': u'eral/艾莱依',
        u'香港七匹狼': u'septwolves/七匹狼',
        u'alouserdu': u'alouserdu/奥陆而盾',
        u'优鲨': u'u&shark/优鲨',
        u'kasablanka': u'kasablanka/卡萨布兰卡',
        u'蒙口': u'moncler/蒙口',
        u'鄂尔多斯': u'erdos/鄂尔多斯',
        u'金利来': u'goldlion/金利来',
        u'九牧王': u'JOEONE/九牧王',
        u'雅琼': u'YQ/雅琼',
        u'YOOQ 佑企': u'YOOQ/佑企',
        u'沃购': u'wocle/沃购',
        u'YOOQ 佑企': u'YOOQ/佑企',
        u'威图vertu': u'vertu/威图',
        u'三普': u'sunup/三普',
        u'地球人TF': u'Terrans force/地球人',
        u'mobiado': u'mobiado/膜拜',
        u'Terransforce': u'Terrans force/地球人',
        u'terrans force': u'Terrans force/地球人',
        u'乐目': u'LM/乐目',
        u'ccpo': u'ccpo/西铂',
        u'松下Panasonic': u'Panasonic/松下',
        u'松下': u'Panasonic/松下',
        u'sonim': u'sonim/萨基姆',
        u'地球人': u'Terrans force/地球人',
        u'镭波': u'镭波/rabook',
        u'欧博信': u'opson/欧博信',
        u'地球人TF P175EM': u'Terrans force/地球人',
        u'优派': u'viewsonic/优派',
        u'镭波电脑': u'镭波/rabook',
        u'水尚': u'SISEAN/水尚',
        u'iope': u'iope/亦博',
        u'skin food': u'skin food/思亲肤',
        u'韩熙贞': u'HEXZE/韩熙贞',
        u'Litfly': u'Litfly/丽塔芙',
        u'Marc Jacobs': u'Marc Jacobs/马克雅克布',
        u'Laura Mercier': u'Laura Mercier/罗拉玛斯亚',
        u'Lanvin': u'Lanvin/浪凡',
        u'it‘s skin': u'it‘s skin/伊思',
        u'Fresh': u'Fresh/馥蕾诗',
        u'雪花秀': u'sulwhasoo/雪花秀',
        u'it‘s skin': u'it‘s skin/伊思',
        u'Fancl/无添加': u'Fancl',
        u'DHC': u'DHC/蝶翠诗',
        u'圣荷': u'st.hers/圣荷',
        u'Skin food': u'skin food/思亲肤',
        u'Nuxe': u'Nuxe/欧树',
        u'vivo': u'vivo/步步高',
        u'UKING': u'UKING/宇康',
        u'YAS': u'YAS/扬新',
        u'VOTO': u'VOTO/维图',
        u'Vinus': u'Vinus/维纳斯',
        u'datang': u'datang/大唐',
        u'Samsung/三星': u'SAMSUNG/三星',
        u'Sigma/适马': u'SIGMA/适马',
        u'Canon/佳能700D 18-55': u'Canon/佳能',
        u'Canon/佳能600D': u'Canon/佳能',
        u'哈苏': u'hasselblad/哈苏',
        u'科尼尔美能达': u'KONICA MINOLTA/柯尼卡美能达',
        u'宝丽来': u'Polaroid/宝丽来',
        u'Canon/佳能700D(18-55)': u'Canon/佳能',
        u'TCL型号': u'TCL',
        u'Polaroid': u'Polaroid/宝丽来',
        u'宝丽来/Polaroid': u'Polaroid/宝丽来',
        u'Nikon/尼康/D3200': u'Nikon/尼康',
        u'富士': u'FINEPIX/富士',
        u'KENKO': u'KENKO/肯高',
        u'polaroid': u'Polaroid/宝丽来',
        u'Fujifilm/富士 Instax mini50s': u'Fujifilm/富士',
        u'vitoret福伦达': u'vitoret/福伦达',
        u'Canon/佳能7D': u'Canon/佳能',
        u'禄莱': u'rollei/禄莱',
        u'Nikon/尼康 D1X': u'Nikon/尼康',
        u'富士（Fujifilm）': u'Fujifilm/富士',
        u'Terrans Force': u'Terrans Force/地球人',
        u'Colorfly': u'Colorfly/七彩虹',
        u'纽曼': u'Newsmy/纽曼',
        u'tg': u'tg/天机',
        u'FNF': u'FNF/五元素',
        u'乐凡': u'Livefan/乐凡',
        u'MOONSE 满石': u'MOONSE/满石',
        u'Ampe': u'Ampe/爱魅',
        u'影驰': u'GALAXY/影驰',
        u'爱可视': u'ARCHOS/爱可视',
        u'Soaye': u'Soaye/首亿',
        u'QRTECH': u'QRTECH/麦本本',
        u'Showtone': u'Showtone/搜通',
        u'Sigo': u'Sigo/思歌',
        u'AMD': u'AMD/速龙',
        u'HIS': u'HIS/希仕',
        u'AOC': u'AOC/冠捷',
        u'EIZO': u'EIZO/艺卓',
        u'ICON': u'ICON/艾肯',
        u'赛睿': u'Steelseries/赛睿',
        u'明基': u'BenQ/明基',
        u'G.Skill': u'G.Skill/芝奇',
        u'ZALMAN': u'ZALMAN/扎曼',
        u'OCZ': u'OCZ/饥饿鲨',
        u'silverstone': u'silverstone/银欣',
        u'Cherry樱桃': u'Cherry/樱桃',
        u'ALUTEK': u'ALUTEK/阿鲁钛克',
        u'AOC': u'AOC/冠捷',
        u'NEC': u'NEC/日本电气',
        u'华擎': u'Asrock/华擎',
        u'Aisino': u'Aisino/爱信诺',
        u'西门子SIMATIC': u'SIMATIC/西门子',
        u'soncci': u'soncci/索奇',
        u'Thinkstation': u'Thinkstation/联想工作站',
        u'联想': u'lenovo/联想',
        u'三星': u'Samsung/三星',
        u'苹果': u'Apple/苹果',
        u'小米': u'MIUI/小米',
        u'艾沃': u'IWO/艾沃',
        u'联想': u'Lenovo/联想',
        u'漫语': u'MOYOU/漫语',
        u'华为': u'HUAWEI/华为',
        u'西门子': u'SIMENS/西门子',
        u'步步高': u'VIVO/步步高',
        u'意达欧': u'YIDAOU/意达欧',
        u'索爱': u'sony ericsson/索爱',
        u'ez Share': u'ez Share/易享派',
        u'思异 SYii': u'SYii/思异',
        u'睿志': u'reamax/睿志',
        u'绿帆': u'LVFAN/绿帆',
        u'Echoii': u'Echoii/一可',
        u'Gigastone': u'Gigastone/立达',
        u'TRUS': u'TRUS/趋势',
        u'GPRINTER': u'GPRINTER/佳博',
        u'佳博': u'GPRINTER/佳博',
        u'ZECO': u'ZECO/智歌',
        u'铼德Ritek': u'Ritek/铼德',
        u'GODEX': u'GODEX/科诚',
        u'海美迪': u'himedia/海美迪',
        u'开博尔': u'kaiboer/开博尔',
        u'skullcandy': u'skullcandy/骷髅头',
        u'google': u'Google/谷歌',
        u'TEMEISHENG': u'TEMEISHENG/特美声',
        u'WONDERFLOWER': u'WONDERFLOWER/樱花',
        u'广州樱花': u'WONDERFLOWER/樱花',
        u'林内': u'Rinnai/林内',
        u'RISUN': u'RISUN/理想',
        u'um 优盟': u'um/优盟',
        u'欧尼尔': u'ounier/欧尼尔',
        u'华帝': u'vatti/华帝',
        u'AOC': u'AOC/冠捷',
        u'AOSLNMSI': u'AOSLNMSI/斯密斯',
        u'樱花': u'WONDERFLOWER/樱花',
        u'碧然德': u'brita/碧然德',
        u'艾玛': u'emma/艾玛',
        u'Hauswirt': u'海氏/Hauswirt',
        u'米技': u'米技/MIJI',
        u'Vitamix': u'Vitamix/维他美仕',
        u'ECOWATER': u'怡口/ECOWATER',
        u'kang er da': u'kang er da/康尔达',
        u'Paiter': u'Paiter/百特',
        u'Kemei': u'Kemei//科美',
        u'沙宣': u'VS/沙宣',
        u'Le Er Kang': u'Le Er Kang/乐尔康',
        u'seago': u'seago/赛嘉',
        u'科勒': u'KOHLER/科勒',
        u'多乐士': u'Dulux/多乐士',
        u'摩恩': u'MOEN/摩恩',
        u'箭牌': u'ARROW/箭牌',
        u'MAWUI 麦辉': u'MAWUI/麦辉',
        u'汉斯格雅': u'hansgrohe/汉斯格雅',
        u'美标': u'American Standard/美标',
        u'FSL': u'FSL/佛山照明',
        u'松下': u'Panasonic/松下',
        u'GAOLANG 高朗': u'GAOLANG/高朗',
        u'L＆D': u'L＆D/特地',
        u'skno': u'skno/塞克洛',
        u'百佳宜 baijiayi': u'baijiayi/百佳宜',
        u'NSURE': u'NSURE/苏美',
        u'Ijarl': u'Ijarl/亿嘉',
        u'星巴克': u'starbucks/星巴克',
        u'优芬': u'youful/优芬',
        u'lovo': u'lovo/罗莱',
        u'罗莱': u'lovo/罗莱',
        u'yiQin 伊沁': u'yiQin/伊沁',
        u'devids': u'devids/黛维斯',
        u'LADYSOFT': u'LADYSOFT/御棉堂',
    }
    if isinstance(brand, str):
        brand = brand.decode('utf-8')

    if brand in ['', None]:
        brand = u'无品牌'
    else:
        m = re.compile(ur'(^其它|^其他|^国内其它|^国内其他|^other|.*其他|.*其它|专柜正品|厂商直销$)', re.IGNORECASE).match(brand)
        if m:
            brand = u'无品牌'

    if brand in aliases:
        brand = aliases[brand]

    return brand

def get_l1_and_l2_cids(cids):
    l1l2 = {}
    for cid in cids:
        if cid in cates:
            cidchain = []
            while cates[cid] != 0:
                cidchain.append(cid)
                cid = cates[cid]
            cidchain.append(cid)
            try:
                l1l2[ cidchain[0] ] = (cidchain[-1], cidchain[-2])
            except:
                if len(cidchain) == 1:
                    l1l2[cid] = [cid, 'all']
    return l1l2

defaultdate = (datetime.utcnow()+timedelta(hours=-16)).strftime("%Y-%m-%d")

def aggregate_items(start, end, hosts=[], date=None, retry=0):
    if retry >= 20:
        raise Exception('retry too many times, give up')

    if start > end:
        aggregate_items(start, 2**63-1, hosts, date, retry)
        aggregate_items(-2**63, end, hosts, date, retry)

    try:
        db = getdb()
        if date is None:
            date = defaultdate
        datestr = date
        date2 = datetime.strptime(date, "%Y-%m-%d")+timedelta(hours=16)
        date1 = date2 - timedelta(days=60)
        si = ShopIndex(date)
        ii = ItemIndex(date)
        bi = BrandIndex(date)
        ci = CategoryIndex(date)
        si.multi()
        ii.multi()
        bi.multi()
        ci.multi()

        try:
            if hosts:
                d2 = calendar.timegm(date2.utctimetuple())*1000
                d1 = calendar.timegm(date1.utctimetuple())*1000
                host = hosts[0]
                conn = db.get_connection(host)
                cur = conn.cursor()
                cur.execute('''select id, shopid, cid, num_sold30, price, brand, title, image, num_reviews, credit_score, title, type
                    from ataobao2.item where token(id)>=:start and token(id)<:end''',
                    dict(start=int(start), end=int(end)))
                iteminfos = list(cur)
                cur.execute('''select id, date, num_collects, num_reviews, num_sold30, num_views, price from ataobao2.item_by_date 
                    where token(id)>:start and token(id)<=:end and date>=:date1 and date<:date2 allow filtering''',
                    dict(start=int(start), end=int(end), date1=d1, date2=d2))
                itemts = list(cur)
                conn.close()
            else:
                iteminfos = db.execute('''select id, shopid, cid, num_sold30, price, brand, title, image, num_reviews, credit_score, title, type
                    from ataobao2.item where token(id)>=:start and token(id)<:end''',
                    dict(start=int(start), end=int(end)), result=True).results
                itemts = db.execute('''select id, date, num_collects, num_reviews, num_sold30, num_views, price from ataobao2.item_by_date 
                    where token(id)>:start and token(id)<=:end and date>=:date1 and date<:date2 allow filtering''',
                    dict(start=int(start), end=int(end), date1=d1, date2=d2), result=True).results
        except:
            print('cluster error on host {}, range {}, retry {}, sleeping 5 secs...'.format(hosts[0], (start, end), retry))
            hosts = hosts[-1:] + hosts[:-1]
            #traceback.print_exc()
            time.sleep(30)
            return aggregate_items(start, end, date=date, hosts=hosts, retry=retry+1)


        itemtsdict = {}
        for row in itemts:
            itemid, date, values = row[0], row[1], list(row[2:])
            # fix data malform
            # 1. num_colllects, index at 0, should not larger than 2**24 ~ 16 million
            if values[0] > 2**24:
                values[0] = 0
            if isinstance(date, datetime):
                date = (date+timedelta(hours=8)).strftime("%Y-%m-%d")
            else:
                date = datetime.utcfromtimestamp(struct.unpack('!q', date)[0]/1000)
                date = (date+timedelta(hours=8)).strftime("%Y-%m-%d")
            if itemid not in itemtsdict:
                itemtsdict[itemid] = {}
            itemtsdict[itemid][date] = values


        for itemid, shopid, cid, nc, price, brand, name, image, nr, credit_score, title, type in iteminfos:
            if in_blacklist(shopid, price, cid, nc, nr, credit_score, title, type, itemid=itemid):
                #print itemid, 'skiped'
                continue
            brand = clean_brand(brand)
            if nc > 0 and itemid in itemtsdict and itemtsdict[itemid]:
                try:
                    if shopid == 0:
                        db.execute('delete from ataobao2.item where id=:id', dict(id=itemid))
                        db.execute('delete from ataobao2.item_by_date where id=:id', dict(id=itemid))
                        continue
                except:
                    traceback.print_exc()
                try:
                    aggregate_item(si, ii, bi, ci, itemid, itemtsdict[itemid], shopid, cid, price, brand, name, image, datestr)
                except:
                    traceback.print_exc()

        si.execute()
        bi.execute()
        ci.execute()
        ii.execute()
    except:
        traceback.print_exc()


def parse_iteminfo(date, itemid, items, price, cid):
    if not items:
        return

    date2 = datetime.strptime(date, "%Y-%m-%d")+timedelta(hours=16)
    date1 = date2 - timedelta(days=60)
    d1 = date
    d2 = (date2 - timedelta(days=2)).strftime("%Y-%m-%d")
    d3 = (date2 - timedelta(days=3)).strftime("%Y-%m-%d")
    d31 = (date2 - timedelta(days=31)).strftime("%Y-%m-%d")
    d32 = (date2 - timedelta(days=32)).strftime("%Y-%m-%d")
    d61 = (date2 - timedelta(days=61)).strftime("%Y-%m-%d")
    d62 = (date2 - timedelta(days=62)).strftime("%Y-%m-%d")
    if d1 not in items:
        items[d1] = items[sorted(items.keys())[-1]]

    try:
        l1, l2 = get_l1_and_l2_cids([cid])[cid]
    except:
        return

    i1 = items[d1]
    i2 = items.get(d2, i1)
    i3 = items.get(d3, i2)
    i31 = items.get(d31, i1)
    i32 = items.get(d32, i2)
    i61 = items.get(d61, i31)
    i62 = items.get(d62, i32)
    active_index_day = max(0, (i1[1]-i2[1])*50 + (i1[0]-i2[0])*10 + (i1[3]-i2[3]))
    delta_active_index_day = active_index_day - max(0, (i2[1]-i3[1])*50 - (i2[0]-i3[0])*10 - (i2[3]-i3[3]))
    active_index_mon = max(0, (i1[1]-i31[1])*50 + (i1[0]-i31[0])*10 + (i1[3]-i31[3]))
    delta_active_index_mon = active_index_mon - max(0, (i31[1]-i61[1])*50 - (i31[0]-i61[0])*10 - (i31[3]-i61[3]))
    deals_mon = i1[2]
    if d31 in items:
        deals_day = i1[2] - (i2[2] - i31[2])
    else:
        deals_day = i1[2]//30
    if d32 in items:
        deals_day1 = i2[2] - (i3[2] - i32[2])
    else:
        deals_day1 = i2[2]//30

    price = i1[-1]
    sales_mon = deals_mon * price
    sales_day = deals_day * price
    delta_sales_mon = deals_mon * price - i2[2] * price
    delta_sales_day = deals_day * price - deals_day1 * price

    return locals()


def aggregate_item(si, ii, bi, ci, itemid, items, shopid, cid, price, brand, name, image, date):
    info = parse_iteminfo(date, itemid, items, price, cid)
    if not info:
        return

    for key, value in info.items():
        locals()[key] = value
        globals()[key] = value

    brand = brand.encode('utf-8')

    # inc category counters
    for mod in ['day', 'mon']:
        inc = {
            'sales': locals()['sales_'+mod],
            'deals': locals()['deals_'+mod],
            'delta_sales': locals()['delta_sales_'+mod],
            'items': 1,
        }
        ci.incrinfo(l1, l2, mod, inc)
        if l2 != 'all':
            ci.incrinfo(l1, 'all', mod, inc)
    if brand != '无品牌':
        ci.addbrand(l1, l2, brand)
        if l2 != 'all':
            ci.addbrand(l1, 'all', brand)

    # inc brand counters
    from aggregator.brands import brands as needaggbrands
    # if brand.decode('utf-8') in needaggbrands:
    if True:
        bi.addbrand(brand)

        bi.addshop(brand, l1, l2, shopid)
        bi.addcates(brand, l1, l2)
        if l2 != 'all':
            bi.addshop(brand, l1, 'all', shopid)
            bi.addcates(brand, l1, 'all')
        bi.addhots(brand, l1, itemid, shopid, sales_mon)
        if l2 != 'all':
            bi.addhots(brand, l2, itemid, shopid, sales_mon)
        inc = {
            'items': 1,
            'deals': deals_mon,
            'sales': sales_mon,
            'delta_sales': delta_sales_mon,
        }
        bi.incrinfo(brand, l1, l2, inc)
        if l2 != 'all':
            bi.incrinfo(brand, l1, 'all', inc)

    # inc item counters
    ii.incrcates(l1, l2, sales_mon, deals_mon)
    if l2 != 'all':
        ii.incrcates(l1, 'all', sales_mon, deals_mon)
    ii.incrindex(l1, l2, 'sales', 'mon', itemid, sales_mon)
    if l2 != 'all':
        ii.incrindex(l1, 'all', 'sales', 'mon', itemid, sales_mon)
    ii.incrindex(l1, l2, 'sales', 'day', itemid, sales_day)
    if l2 != 'all':
        ii.incrindex(l1, 'all', 'sales', 'day', itemid, sales_day)

    # inc shop counters
    si.addcates(shopid, l1, l2)
    si.incrbrand(shopid, 'sales', 'mon', brand, sales_mon)
    si.incrbrand(shopid, 'deals', 'mon', brand, deals_mon)
    si.incrbrand(shopid, 'sales', 'day', brand, sales_day)
    si.incrbrand(shopid, 'deals', 'day', brand, deals_day)
    si.addhotitems(shopid, itemid, sales_mon)

    cate1 = l1
    for cate2 in set(['all', l2]):
        for period in ['mon', 'day']:
            inc = {'sales':locals()['sales_'+period],
                   'deals':locals()['deals_'+period],
                   'delta_sales': locals()['delta_sales_'+period],
                   'active_index': locals()['active_index_'+period],
                   'delta_active_index': locals()['delta_active_index_'+period]}
            si.incrinfo(cate1, cate2, period, shopid, inc)
    inc = {'sales_mon': sales_mon,
           'sales_day': sales_day,
           'deals_mon': deals_mon,
           'deals_day': deals_day,
           'active_index_mon': active_index_mon,
           'active_index_day': active_index_day}
    si.incrbase(shopid, inc)


class ItemAggProcess(Process):
    def __init__(self, date=None):
        super(ItemAggProcess, self).__init__('itemagg')
        if ENV == 'DEV':
            self.step = 256*10
            self.max_workers = 10
        else:
            self.step = 256*10*200
            self.max_workers = 500
        self.date = date

    def generate_tasks(self):
        self.clear_redis()
        conn = getdb().get()
        tclient = conn.client
        ring = tclient.describe_ring('ataobao2')
        conn.close()
        tokens = len(ring)
        tasks = defaultdict(list)
        v264 = 2**64
        v263_1 = 2**63-1
        step = v264 // self.step
        #slicepertoken = self.step/tokens
        for tokenrange in ring:
            ostart = int(tokenrange.start_token)
            oend = int(tokenrange.end_token)
            slicepertoken = (oend - ostart) // step if ostart < oend else (v264+oend - ostart) // step
            #step = (oend - ostart) // slicepertoken if ostart < oend else (v264+oend - ostart) // slicepertoken
            hosts = tokenrange.endpoints
            for i in range(slicepertoken):
                start = ostart + step * i
                end = start + step
                if start > v263_1:
                    start -= v264
                if end > v263_1:
                    end -= v264
                tasks[hosts[0]].append(['aggregator.itemagg.aggregate_items', (start, end), dict(date=self.date, hosts=hosts)])
            start = ostart + slicepertoken*step
            end = oend
            tasks[hosts[0]].append(['aggregator.itemagg.aggregate_items', (start, end), dict(date=self.date, hosts=hosts)])
        universe_tasks = []
        # averaging tasks
        #for _ in range(40):
        #    lenhosts = sorted([[len(tasks[host]), host] for host in tasks])
        #    delta = (lenhosts[-1][0] - lenhosts[0][0]) // 2
        #    if delta > 0 and len(tasks) > 1:
        #        print 'inequality index', delta
        #        for task in tasks[lenhosts[-1][1]][-delta:]:
        #            task[2]['hosts'] = task[2]['hosts'][-1:] + task[2]['hosts'][:-1]
        #            tasks[task[2]['hosts'][0]].insert(0, task)
        #        tasks[lenhosts[-1][1]] = tasks[lenhosts[-1][1]][:-delta]
        while sum(map(len, tasks.itervalues())):
            for host in tasks:
                if tasks[host]:
                    task = tasks[host].pop()
                    universe_tasks.append(task)
        self.add_tasks(*universe_tasks)
        self.finish_generation()

iap = ItemAggProcess()

if __name__ == '__main__':
    #iap.date = '2013-12-04'
    #iap.start()
    #aggregate_items(start=-5897829018164995167-1, end=-5897829018164995167+1, hosts=['54.199.146.135'], date='2014-01-19')
    pass
