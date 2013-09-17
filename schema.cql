CREATE KEYSPACE IF NOT EXISTS ataobao2
    WITH replication = {'class':'SimpleStrategy', 'replication_factor':1};

USE ataobao2;

CREATE TABLE IF NOT EXISTS shop (
    id              bigint PRIMARY KEY,
    sid             bigint,
    rateid          text,
    nick            text,
    created         timestamp,
    modified        timestamp,
    charge          text,
    promise         text,
    pic_path        text,
    rating          text,
    cid             int,
    rank            text,
    num_collects    int,
    title           text,
    good_rating     float,
);

CREATE TABLE IF NOT EXISTS item (
    id              bigint PRIMARY KEY,
    cid             int,
    rcid            int,
    shopid          int,
    pagetype        text,
    title           text,
    price           float,
    rating          float,
    num_collects    int,
    num_instock     int,
    num_reviews     int,
    num_sold30      int,
    num_views       int,
);

CREATE TABLE IF NOT EXISTS shop_by_item (
    id              bigint,
    date            timestamp,
    iid             bigint,
    PRIMARY KEY (id, date)
);
 
CREATE TABLE IF NOT EXISTS item_by_date (
    id              bigint,
    date            timestamp,
    title           text,
    price           float,
    num_collects    int,
    num_instock     int,
    num_reviews     int,
    num_sold30      int,
    num_views       int,
    PRIMARY KEY (id, date)
);

CREATE TABLE IF NOT EXISTS shop_by_date (
    id              bigint,
    date            timestamp,
    rating          text,
    cid             int,
    rank            text,
    num_collects    int,
    title           text,
    good_rating     float,
    PRIMARY KEY (id, date)
);

CREATE TABLE IF NOT EXISTS item_attr (
    id              bigint,
    attr_name       text,
    attr_value      text,
    PRIMARY KEY (id, attr_name)
);
