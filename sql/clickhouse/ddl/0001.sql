--- Copyright 2021 Internet Corporation for Assigned Names and Numbers.
---
--- This Source Code Form is subject to the terms of the Mozilla Public
--- License, v. 2.0. If a copy of the MPL was not distributed with this
--- file, you can obtain one at https://mozilla.org/MPL/2.0/.
---
--- Developed by Sinodun IT (sinodun.com)
---
--- Create raw data tables.
---

---
--- Raw Query/Response data table shard.
---
CREATE TABLE dsv.QueryResponseShard
(
    Date Date,
    DateTime DateTime,
    NanoSecondsSinceEpoch UInt64,
    NodeID UInt16,
    ClientAddress FixedString(16),
    ClientPort UInt16,
    ClientHoplimit UInt8,
    ClientGeoLocation UInt32,
    ClientASN UInt32,
    ClientASNetmask UInt8,
    ServerAddress FixedString(16),
    ServerPort UInt16,
    TransportTCP UInt8,
    TransportIPv6 UInt8,
    QueryResponseHasQuery UInt8,
    QueryResponseHasResponse UInt8,
    QueryResponseQueryHasQuestion UInt8,
    QueryResponseQueryHasOpt UInt8,
    QueryResponseResponseHasQuestion UInt8,
    QueryResponseResponseHasOpt UInt8,
    QueryLength UInt16,
    ResponseLength UInt16,
    ID UInt16,
    QueryOpcode UInt8,
    QueryCheckingDisabled UInt8,
    QueryAuthenticatedData UInt8,
    QueryZ UInt8,
    QueryRecursionAvailable UInt8,
    QueryRecursionDesired UInt8,
    QueryTruncated UInt8,
    QueryAuthoritativeAnswer UInt8,
    QueryDO UInt8,
    QueryRcode UInt16,
    QueryClass UInt16,
    QueryType UInt16,
    QueryName String,
    QueryQDCount UInt16,
    QueryANCount UInt16,
    QueryARCount UInt16,
    QueryNSCount UInt16,
    QueryEDNSVersion UInt8,
    QueryEDNSUDPMessageSize UInt16,
    ResponseDelayNanoSeconds Int64,
    ResponseCheckingDisabled UInt8,
    ResponseAuthenticatedData UInt8,
    ResponseZ UInt8,
    ResponseRecursionAvailable UInt8,
    ResponseRecursionDesired UInt8,
    ResponseTruncated UInt8,
    ResponseAuthoritativeAnswer UInt8,
    ResponseRcode UInt16,
    ResponseQDCount UInt16,
    ResponseANCount UInt16,
    ResponseARCount UInt16,
    ResponseNSCount UInt16
)
ENGINE = MergeTree()
PARTITION BY toYearWeek(Date)
ORDER BY (Date, DateTime, NanoSecondsSinceEpoch, NodeID, xxHash64(ClientAddress))
SAMPLE BY xxHash64(ClientAddress);

---
--- Create distributed table for raw Query/Response data.
---
CREATE TABLE dsv.QueryResponse
(
    Date Date,
    DateTime DateTime,
    NanoSecondsSinceEpoch UInt64,
    NodeID UInt16,
    ClientAddress FixedString(16),
    ClientPort UInt16,
    ClientHoplimit UInt8,
    ClientGeoLocation UInt32,
    ClientASN UInt32,
    ClientASNetmask UInt8,
    ServerAddress FixedString(16),
    ServerPort UInt16,
    TransportTCP UInt8,
    TransportIPv6 UInt8,
    QueryResponseHasQuery UInt8,
    QueryResponseHasResponse UInt8,
    QueryResponseQueryHasQuestion UInt8,
    QueryResponseQueryHasOpt UInt8,
    QueryResponseResponseHasQuestion UInt8,
    QueryResponseResponseHasOpt UInt8,
    QueryLength UInt16,
    ResponseLength UInt16,
    ID UInt16,
    QueryOpcode UInt8,
    QueryCheckingDisabled UInt8,
    QueryAuthenticatedData UInt8,
    QueryZ UInt8,
    QueryRecursionAvailable UInt8,
    QueryRecursionDesired UInt8,
    QueryTruncated UInt8,
    QueryAuthoritativeAnswer UInt8,
    QueryDO UInt8,
    QueryRcode UInt16,
    QueryClass UInt16,
    QueryType UInt16,
    QueryName String,
    QueryQDCount UInt16,
    QueryANCount UInt16,
    QueryARCount UInt16,
    QueryNSCount UInt16,
    QueryEDNSVersion UInt8,
    QueryEDNSUDPMessageSize UInt16,
    ResponseDelayNanoSeconds Int64,
    ResponseCheckingDisabled UInt8,
    ResponseAuthenticatedData UInt8,
    ResponseZ UInt8,
    ResponseRecursionAvailable UInt8,
    ResponseRecursionDesired UInt8,
    ResponseTruncated UInt8,
    ResponseAuthoritativeAnswer UInt8,
    ResponseRcode UInt16,
    ResponseQDCount UInt16,
    ResponseANCount UInt16,
    ResponseARCount UInt16,
    ResponseNSCount UInt16
)
ENGINE = Distributed(dsv, dsv, QueryResponseShard, rand());

---
--- Zone latency data table.
---
--- Since zone updates are relatively infrequent, we don't
--- worry about time resolutions of less than a second.
---
CREATE TABLE dsv.ZoneLatencyShard
(
    Date Date,
    DateTime DateTime,
    NodeID UInt16,
    Zone String,
    Serial UInt32,
    Latency UInt32,
    PercentNodesUpdated UInt8
)
ENGINE = MergeTree()
PARTITION BY toYearWeek(Date)
ORDER BY (Date, DateTime, NodeID);

---
--- Create distributed table for zone latency data.
---
CREATE TABLE dsv.ZoneLatency
(
    Date Date,
    DateTime DateTime,
    NodeID UInt16,
    Zone String,
    Serial UInt32,
    Latency UInt32,
    PercentNodesUpdated UInt8
)
ENGINE = Distributed(dsv, dsv, ZoneLatencyShard, rand());

---
--- Raw table for packet counts.
--- (These tables are not currently graphed but are required for the import to work correctly)
---
CREATE TABLE dsv.PacketCountsShard
(
    Date Date,
    DateTime DateTime,
    NodeID UInt16,
    Duration UInt32 DEFAULT 300,
    RawPackets UInt64,
    MalformedPackets UInt64,
    NonDNSPackets UInt64
)
ENGINE = MergeTree()
PARTITION BY toYearWeek(Date)
ORDER BY (Date, DateTime, NodeID);

---
--- Create distributed table for packet count data.
--- (These tables are not currently graphed but are required for the import to work correctly)
---
CREATE TABLE dsv.PacketCounts
(
    Date Date,
    DateTime DateTime,
    NodeID UInt16,
    Duration UInt32 DEFAULT 300,
    RawPackets UInt64,
    MalformedPackets UInt64,
    NonDNSPackets UInt64
)
ENGINE = Distributed(dsv, dsv, PacketCountsShard, rand());

---
--- Table tracking import queue sizes.
--- (These tables are not currently graphed but are required for queue size monitoring)
---
CREATE TABLE dsv.ImportQueueSizesShard
(
    Date Date,
    DateTime DateTime,
    NodeID UInt16,
    CDNSIncoming UInt32,
    CDNStoTSVPending UInt32,
    TSVImportPending UInt32,
    CDNStoPCAPPending UInt32,
    CDNStoTSVErrors UInt32,
    TSVImportErrors UInt32,
    CDNStoPCAPErrors UInt32
)
ENGINE = MergeTree()
PARTITION BY toYearWeek(Date)
ORDER BY (Date, DateTime, NodeID);

---
--- Create distributed table for import queue sizes.
--- (These tables are not currently graphed but are required for queue size monitoring)
---
CREATE TABLE dsv.ImportQueueSizes
(
    Date Date,
    DateTime DateTime,
    NodeID UInt16,
    CDNSIncoming UInt32,
    CDNStoTSVPending UInt32,
    TSVImportPending UInt32,
    CDNStoPCAPPending UInt32,
    CDNStoTSVErrors UInt32,
    TSVImportErrors UInt32,
    CDNStoPCAPErrors UInt32
)
ENGINE = Distributed(dsv, dsv, ImportQueueSizesShard, rand());
