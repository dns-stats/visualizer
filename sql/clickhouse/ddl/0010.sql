--- Copyright 2021 Internet Corporation for Assigned Names and Numbers.
---
--- This Source Code Form is subject to the terms of the Mozilla Public
--- License, v. 2.0. If a copy of the MPL was not distributed with this
--- file, you can obtain one at https://mozilla.org/MPL/2.0/.
---
--- Developed by Sinodun IT (sinodun.com)
---
--- Create supporting tables for aggregations.
---
--- These are tables that are not directly part of the aggregation,
--- but data from which is used when building an aggregation table.
---

---
--- Create local shard aggregating top 40 undelegated TLDs.
--- This is just used for tracking the most popular TLDs, to determine
--- whether a particular TLD should be added to
--- QtypeUndelegatedTldShard. When making that decision, we
--- consider only the last hour at 5 minute granularity, to ensure
--- that temporary bursts of popularity fade from view.
---
--- It appears that additions to materialized views are done in
--- alphabetical order. So put this first, so that aggregating
--- into the main data table proper based on the the contents of this
--- table happens after this table is updated.
---
--- NOTE. I tried calculating TLD in a subquery and using that value
---       instead of repeating the QueryName modification. But I found
---       that in some ClickHouse versions the select
---       works fine on its own, but as the AS clause in a CREATE
---       MATERIALIZED VIEW it errors.
---       I suspect ClickHouse has problems with subqueries in this context.
---
CREATE TABLE dsv.AAATopUndelegatedTldPerFiveMinsShard
(
    Date Date,
    DateTime DateTime,
    NodeID UInt16,
    TopTlds AggregateFunction(topK(40), String)
)
ENGINE = AggregatingMergeTree()
PARTITION BY toYearWeek(Date)
ORDER BY (Date, DateTime, NodeID);

CREATE MATERIALIZED VIEW dsv.AAATopUndelegatedTldPerFiveMinsShardMV
TO dsv.AAATopUndelegatedTldPerFiveMinsShard
AS SELECT
    today() AS Date,
    toStartOfFiveMinute(now()) AS DateTime,
    NodeID,
    topKState(40)(lower(topLevelDomain(QueryName))) AS TopTlds
FROM dsv.QueryResponseShard
WHERE QueryResponseHasQuery
AND notEmpty(lower(topLevelDomain(QueryName)))
AND lower(topLevelDomain(QueryName)) NOT IN (SELECT name FROM dsv.tld_text)
GROUP BY Date, DateTime, NodeID;

---
--- Create distributed table for aggregated top 40 undelegated TLDs.
---
CREATE TABLE dsv.AAATopUndelegatedTldPerFiveMins
(
    Date Date,
    DateTime DateTime,
    NodeID UInt16,
    TopTlds AggregateFunction(topK(40), String)
)
ENGINE = Distributed(dsv, dsv, AAATopUndelegatedTldPerFiveMinsShard);
