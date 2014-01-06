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
    /* WITH replication = {'class':'NetworkTopologyStrategy', 'DC1':3, 'DC2':3}; */

USE ataobao2;

CREATE TABLE IF NOT EXISTS shop (
    id              bigint PRIMARY KEY,
    sid             bigint,
    logo            text,
    type            text,
    nick            text,
    title           text,
    prov            text,
    city            text,
    credit_score    int,
    num_collects    int,
    num_products    int,
    good_rating     text,
    rating          text,
    created_at      text,
    mobile          text,

    charge          text,
    promise         text,
    main_sale       text,
);

CREATE TABLE IF NOT EXISTS item (
    id              bigint PRIMARY KEY,
    type            text,
    cid             int,
    brand           text,
    image           text,
    shopid          int,
    title           text,
    oprice          float,
    price           float,
    num_collects    int,
    num_instock     int,
    num_reviews     int,
    num_sold30      int,
    num_views       int,
    promo           text,
    delivery_type   int,
    soldout         boolean,
    status          text,
    credit_score    int,
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
    datestr         text,
    rating          text,
    cid             int,
    brandshare      text,
    cateshare       text,
    catetrend       text,
    sales           float,
    worth           float,
    num_collects    int,
    title           text,
    good_rating     float,
    PRIMARY KEY (id, datestr)
);

CREATE TABLE IF NOT EXISTS brand (
    name            text,
    logo            text,
    PRIMARY KEY (name)
);

CREATE TABLE IF NOT EXISTS brand_by_date (
    name            text,
    datestr         text, 
    cate1           int,
    sales           float,
    share           float,
    num_shops       int,
    PRIMARY KEY (name, datestr, cate1)
);

CREATE TABLE IF NOT EXISTS top10 (
    datestr         text,
    field           text,
    value           text,
    PRIMARY KEY (datestr, field)
);

CREATE TABLE IF NOT EXISTS blacklist (
    type            text,
    args            text,
    value           text,
    PRIMARY KEY (type, args)
);

CREATE TABLE IF NOT EXISTS agghosts (
    datestr         text,
    hosts           text,
    ready           boolean,
    PRIMARY KEY (datestr)
);
