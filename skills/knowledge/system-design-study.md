---
name: system-design-study
description: Use when preparing for system design interviews, learning distributed systems fundamentals, or designing scalable architecture for large-scale applications.
---

# System Design Study

## Overview
System design requires reasoning about trade-offs between performance, scalability, reliability, and cost. There are no perfect designs — only justified trade-offs.

## When to Use
- Preparing for FAANG/Big Tech system design interviews
- Designing a new distributed system or service
- Learning CAP theorem, consistency models, or scaling patterns
- Reviewing architecture decisions

## The Trade-Off Framework

### Core Trade-Offs
| Dimension A | vs | Dimension B | Key Question |
|-------------|---|-------------|-------------|
| Performance | vs | Scalability | Does it stay fast as load grows? |
| Latency | vs | Throughput | Few fast requests or many total? |
| Availability | vs | Consistency | CAP theorem — pick two of three |
| SQL | vs | NoSQL | Schema flexibility vs ACID guarantees |

### CAP Theorem
In a distributed system, you can guarantee at most **two** of:
- **C**onsistency — every read gets latest write
- **A**vailability — every request gets a response
- **P**artition Tolerance — system works despite network splits

In practice: partition tolerance is mandatory → choose C or A.

## Building Blocks

### Scaling Reads
```
Client → Load Balancer → App Servers → Cache (Redis) → DB
                                          ↓ (miss)
                                        Database
```
- **Horizontal scaling**: add more servers behind load balancer
- **Caching**: Redis/Memcached for hot data (cache-aside pattern)
- **CDN**: static assets and geographically distributed content
- **Read replicas**: scale read queries independently

### Scaling Writes
- **Database sharding**: partition data by key (user_id % N)
- **Write-ahead log**: durability before acknowledgment
- **Message queues**: Kafka/RabbitMQ for async processing

### Reliability
- **Replication**: master-replica or multi-master
- **Health checks**: load balancer routes around failed nodes
- **Circuit breaker**: fail fast to prevent cascade failures
- **Rate limiting**: token bucket or leaky bucket algorithm

## Interview Formula (45 min)
1. **Clarify** (5 min) — functional + non-functional requirements, scale estimates
2. **High-level design** (10 min) — boxes and arrows, major components
3. **Deep dive** (20 min) — data model, APIs, bottlenecks, scaling
4. **Trade-offs** (10 min) — what you'd do differently, what you sacrificed

## Classic Problems to Master
| Problem | Key Concepts |
|---------|-------------|
| URL Shortener (Pastebin) | Hashing, KV store, redirection |
| Twitter Timeline | Fan-out on write vs read, caching |
| Web Crawler | BFS, deduplication, politeness |
| Chat System | WebSockets, message delivery guarantees |
| Rate Limiter | Token bucket, sliding window, Redis |
| Design YouTube | Video encoding, CDN, chunked upload |

## Study Tools
- Anki flashcard decks available in the repo for spaced repetition
- Diagrams for every major concept

## Reference
Source: [donnemartin/system-design-primer](https://github.com/donnemartin/system-design-primer)
