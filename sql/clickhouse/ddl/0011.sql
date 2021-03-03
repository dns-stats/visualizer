--- Copyright 2021 Internet Corporation for Assigned Names and Numbers.
---
--- This Source Code Form is subject to the terms of the Mozilla Public
--- License, v. 2.0. If a copy of the MPL was not distributed with this
--- file, you can obtain one at https://mozilla.org/MPL/2.0/.
---
--- Developed by Sinodun IT (sinodun.com)
--
--- Create five minute aggregation tables.
---

CREATE DATABASE IF NOT EXISTS dsv_five_minute;

CREATE TABLE dsv_five_minute.QueriesShard
(
    Date Date,
    DateTime DateTime,
    NodeID UInt16,
    QueryCount UInt32,
    QueryOpcodeMap Nested
    (
        QueryOpcode UInt8,
        Count UInt32
    ),
    QueryTypeMap Nested
    (
        QueryType UInt16,
        Count UInt32
    ),
    QueryClassMap Nested
    (
        QueryClass UInt16,
        Count UInt32
    ),
    QueryDOCount UInt32,
    QueryRecursionDesiredCount UInt32,
    QueryCheckingDisabledCount UInt32,
    TransportIPv6Count UInt32,
    TransportTCPMap Nested
    (
        TransportTCP UInt8,
        Count UInt32
    )
)
ENGINE = SummingMergeTree()
PARTITION BY toYearWeek(Date)
ORDER BY (Date, DateTime, NodeID);

CREATE MATERIALIZED VIEW dsv_five_minute.QueriesShardMV
TO dsv_five_minute.QueriesShard
AS SELECT
    Date,
    toStartOfFiveMinute(DateTime) AS DateTime,
    NodeID,
    CAST(1 as UInt32) AS QueryCount,
    [QueryOpcode] AS `QueryOpcodeMap.QueryOpcode`,
    [CAST(1 AS UInt32)] AS `QueryOpcodeMap.Count`,
    [QueryType] AS `QueryTypeMap.QueryType`,
    [CAST(1 AS UInt32)] AS `QueryTypeMap.Count`,
    [QueryClass] AS `QueryClassMap.QueryClass`,
    [CAST(1 AS UInt32)] AS `QueryClassMap.Count`,
    CAST(QueryDO AS UInt32) AS QueryDOCount,
    CAST(QueryRecursionDesired AS UInt32) AS QueryRecursionDesiredCount,
    CAST(QueryCheckingDisabled AS UInt32) AS QueryCheckingDisabledCount,
    CAST(TransportIPv6 AS UInt32) AS TransportIPv6Count,
    [TransportTCP] AS `TransportTCPMap.TransportTCP`,
    [CAST(1 AS UInt32)] AS `TransportTCPMap.Count`
FROM dsv.QueryResponseShard
WHERE QueryResponseHasQuery;

---
--- Create distributed table for aggregated query counts.
---
CREATE TABLE dsv_five_minute.Queries
(
    Date Date,
    DateTime DateTime,
    NodeID UInt16,
    QueryCount UInt32,
    QueryOpcodeMap Nested
    (
        QueryOpcode UInt8,
        Count UInt32
    ),
    QueryTypeMap Nested
    (
        QueryType UInt16,
        Count UInt32
    ),
    QueryClassMap Nested
    (
        QueryClass UInt16,
        Count UInt32
    ),
    QueryDOCount UInt32,
    QueryRecursionDesiredCount UInt32,
    QueryCheckingDisabledCount UInt32,
    TransportIPv6Count UInt32,
    TransportTCPMap Nested
    (
        TransportTCP UInt8,
        Count UInt32
    )
)
ENGINE = Distributed(dsv, dsv_five_minute, QueriesShard);

---
--- Create local shard aggregated response counts.
---
CREATE TABLE dsv_five_minute.ResponsesShard
(
    Date Date,
    DateTime DateTime,
    NodeID UInt16,
    ResponseCount UInt32,
    ResponseRcodeMap Nested
    (
        ResponseRcode UInt16,
        Count UInt32
    ),
    ResponseRecursionAvailableCount UInt32,
    ResponseAuthoritativeAnswerCount UInt32,
    ResponseUDPTruncatedCount UInt32,
    TransportIPv6Count UInt32,
    TransportTCPMap Nested
    (
        TransportTCP UInt8,
        Count UInt32
    ),
    QueryTypeWithAnswerMap Nested
    (
        QueryType UInt16,
        Count UInt32
    )
)
ENGINE = SummingMergeTree()
PARTITION BY toYearWeek(Date)
ORDER BY (Date, DateTime, NodeID);

CREATE MATERIALIZED VIEW dsv_five_minute.ResponsesShardMV
TO dsv_five_minute.ResponsesShard
AS SELECT
    Date,
    toStartOfFiveMinute(DateTime) AS DateTime,
    NodeID,
    CAST(1 as UInt32) AS ResponseCount,
    [ResponseRcode] AS `ResponseRcodeMap.ResponseRcode`,
    [CAST(1 AS UInt32)] AS `ResponseRcodeMap.Count`,
    CAST(ResponseRecursionAvailable AS UInt32) AS ResponseRecursionAvailableCount,
    CAST(ResponseAuthoritativeAnswer AS UInt32) AS ResponseAuthoritativeAnswerCount,
    CAST(TransportTCP == 0 AND ResponseTruncated AS UInt32) AS ResponseUDPTruncatedCount,
    CAST(TransportIPv6 AS UInt32) AS TransportIPv6Count,
    [TransportTCP] AS `TransportTCPMap.TransportTCP`,
    [CAST(1 AS UInt32)] AS `TransportTCPMap.Count`,
    [QueryType] AS `QueryTypeWithAnswerMap.QueryType`,
    [CAST(ResponseANCount > 0 AS UInt32)] AS `QueryTypeWithAnswerMap.Count`
FROM dsv.QueryResponseShard
WHERE QueryResponseHasResponse;

---
--- Create distributed table for aggregated response counts.
---
CREATE TABLE dsv_five_minute.Responses
(
    Date Date,
    DateTime DateTime,
    NodeID UInt16,
    ResponseCount UInt32,
    ResponseRcodeMap Nested
    (
        ResponseRcode UInt16,
        Count UInt32
    ),
    ResponseRecursionAvailableCount UInt32,
    ResponseAuthoritativeAnswerCount UInt32,
    ResponseUDPTruncatedCount UInt32,
    TransportIPv6Count UInt32,
    TransportTCPMap Nested
    (
        TransportTCP UInt8,
        Count UInt32
    ),
    QueryTypeWithAnswerMap Nested
    (
        QueryType UInt16,
        Count UInt32
    )
)
ENGINE = Distributed(dsv, dsv_five_minute, ResponsesShard);

---
--- Aggregations for specific plots.
---

---
--- Create local shard aggregated ServerAddressTransport counts.
---
CREATE TABLE dsv_five_minute.ServerAddressTransportShard
(
    Date Date,
    DateTime DateTime,
    NodeID UInt16,
    ServerAddress FixedString(16),
    TransportTCP UInt8,
    Count UInt32
)
ENGINE = SummingMergeTree()
PARTITION BY toYearWeek(Date)
ORDER BY (Date, DateTime, NodeID, ServerAddress, TransportTCP);

CREATE MATERIALIZED VIEW dsv_five_minute.ServerAddressTransportShardMV
TO dsv_five_minute.ServerAddressTransportShard
AS SELECT
    Date,
    toStartOfFiveMinute(DateTime) AS DateTime,
    NodeID,
    ServerAddress,
    TransportTCP,
    CAST(1 AS UInt32) AS Count
FROM dsv.QueryResponseShard
WHERE ServerAddress IN (
    SELECT IPv6StringToNum(address) FROM dsv.server_address );

---
--- Create distributed table for aggregated ServerAddressTransport counts.
---
CREATE TABLE dsv_five_minute.ServerAddressTransport
(
    Date Date,
    DateTime DateTime,
    NodeID UInt16,
    ServerAddress FixedString(16),
    TransportTCP UInt8,
    Count UInt32
)
ENGINE = Distributed(dsv, dsv_five_minute, ServerAddressTransportShard);

---
--- Create local shard aggregated IDNQuery counts.
---
CREATE TABLE dsv_five_minute.IDNQueryCountShard
(
    Date Date,
    DateTime DateTime,
    NodeID UInt16,
    Count UInt32
)
ENGINE = SummingMergeTree()
PARTITION BY toYearWeek(Date)
ORDER BY (Date, DateTime, NodeID);

CREATE MATERIALIZED VIEW dsv_five_minute.IDNQueryCountShardMV
TO dsv_five_minute.IDNQueryCountShard
AS SELECT
    Date,
    toStartOfFiveMinute(DateTime) AS DateTime,
    NodeID,
    CAST(1 AS UInt32) AS Count
FROM dsv.QueryResponseShard
WHERE QueryResponseHasQuery AND startsWith(QueryName, 'xn--');

---
--- Create distributed table for aggregated IDNQuery counts.
---
CREATE TABLE dsv_five_minute.IDNQueryCount
(
    Date Date,
    DateTime DateTime,
    NodeID UInt16,
    Count UInt32
)
ENGINE = Distributed(dsv, dsv_five_minute, IDNQueryCountShard);

---
--- Create local shard aggregated QtypePopularQueryNames counts.
---
CREATE TABLE dsv_five_minute.QtypePopularQueryNamesShard
(
    Date Date,
    DateTime DateTime,
    NodeID UInt16,
    PopularQueryName String,
    QueryType UInt16,
    Count UInt32
)
ENGINE = SummingMergeTree()
PARTITION BY toYearWeek(Date)
ORDER BY (Date, DateTime, NodeID, PopularQueryName, QueryType);

CREATE MATERIALIZED VIEW dsv_five_minute.QtypePopularQueryNamesShardMV
TO dsv_five_minute.QtypePopularQueryNamesShard
AS SELECT
    Date,
    toStartOfFiveMinute(DateTime) AS DateTime,
    NodeID,
    multiIf(QueryName = 'localhost', QueryName, '*.root-servers.net') AS PopularQueryName,
    QueryType,
    CAST(1 AS UInt32) AS Count
FROM dsv.QueryResponseShard
WHERE QueryResponseHasQuery AND
      ( QueryName = 'localhost' OR positionCaseInsensitive(QueryName, '.root-servers.net') > 0 );

---
--- Create distributed table for aggregated QtypePopularQueryNames counts.
---
CREATE TABLE dsv_five_minute.QtypePopularQueryNames
(
    Date Date,
    DateTime DateTime,
    NodeID UInt16,
    PopularQueryName String,
    QueryType UInt16,
    Count UInt32
)
ENGINE = Distributed(dsv, dsv_five_minute, QtypePopularQueryNamesShard);

---
--- Create local shard aggregated QtypeQueryNameLength counts.
---
CREATE TABLE dsv_five_minute.QtypeQueryNameLengthShard
(
    Date Date,
    DateTime DateTime,
    NodeID UInt16,
    QueryNameLength UInt16,
    QueryType UInt16,
    Count UInt32
)
ENGINE = SummingMergeTree()
PARTITION BY toYearWeek(Date)
ORDER BY (Date, DateTime, NodeID, QueryNameLength, QueryType);

CREATE MATERIALIZED VIEW dsv_five_minute.QtypeQueryNameLengthShardMV
TO dsv_five_minute.QtypeQueryNameLengthShard
AS SELECT
    Date,
    toStartOfFiveMinute(DateTime) AS DateTime,
    NodeID,
    toUInt16(length(QueryName)) AS QueryNameLength,
    QueryType,
    CAST(1 AS UInt32) AS Count
FROM dsv.QueryResponseShard
WHERE QueryResponseHasQuery;

---
--- Create distributed table for aggregated QtypeQueryNameLength counts.
---
CREATE TABLE dsv_five_minute.QtypeQueryNameLength
(
    Date Date,
    DateTime DateTime,
    NodeID UInt16,
    QueryNameLength UInt16,
    QueryType UInt16,
    Count UInt32
)
ENGINE = Distributed(dsv, dsv_five_minute, QtypeQueryNameLengthShard);

---
--- Create local shard aggregated QtypeIpVersion counts.
---
CREATE TABLE dsv_five_minute.QtypeIpVersionShard
(
    Date Date,
    DateTime DateTime,
    NodeID UInt16,
    TransportIPv6 UInt8,
    QueryType UInt16,
    Count UInt32
)
ENGINE = SummingMergeTree()
PARTITION BY toYearWeek(Date)
ORDER BY (Date, DateTime, NodeID, TransportIPv6, QueryType);

CREATE MATERIALIZED VIEW dsv_five_minute.QtypeIpVersionShardMV
TO dsv_five_minute.QtypeIpVersionShard
AS SELECT
    Date,
    toStartOfFiveMinute(DateTime) AS DateTime,
    NodeID,
    TransportIPv6,
    QueryType,
    CAST(1 AS UInt32) AS Count
FROM dsv.QueryResponseShard
WHERE QueryResponseHasQuery;

---
--- Create distributed table for aggregated QtypeIpVersion counts.
---
CREATE TABLE dsv_five_minute.QtypeIpVersion
(
    Date Date,
    DateTime DateTime,
    NodeID UInt16,
    TransportIPv6 UInt8,
    QueryType UInt16,
    Count UInt32
)
ENGINE = Distributed(dsv, dsv_five_minute, QtypeIpVersionShard);

---
--- Create local shard aggregated QueryResponseTransport counts.
---
CREATE TABLE dsv_five_minute.QueryResponseTransportShard
(
    Date Date,
    DateTime DateTime,
    NodeID UInt16,
    TransportTCP UInt8,
    TransportIPv6 UInt8,
    QueryCount UInt32,
    ResponseCount UInt32
)
ENGINE = SummingMergeTree()
PARTITION BY toYearWeek(Date)
ORDER BY (Date, DateTime, NodeID, TransportTCP, TransportIPv6);

CREATE MATERIALIZED VIEW dsv_five_minute.QueryResponseTransportShardMV
TO dsv_five_minute.QueryResponseTransportShard
AS SELECT
    Date,
    toStartOfFiveMinute(DateTime) AS DateTime,
    NodeID,
    TransportTCP,
    TransportIPv6,
    CAST((QueryResponseHasQuery != 0) AS UInt32) AS QueryCount,
    CAST((QueryResponseHasResponse != 0) AS UInt32) AS ResponseCount
FROM dsv.QueryResponseShard;

---
--- Create distributed table for aggregated QueryResponseTransport counts.
---
CREATE TABLE dsv_five_minute.QueryResponseTransport
(
    Date Date,
    DateTime DateTime,
    NodeID UInt16,
    TransportTCP UInt8,
    TransportIPv6 UInt8,
    QueryCount UInt32,
    ResponseCount UInt32
)
ENGINE = Distributed(dsv, dsv_five_minute, QueryResponseTransportShard);

---
--- Create local shard aggregated ASN/QTYPE counts.
---
CREATE TABLE dsv_five_minute.AsnQtypeShard
(
    Date Date,
    DateTime DateTime,
    NodeID UInt16,
    ClientASN UInt32,
    QueryType UInt16,
    Count UInt32
)
ENGINE = SummingMergeTree()
PARTITION BY toYearWeek(Date)
ORDER BY (Date, DateTime, NodeID, ClientASN, QueryType);

CREATE MATERIALIZED VIEW dsv_five_minute.AsnQtypeShardMV
TO dsv_five_minute.AsnQtypeShard
AS SELECT
    Date,
    toStartOfFiveMinute(DateTime) AS DateTime,
    NodeID,
    ClientASN,
    QueryType,
    CAST(1 AS UInt32) AS Count
FROM dsv.QueryResponseShard
WHERE QueryResponseHasQuery AND ClientASN <> 0;

---
--- Create distributed table for aggregated QueryResponseTransport counts.
---
CREATE TABLE dsv_five_minute.AsnQtype
(
    Date Date,
    DateTime DateTime,
    NodeID UInt16,
    ClientASN UInt32,
    QueryType UInt16,
    Count UInt32
)
ENGINE = Distributed(dsv, dsv_five_minute, AsnQtypeShard);

---
--- Create local shard aggregated query/response length counts.
---
CREATE TABLE dsv_five_minute.QueryResponseLengthShard
(
    Date Date,
    DateTime DateTime,
    NodeID UInt16,
    TransportTCP UInt8,
    TransportIPv6 UInt8,
    QueryLengthMap Nested
    (
        Length UInt16,
        Count UInt32
    ),
    ResponseLengthMap Nested
    (
        Length UInt16,
        Count UInt32
    )
)
ENGINE = SummingMergeTree()
PARTITION BY toYearWeek(Date)
ORDER BY (Date, DateTime, NodeID, TransportTCP, TransportIPv6);

CREATE MATERIALIZED VIEW dsv_five_minute.QueryResponseLengthShardMV
TO dsv_five_minute.QueryResponseLengthShard
AS SELECT
    Date,
    toStartOfFiveMinute(DateTime) AS DateTime,
    NodeID,
    TransportTCP,
    TransportIPv6,
    [QueryLength] AS `QueryLengthMap.Length`,
    [CAST((QueryResponseHasQuery != 0) AS UInt32)] AS `QueryLengthMap.Count`,
    [ResponseLength] AS `ResponseLengthMap.Length`,
    [CAST((QueryResponseHasResponse != 0) AS UInt32)] AS `ResponseLengthMap.Count`
FROM dsv.QueryResponseShard;

---
--- Create distributed table for aggregated query/response length counts.
---
CREATE TABLE dsv_five_minute.QueryResponseLength
(
    Date Date,
    DateTime DateTime,
    NodeID UInt16,
    TransportTCP UInt8,
    TransportIPv6 UInt8,
    QueryLengthMap Nested
    (
        Length UInt16,
        Count UInt32
    ),
    ResponseLengthMap Nested
    (
        Length UInt16,
        Count UInt32
    )
)
ENGINE = Distributed(dsv, dsv_five_minute, QueryResponseLengthShard);

---
--- Create local shard aggregating unique IPv4 address counts.
---
CREATE TABLE dsv_five_minute.UniqueIPv4AddrShard
(
    Date Date,
    DateTime DateTime,
    NodeID UInt16,
    TransportTCP UInt8,
    IPv4Addr AggregateFunction(uniq, FixedString(16))
)
ENGINE = AggregatingMergeTree()
PARTITION BY toYearWeek(Date)
ORDER BY (Date, DateTime, NodeID, TransportTCP);

CREATE MATERIALIZED VIEW dsv_five_minute.UniqueIPv4AddrShardMV
TO dsv_five_minute.UniqueIPv4AddrShard
AS SELECT
    Date,
    toStartOfFiveMinute(DateTime) AS DateTime,
    NodeID,
    TransportTCP,
    uniqState(ClientAddress) AS IPv4Addr
FROM dsv.QueryResponseShard
WHERE not(TransportIPv6)
GROUP BY Date, DateTime, NodeID, TransportTCP;

---
--- Create distributed table for aggregated IPv4 address counts.
---
CREATE TABLE dsv_five_minute.UniqueIPv4Addr
(
    Date Date,
    DateTime DateTime,
    NodeID UInt16,
    TransportTCP UInt8,
    IPv4Addr AggregateFunction(uniq, FixedString(16))
)
ENGINE = Distributed(dsv, dsv_five_minute, UniqueIPv4AddrShard);

---
--- Create local shard aggregating unique IPv6 address counts.
---
CREATE TABLE dsv_five_minute.UniqueIPv6AddrShard
(
    Date Date,
    DateTime DateTime,
    NodeID UInt16,
    TransportTCP UInt8,
    IPv6Addr AggregateFunction(uniq, FixedString(16)),
    IPv664Addr AggregateFunction(uniq, String)
)
ENGINE = AggregatingMergeTree()
PARTITION BY toYearWeek(Date)
ORDER BY (Date, DateTime, NodeID, TransportTCP);

CREATE MATERIALIZED VIEW dsv_five_minute.UniqueIPv6AddrShardMV
TO dsv_five_minute.UniqueIPv6AddrShard
AS SELECT
    Date,
    toStartOfFiveMinute(DateTime) AS DateTime,
    NodeID,
    TransportTCP,
    uniqState(ClientAddress) AS IPv6Addr,
    uniqState(substring(ClientAddress, 1, 8)) AS IPv664Addr
FROM dsv.QueryResponseShard
WHERE TransportIPv6
GROUP BY Date, DateTime, NodeID, TransportTCP;

---
--- Create distributed table for aggregated IPv6 address counts.
---
CREATE TABLE dsv_five_minute.UniqueIPv6Addr
(
    Date Date,
    DateTime DateTime,
    NodeID UInt16,
    TransportTCP UInt8,
    IPv6Addr AggregateFunction(uniq, FixedString(16)),
    IPv664Addr AggregateFunction(uniq, String)
)
ENGINE = Distributed(dsv, dsv_five_minute, UniqueIPv6AddrShard);

---
--- Create local shard aggregating QTYPE/TLD counts for delegated TLDs.
---
CREATE TABLE dsv_five_minute.QtypeDelegatedTldShard
(
    Date Date,
    DateTime DateTime,
    NodeID UInt16,
    Tld String,
    QueryType UInt16,
    Count UInt32
)
ENGINE = SummingMergeTree()
PARTITION BY toYearWeek(Date)
ORDER BY (Date, DateTime, NodeID, Tld, QueryType);

CREATE MATERIALIZED VIEW dsv_five_minute.QtypeDelegatedTldShardMV
TO dsv_five_minute.QtypeDelegatedTldShard
AS SELECT
    Date,
    toStartOfFiveMinute(DateTime) AS DateTime,
    NodeID,
    lower(splitByChar('.', QueryName)[-1]) As Tld,
    QueryType,
    CAST(1 AS UInt32) AS Count
FROM dsv.QueryResponseShard
WHERE QueryResponseHasQuery
AND empty(Tld) OR Tld IN (SELECT name FROM dsv.tld_text);

---
--- Create distributed table for aggregated QTYPE/TLD counts.
---
CREATE TABLE dsv_five_minute.QtypeDelegatedTld
(
    Date Date,
    DateTime DateTime,
    NodeID UInt16,
    Tld String,
    QueryType UInt16,
    Count UInt32
)
ENGINE = Distributed(dsv, dsv_five_minute, QtypeDelegatedTldShard);

---
--- Create local shard aggregating QTYPE/TLD counts for top 40
--- undelegated TLDs.
---
CREATE TABLE dsv_five_minute.QtypeUndelegatedTldShard
(
    Date Date,
    DateTime DateTime,
    NodeID UInt16,
    Tld String,
    QueryType UInt16,
    Count UInt32
)
ENGINE = SummingMergeTree()
PARTITION BY toYearWeek(Date)
ORDER BY (Date, DateTime, NodeID, Tld, QueryType);

CREATE MATERIALIZED VIEW dsv_five_minute.QtypeUndelegatedTldShardMV
TO dsv_five_minute.QtypeUndelegatedTldShard
AS SELECT
    Date,
    toStartOfFiveMinute(DateTime) AS DateTime,
    NodeID,
    lower(topLevelDomain(QueryName)) As Tld,
    QueryType,
    CAST(1 AS UInt32) AS Count
FROM dsv.QueryResponseShard
INNER JOIN
(
    SELECT
        NodeID AS TopNID,
        topKMerge(40)(TopTlds) AS Tlds
    FROM dsv.AAATopUndelegatedTldPerFiveMinsShard
    WHERE (Date >= today() - 1) AND
          (DateTime >= subtractHours(now(), 1)) AND (DateTime <= now())
    GROUP BY TopNID
) AS TopNodes ON NodeID = TopNID
WHERE QueryResponseHasQuery
AND notEmpty(Tld)
AND has(Tlds, Tld);

---
--- Create distributed table for aggregated QTYPE/TLD counts.
---
CREATE TABLE dsv_five_minute.QtypeUndelegatedTld
(
    Date Date,
    DateTime DateTime,
    NodeID UInt16,
    Tld String,
    QueryType UInt16,
    Count UInt32
)
ENGINE = Distributed(dsv, dsv_five_minute, QtypeUndelegatedTldShard);

---
--- BGP prefix aggregation. We assume that the number of possible
--- subnets is bounded at a reasonable level, and accumulate exact
--- data.
---
CREATE TABLE dsv_five_minute.BGPPrefixShard
(
    Date Date,
    DateTime DateTime,
    NodeID UInt16,
    Prefix String,
    Count UInt32,
    RcodeMap Nested
    (
        ResponseRcode UInt16,
        Count UInt32
    )
)
ENGINE = SummingMergeTree()
PARTITION BY toYearWeek(Date)
ORDER BY (Date, DateTime, NodeID, Prefix);

CREATE MATERIALIZED VIEW dsv_five_minute.BGPPrefixShardMV
TO dsv_five_minute.BGPPrefixShard
AS SELECT
    Date,
    toStartOfFiveMinute(DateTime) AS DateTime,
    NodeID,
    concat(replaceRegexpOne(IPv6NumToString(IPv6CIDRToRange(ClientAddress, if(TransportIPv6, ClientASNetmask, toUInt8(96 + ClientASNetmask))).1), '^::ffff:', ''), '/', toString(ClientASNetmask)) AS Prefix,
    CAST(1 AS UInt32) AS Count,
    [if(QueryResponseHasResponse, ResponseRcode, 0)] AS `RcodeMap.ResponseRcode`,
    [CAST((QueryResponseHasResponse != 0) AS UInt32)] AS `RcodeMap.Count`
FROM dsv.QueryResponseShard
WHERE ClientASNetmask != 0;

---
--- Create distributed table for BGP prefix aggregation.
---
CREATE TABLE dsv_five_minute.BGPPrefix
(
    Date Date,
    DateTime DateTime,
    NodeID UInt16,
    Prefix String,
    Count UInt32,
    RcodeMap Nested
    (
        ResponseRcode UInt16,
        Count UInt32
    )
)
ENGINE = Distributed(dsv, dsv_five_minute, BGPPrefixShard);

---
--- Fixed sized client subnet aggregation. Subnets are /8 for IPv4
--- and /32 for IPv6. Includes counts for individual RCODEs.
---
CREATE TABLE dsv_five_minute.BusiestClientSubnetsShard
(
    Date Date,
    DateTime DateTime,
    NodeID UInt16,
    Prefix String,
    ClientASN UInt32,
    Count UInt32,
    RcodeMap Nested
    (
        ResponseRcode UInt16,
        Count UInt32
    )
)
ENGINE = SummingMergeTree()
PARTITION BY toYearWeek(Date)
ORDER BY (Date, DateTime, NodeID, Prefix, ClientASN);

CREATE MATERIALIZED VIEW dsv_five_minute.BusiestClientSubnetsShardMV
TO dsv_five_minute.BusiestClientSubnetsShard
AS SELECT
    Date,
    toStartOfFiveMinute(DateTime) AS DateTime,
    NodeID,
    concat(replaceRegexpOne(IPv6NumToString(IPv6CIDRToRange(ClientAddress, if(TransportIPv6, 32, 104)).1), '^::ffff:', ''), '/', toString(if(TransportIPv6, 32, 8))) AS Prefix,
    ClientASN,
    CAST(1 AS UInt32) AS Count,
    [if(QueryResponseHasResponse, ResponseRcode, 0)] AS `RcodeMap.ResponseRcode`,
    [CAST((QueryResponseHasResponse != 0) AS UInt32)] AS `RcodeMap.Count`
FROM dsv.QueryResponseShard;

---
--- Create distributed table for fixed sized client subnet aggregation.
---
CREATE TABLE dsv_five_minute.BusiestClientSubnets
(
    Date Date,
    DateTime DateTime,
    NodeID UInt16,
    Prefix String,
    ClientASN UInt32,
    Count UInt32,
    RcodeMap Nested
    (
        ResponseRcode UInt16,
        Count UInt32
    )
)
ENGINE = Distributed(dsv, dsv_five_minute, BusiestClientSubnetsShard);

---
--- Aggregation for tracking RCODE by Length.
---
CREATE TABLE dsv_five_minute.RcodeResponseLengthShard
(
    Date Date,
    DateTime DateTime,
    NodeID UInt16,
    Length UInt16,
    Rcode UInt16,
    Count UInt32
)
ENGINE = SummingMergeTree()
PARTITION BY toYearWeek(Date)
ORDER BY (Date, DateTime, NodeID, Length, Rcode)
SETTINGS index_granularity = 8192;

CREATE MATERIALIZED VIEW dsv_five_minute.RcodeResponseLengthShardMV
TO dsv_five_minute.RcodeResponseLengthShard
AS SELECT
    Date,
    toStartOfFiveMinute(DateTime) AS DateTime,
    NodeID,
    ResponseLength as Length,
    ResponseRcode as Rcode,
    CAST(1 AS UInt32) AS Count
FROM dsv.QueryResponseShard
WHERE QueryResponseHasResponse;

---
--- Create distributed table for tracking RCODE by length.
---
CREATE TABLE dsv_five_minute.RcodeResponseLength
(
    Date Date,
    DateTime DateTime,
    NodeID UInt16,
    Length UInt16,
    Rcode UInt16,
    Count UInt32
)
ENGINE = Distributed(dsv, dsv_five_minute, RcodeResponseLengthShard);

---
--- Count query/responses for individual locations.
---
CREATE TABLE dsv_five_minute.ClientGeoLocationsShard
(
    Date Date,
    DateTime DateTime,
    NodeID UInt16,
    ClientGeoLocation UInt32,
    Count UInt32
)
ENGINE = SummingMergeTree()
PARTITION BY toYearWeek(Date)
ORDER BY (Date, DateTime, NodeID, ClientGeoLocation)
SETTINGS index_granularity = 8192;

CREATE MATERIALIZED VIEW dsv_five_minute.ClientGeoLocationsShardMV
TO dsv_five_minute.ClientGeoLocationsShard
AS SELECT
    Date,
    toStartOfFiveMinute(DateTime) AS DateTime,
    NodeID,
    ClientGeoLocation,
    CAST(1 AS UInt32) AS Count
FROM dsv.QueryResponseShard;

---
--- Create distributed table of query/response counts for individual locations.
---
CREATE TABLE dsv_five_minute.ClientGeoLocations
(
    Date Date,
    DateTime DateTime,
    NodeID UInt16,
    ClientGeoLocation UInt32,
    Count UInt32
)
ENGINE = Distributed(dsv, dsv_five_minute, ClientGeoLocationsShard);

---
--- Aggregations for query classifications.
---
CREATE TABLE dsv_five_minute.QueryClassificationsShard
(
    Date Date,
    DateTime DateTime,
    NodeID UInt16,
    ASPrefix String,
    FixedPrefix String,
    ClientASN UInt32,
    Count UInt32,
    AForACount UInt32,
    AForRootCount UInt32,
    FunnyQueryClassCount UInt32,
    FunnyQueryTypeCount UInt32,
    LocalhostCount UInt32,
    NonAuthTldCount UInt32,
    RFC1918PtrCount UInt32,
    RootServersNetCount UInt32,
    SrcPortZeroCount UInt32,
    RootAbuseCount UInt32
)
ENGINE = SummingMergeTree()
PARTITION BY toYearWeek(Date)
ORDER BY (Date, DateTime, NodeID, ASPrefix, FixedPrefix, ClientASN)
SETTINGS index_granularity = 8192;

CREATE MATERIALIZED VIEW dsv_five_minute.QueryClassificationsShardMV
TO dsv_five_minute.QueryClassificationsShard
AS SELECT
    Date,
    toStartOfFiveMinute(DateTime) AS DateTime,
    NodeID,
    concat(replaceRegexpOne(IPv6NumToString(IPv6CIDRToRange(ClientAddress, if(TransportIPv6, ClientASNetmask, toUInt8(96 + ClientASNetmask))).1), '^::ffff:', ''), '/', toString(ClientASNetmask)) AS ASPrefix,
    concat(replaceRegexpOne(IPv6NumToString(IPv6CIDRToRange(ClientAddress, if(TransportIPv6, 32, 104)).1), '^::ffff:', ''), '/', toString(if(TransportIPv6, 32, 8))) AS FixedPrefix,
    ClientASN,
    CAST(1 AS UInt32) AS Count,
    CAST((QueryType == 1 AND IPv4StringToNum(QueryName) != 0) AS UInt32) AS AForACount,
    CAST((QueryType == 1 AND empty(QueryName)) AS UInt32) AS AForRootCount,
    CAST(QueryClass NOT IN (
        SELECT toUInt16(value) FROM dsv.iana_text
        WHERE registry_name == 'CLASS' AND
              value_name NOT IN ('Reserved', 'Unassigned')) AS UInt32) AS FunnyQueryClassCount,
    CAST(QueryType NOT IN (
        SELECT toUInt16(value) FROM dsv.iana_text
        WHERE registry_name == 'QTYPE' AND
              value_name NOT IN ('Reserved', 'Unassigned')) AS UInt32) AS FunnyQueryTypeCount,
    CAST(lower(substring(QueryName, length(QueryName) - 9 + 1, 9)) == 'localhost' AS UInt32) AS LocalhostCount,
    CAST(lower(splitByChar('.', QueryName)[-1]) NOT IN (SELECT name FROM dsv.tld_text) AS UInt32) AS NonAuthTldCount,
    CAST(QueryType == 12 AND match(QueryName, '^([0-9]\.)*(10|168\.192|(1[6-9]|2[0-9]|3[01])\.172)\.in-addr\.arpa$') AS UInt32) AS RFC1918PtrCount,
    CAST(lower(substring(QueryName, length(QueryName) - 16 + 1, 16)) == 'root-servers.net' AS UInt32) AS RootServersNetCount,
    CAST(ClientPort == 0 AS UInt32) AS SrcPortZeroCount,
    CAST(QueryType IN (28, 38) AND lower(substring(QueryName, length(QueryName) - 16 + 1, 16)) == 'root-servers.net' AS UInt32) AS RootAbuseCount
FROM dsv.QueryResponseShard;

---
--- Create distributed table for query classifications.
---
CREATE TABLE dsv_five_minute.QueryClassifications
(
    Date Date,
    DateTime DateTime,
    NodeID UInt16,
    ASPrefix String,
    FixedPrefix String,
    ClientASN UInt32,
    Count UInt32,
    AForACount UInt32,
    AForRootCount UInt32,
    FunnyQueryClassCount UInt32,
    FunnyQueryTypeCount UInt32,
    LocalhostCount UInt32,
    NonAuthTldCount UInt32,
    RFC1918PtrCount UInt32,
    RootServersNetCount UInt32,
    SrcPortZeroCount UInt32,
    RootAbuseCount UInt32
)
ENGINE = Distributed(dsv, dsv_five_minute, QueryClassificationsShard);

---
--- Aggregation for tracking EDNS queries.
---
--- The aggregation needs to track the number of non-EDNS queries.
---
CREATE TABLE dsv_five_minute.EDNSQueriesShard
(
    Date Date,
    DateTime DateTime,
    NodeID UInt16,
    EDNSQueryCount UInt32,
    NonEDNSQueryCount UInt32,
    EDNSQueryMap Nested
    (
        EDNSVersion UInt8,
        EDNSCount UInt32
    )
)
ENGINE = SummingMergeTree()
PARTITION BY toYearWeek(Date)
ORDER BY (Date, DateTime, NodeID)
SETTINGS index_granularity = 8192;

CREATE MATERIALIZED VIEW dsv_five_minute.EDNSQueriesShardMV
TO dsv_five_minute.EDNSQueriesShard
AS SELECT
    Date,
    toStartOfFiveMinute(DateTime) AS DateTime,
    NodeID,
    CAST(QueryResponseQueryHasOpt AS UInt32) AS EDNSQueryCount,
    CAST(NOT QueryResponseQueryHasOpt AS UInt32) AS NonEDNSQueryCount,
    [QueryEDNSVersion] AS `EDNSQueryMap.EDNSVersion`,
    [CAST(QueryResponseQueryHasOpt AS UInt32)] AS `EDNSQueryMap.EDNSCount`
FROM dsv.QueryResponseShard
WHERE QueryResponseHasQuery AND QueryResponseQueryHasOpt;

---
--- Create distributed table for EDNS queries.
---
CREATE TABLE dsv_five_minute.EDNSQueries
(
    Date Date,
    DateTime DateTime,
    NodeID UInt16,
    EDNSQueryCount UInt32,
    NonEDNSQueryCount UInt32,
    EDNSQueryMap Nested
    (
        EDNSVersion UInt8,
        EDNSCount UInt32
    )
)
ENGINE = Distributed(dsv, dsv_five_minute, EDNSQueriesShard);

---
--- Aggregation for tracking CHAOS queries.
---
--- The aggregation needs to track QTYPE for each query.
---
CREATE TABLE dsv_five_minute.CHQueriesShard
(
    Date Date,
    DateTime DateTime,
    NodeID UInt16,
    CHQType UInt16,
    CHQName String,
    CHCount UInt32
)
ENGINE = SummingMergeTree()
PARTITION BY toYearWeek(Date)
ORDER BY (Date, DateTime, NodeID, CHQType, CHQName)
SETTINGS index_granularity = 8192;

CREATE MATERIALIZED VIEW dsv_five_minute.CHQueriesShardMV
TO dsv_five_minute.CHQueriesShard
AS SELECT
    Date,
    toStartOfFiveMinute(DateTime) AS DateTime,
    NodeID,
    QueryType AS CHQType,
    lower(QueryName) AS CHQName,
    CAST(1 AS UInt32) AS CHCount
FROM dsv.QueryResponseShard
WHERE QueryResponseHasQuery and QueryClass=3;

---
--- Create distributed table for CHAOS queries.
---
CREATE TABLE dsv_five_minute.CHQueries
(
    Date Date,
    DateTime DateTime,
    NodeID UInt16,
    CHQType UInt16,
    CHQName String,
    CHCount UInt32
)
ENGINE = Distributed(dsv, dsv_five_minute, CHQueriesShard);
