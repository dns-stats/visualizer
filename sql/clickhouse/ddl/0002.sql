--- Copyright 2021 Internet Corporation for Assigned Names and Numbers.
---
--- This Source Code Form is subject to the terms of the Mozilla Public
--- License, v. 2.0. If a copy of the MPL was not distributed with this
--- file, you can obtain one at https://mozilla.org/MPL/2.0/.
---
--- Developed by Sinodun IT (sinodun.com)
---
--- Create tables accessing dictionaries.
---
CREATE TABLE dsv.node_text
(
    node_id UInt16,
    name String,
    server_name String,
    instance_name String,
    city_name String,
    country_name String,
    region_name String,
    flags UInt64
)
ENGINE = Dictionary('node_text');

CREATE TABLE dsv.server_address
(
    id UInt64,
    address String
)
ENGINE = Dictionary('server_address');

CREATE TABLE dsv.iana_text
(
    registry_name String,
    value_name String,
    value UInt32,
    value_description String
)
ENGINE = Dictionary('iana_text');

CREATE TABLE dsv.tld_text
(
    name String,
    tld_type String,
    ulabel String
)
ENGINE = Dictionary('tld_text');

CREATE TABLE dsv.geolocation
(
    id UInt64,
    country_id UInt64,
    name String,
    latitude Float32,
    longitude Float32
)
ENGINE = Dictionary('geolocation');
