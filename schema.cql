/*
 * Cassandra Schemas
 * 
 * Import this file into cassandra::
 *
 *     $cqlsh host port -f schema.cql
 *
 * Or, check schemas using script::
 *     
 *     $source env.sh DEV 
 *     $python scripts/checkschema.py 
 *     ...
 *     $#if there are fix plans in output, review them, and execute them by
 *     $python scripts/checkschema.py --fix
 */
CREATE KEYSPACE IF NOT EXISTS ataobao2
    WITH replication = {'class':'SimpleStrategy', 'replication_factor':3};

USE ataobao2;

CREATE TABLE IF NOT EXISTS shop (
    id              bigint PRIMARY KEY,
    sid             bigint,
    type            text,
    mobile          text,
    rateid          text,
    nick            text,
    charge          text,
    promise         text,
    logo            text,
    main_sale       text,
    rank            text,
    rank_num        int,
    num_collects    int,
    title           text,
    rates           text,
    rating          text,
    good_rating     float,
);

CREATE TABLE IF NOT EXISTS item (
    id              bigint PRIMARY KEY,
    cid             int,
    rcid            int,
    brand           text,
    image           text,
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
    sales           float,
    worth           float,
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

CREATE TABLE IF NOT EXISTS brand (
    name            text,
    logo            text,
    PRIMARY KEY (name)
);

CREATE TABLE IF NOT EXISTS brand_by_date (
    name            text,
    date            timestamp, 
    cate1           int,
    sales           float,
    share           float,
    num_shops       int,
    PRIMARY KEY (name, date, cate1)
);
