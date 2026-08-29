# Threat Cache & Persistence Layer

## Architecture
- `models.py`: CacheRecord, CacheRevision
- `storage.py`: InMemoryStorage + PersistentStorage
- `manager.py`: CRUD, TTL, eviction, revisions
- `repository.py`: Indexed queries
- `eviction.py`: LRU / TTL policies
- `cleanup.py`: Expired removal, revision pruning, compaction
- `serializer.py`: JSON / export-import
- `statistics.py`: Hit ratio, size, provider distribution

## Cache Record
Contains cache_id, ioc_id, ioc_type, original/normalized value, provider, threat_status, score, confidence, evidence, first_seen, last_updated, expiration, TTL, lookup counts, revision, status.

## Operations
Create, Read, Update, Delete, Bulk, Lookup by IOC/Type/Provider/Score/Confidence/Date

## Versioning
Each update creates CacheRevision with revision number, timestamp, reason, provider.

## API
GET /api/v2/threat/cache
GET /api/v2/threat/cache/{ioc}
DELETE /api/v2/threat/cache/{ioc}
POST /api/v2/threat/cache/refresh
GET /api/v2/threat/cache/statistics

## Configuration
max_size, default_ttl, cleanup interval, persistence path.

## Monitoring
Hit ratio, miss ratio, latency, evictions, storage usage.
