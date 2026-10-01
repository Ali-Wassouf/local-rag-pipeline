# Phase 4 eval — hybrid (vector + keyword RRF), no reranking

Same 20 questions as evals/baseline.md, same project (Systems Books, real ~600-page DDIA book), re-run against this configuration only, per docs/build-phases.md Phase 4's requirement to measure hybrid-vs-vector and reranked-vs-unreranked *separately*.

---

## 1. What is a log-structured storage engine?

A **log-structured storage engine** is a type of storage system that organizes data in a way that emphasizes sequential writes to disk, often using a log-like structure to manage data. Key characteristics and mechanisms include:

1. **Sequential Writes**: Unlike page-oriented systems (e.g., B-trees), log-structured engines append data to a log (or "memtable") and periodically flush it to disk as sorted SSTables (Sorted Table Files). This reduces the overhead of random disk writes, enabling higher write throughput [3][7].

2. **Compaction and Merging**: Over time, the system merges and compacts SSTables to eliminate redundant data and optimize storage. This process, called **compaction**, can involve strategies like size-tiered or leveled compaction, which balance write amplification (multiple disk writes per data update) and disk space usage [5][7].

3. **Write Amplification**: Due to repeated compaction and merging, log-structured engines may generate more disk I/O than the original data size. This is particularly impactful on SSDs, which have limited write endurance [5][7].

4. **Use Cases**: These engines excel in write-heavy workloads (e.g., databases like Cassandra, HBase, and LevelDB) where sequential writes outperform random writes. However, they may lag in read performance compared to B-trees for certain queries [3][5].

5. **Comparison to B-Trees**: While B-trees are update-in-place and support efficient range queries, log-structured engines trade predictability for higher write throughput. They are less suitable for applications requiring frequent updates to the same keys but shine in scenarios with high insertion rates [3][5][7].

For example, the `db_set` and `db_get` functions in [1] illustrate a simplistic log-structured approach, but real-world implementations (e.g., LevelDB, RocksDB) use advanced mechanisms like memtables, SSTables, and background compaction to manage scalability and performance [7].

**Sources (8):**
- [1] Designing Data Intensive Applications by Martin Kleppmann — Part I. Foundations of Data Systems > Chapter 3. Storage and Retrieval > Data Structures That Power Your Database
- [2] Designing Data Intensive Applications by Martin Kleppmann — Part I. Foundations of Data Systems > Chapter 3. Storage and Retrieval > Data Structures That Power Your Database > Other Indexing Structures
- [3] Designing Data Intensive Applications by Martin Kleppmann — Part I. Foundations of Data Systems > Chapter 3. Storage and Retrieval > Data Structures That Power Your Database > B-Trees
- [4] Designing Data Intensive Applications by Martin Kleppmann — Part I. Foundations of Data Systems > Chapter 3. Storage and Retrieval > Summary
- [5] Designing Data Intensive Applications by Martin Kleppmann — Part I. Foundations of Data Systems > Chapter 3. Storage and Retrieval > Data Structures That Power Your Database > Comparing B-Trees and LSM-Trees
- [6] Designing Data Intensive Applications by Martin Kleppmann — Part III. Derived Data > Chapter 11. Stream Processing > Databases and Streams > Change Data Capture
- [7] Designing Data Intensive Applications by Martin Kleppmann — Part I. Foundations of Data Systems > Chapter 3. Storage and Retrieval > Data Structures That Power Your Database > SSTables and LSM-Trees
- [8] Designing Data Intensive Applications by Martin Kleppmann — Part I. Foundations of Data Systems > Chapter 3. Storage and Retrieval > Summary

---

## 2. What is the difference between a B-tree and an LSM-tree?

The differences between B-trees and LSM-trees lie in their design, performance characteristics, and use cases. Here's a structured comparison:

1. **Write vs. Read Performance**:  
   - **B-trees** are generally faster for **reads** because they allow direct access to data via hierarchical indexing. However, writes involve overwriting pages, which can be slower due to random I/O [1].  
   - **LSM-trees** excel at **writes** due to sequential disk I/O during compaction, which reduces write amplification (multiple disk writes per database write). Reads are slower because they require checking multiple SSTables and compaction stages [1].  

2. **Compaction and Write Amplification**:  
   - LSM-trees **rewrite data during compaction**, merging sorted SSTables into larger files. This process can cause **write amplification** (e.g., SSDs have limited overwrite cycles), but it enables sequential writes and higher throughput [3].  
   - B-trees avoid compaction but require **overwriting pages** during updates, which introduces overhead and fragmentation [4].  

3. **Disk I/O Patterns**:  
   - LSM-trees prioritize **sequential writes** (e.g., merging SSTables), which is faster on magnetic drives and SSDs (via firmware log-structured optimizations) [3].  
   - B-trees rely on **random writes** for updates, which are slower on traditional disks [4].  

4. **Storage Efficiency**:  
   - LSM-trees can **compress data better** and reduce fragmentation by periodically rewriting SSTables, leading to smaller disk usage [3].  
   - B-trees leave unused space in pages due to fragmentation, increasing storage overhead [1].  

5. **Use Cases**:  
   - **B-trees** are ideal for **read-heavy workloads** (e.g., OLTP systems) where fast lookups are critical [5].  
   - **LSM-trees** are preferred for **write-heavy applications** (e.g., OLAP systems) and scenarios requiring high write throughput [3].  

In summary, B-trees prioritize read efficiency and simplicity, while LSM-trees optimize for write throughput and scalability, albeit with trade-offs in read performance and storage complexity [1][3][4].

**Sources (8):**
- [1] Designing Data Intensive Applications by Martin Kleppmann — Part I. Foundations of Data Systems > Chapter 3. Storage and Retrieval > Data Structures That Power Your Database > Comparing B-Trees and LSM-Trees
- [2] Designing Data Intensive Applications by Martin Kleppmann — Part I. Foundations of Data Systems > Chapter 3. Storage and Retrieval > Data Structures That Power Your Database > B-Trees
- [3] Designing Data Intensive Applications by Martin Kleppmann — Part I. Foundations of Data Systems > Chapter 3. Storage and Retrieval > Data Structures That Power Your Database > Comparing B-Trees and LSM-Trees
- [4] Designing Data Intensive Applications by Martin Kleppmann — Part I. Foundations of Data Systems > Chapter 3. Storage and Retrieval > Data Structures That Power Your Database > B-Trees
- [5] Designing Data Intensive Applications by Martin Kleppmann — Part I. Foundations of Data Systems > Chapter 3. Storage and Retrieval > Summary
- [6] Designing Data Intensive Applications by Martin Kleppmann — Part I. Foundations of Data Systems > Chapter 3. Storage and Retrieval > Column-Oriented Storage > Aggregation: Data Cubes and Materialized Views
- [7] Designing Data Intensive Applications by Martin Kleppmann — Part I. Foundations of Data Systems > Chapter 3. Storage and Retrieval > Summary
- [8] Designing Data Intensive Applications by Martin Kleppmann — Part I. Foundations of Data Systems > Chapter 3. Storage and Retrieval > Data Structures That Power Your Database > SSTables and LSM-Trees

---

## 3. What does ACID stand for in the context of databases?

ACID stands for **Atomicity, Consistency, Isolation, and Durability** in the context of databases. These properties define the characteristics of reliable transaction processing in database systems [1]. 

- **Atomicity** ensures that transactions are treated as a single, indivisible unit of work [1].  
- **Consistency** guarantees that a transaction leaves the database in a valid state, adhering to defined invariants [1].  
- **Isolation** ensures that concurrent transactions do not interfere with each other, maintaining the illusion of serial execution [1].  
- **Durability** ensures that once a transaction is committed, its changes persist even in the event of system failures [1].  

This acronym was coined in 1983 by Theo Härder and Andreas Reuter to establish precise terminology for fault-tolerance mechanisms in databases [1]. While the term "ACID" is often used as a marketing label today, its foundational principles remain central to transactional guarantees [1].  

References:  
[1] Part II. Distributed Data > Chapter 7. Transactions > The Meaning of ACID  
[6] Part II. Distributed Data > Chapter 7. Transactions > The Slippery Concept of a Transaction > The Meaning of ACID

**Sources (8):**
- [1] Designing Data Intensive Applications by Martin Kleppmann — Part II. Distributed Data > Chapter 7. Transactions > The Slippery Concept of a Transaction > The Meaning of ACID
- [2] Designing Data Intensive Applications by Martin Kleppmann — Part II. Distributed Data > Chapter 7. Transactions > Summary
- [3] Designing Data Intensive Applications by Martin Kleppmann — Part II. Distributed Data > Chapter 7. Transactions > The Slippery Concept of a Transaction > The Meaning of ACID
- [4] Designing Data Intensive Applications by Martin Kleppmann — Index
- [5] Designing Data Intensive Applications by Martin Kleppmann — Part I. Foundations of Data Systems > Chapter 3. Storage and Retrieval > Transaction Processing or Analytics?
- [6] Designing Data Intensive Applications by Martin Kleppmann — Part II. Distributed Data > Chapter 7. Transactions > The Slippery Concept of a Transaction > The Meaning of ACID
- [7] Designing Data Intensive Applications by Martin Kleppmann — Index
- [8] Designing Data Intensive Applications by Martin Kleppmann — Index

---

## 4. What is eventual consistency?

Eventual consistency is a consistency model in distributed systems where, after a sufficient amount of time passes without further writes, all replicas will eventually agree on the same value. However, during the time before convergence, reads may return outdated or inconsistent results [1]. This model is commonly used in systems with asynchronous replication, where followers may lag behind the leader, leading to temporary inconsistencies until the replicas catch up [2]. 

Key characteristics include:
1. **Temporary Inconsistencies**: Reads may not reflect the latest writes immediately, especially if the read is directed to a stale replica [1].
2. **No Guarantee on Convergence Time**: The model does not specify how long it will take for replicas to converge, making it a "weak" guarantee [3].
3. **Conflict Resolution**: Systems often use mechanisms like "last write wins" (LWW) to resolve conflicts, though this can lead to data loss if not handled carefully [5].

This model is contrasted with stronger guarantees like linearizability, which ensures reads always reflect the most recent writes [4]. Eventual consistency is practical for scalability but requires applications to account for its limitations, such as implementing read-after-write consistency to avoid user-facing issues [2].

**Sources (8):**
- [1] Designing Data Intensive Applications by Martin Kleppmann — Part II. Distributed Data > Chapter 9. Consistency and Consensus > Consistency Guarantees
- [2] Designing Data Intensive Applications by Martin Kleppmann — Part II. Distributed Data > Chapter 5. Replication > Problems with Replication Lag > Reading Your Own Writes
- [3] Designing Data Intensive Applications by Martin Kleppmann — Part II. Distributed Data > Chapter 9. Consistency and Consensus > Consistency Guarantees
- [4] Designing Data Intensive Applications by Martin Kleppmann — Part II. Distributed Data > Chapter 9. Consistency and Consensus > Linearizability
- [5] Designing Data Intensive Applications by Martin Kleppmann — Part II. Distributed Data > Chapter 5. Replication > Leaderless Replication > Detecting Concurrent Writes
- [6] Designing Data Intensive Applications by Martin Kleppmann — Part II. Distributed Data > Chapter 8. The Trouble with Distributed Systems > Summary
- [7] Designing Data Intensive Applications by Martin Kleppmann — Index
- [8] Designing Data Intensive Applications by Martin Kleppmann — Part II. Distributed Data > Chapter 5. Replication > Problems with Replication Lag > Solutions for Replication Lag

---

## 5. What is the CAP theorem?

The CAP theorem, introduced by Eric Brewer in 2000, addresses the trade-offs in distributed systems when dealing with **consistency (linearizability)**, **availability**, and **partition tolerance** [1][2][3]. Here's a concise summary:

1. **Core Trade-off**:  
   - In the event of a **network partition** (a type of fault), a system must choose between **consistency** (linearizability) and **availability**. It cannot guarantee both simultaneously [1][3].  
   - This is often summarized as **CP (Consistent and Partition-tolerant)** or **AP (Available and Partition-tolerant)**, but this framing is criticized for oversimplifying the problem [3][9].

2. **Key Limitations of CAP**:  
   - The theorem’s original formulation is **vague** and lacks precise definitions, leading to misunderstandings [3][9].  
   - It focuses narrowly on **linearizability** (a strict consistency model) and **network partitions**, ignoring other factors like **network delays**, **dead nodes**, or alternative consistency models [3][40].  
   - Modern research has shown more nuanced and precise results, rendering CAP less relevant for practical system design [3][42].

3. **Practical Implications**:  
   - Systems prioritizing **linearizability** (e.g., CP) may become unavailable during partitions, while those prioritizing **availability** (e.g., AP) may sacrifice consistency [1][3].  
   - Many "highly available" systems do not strictly adhere to CAP’s definitions, highlighting its limited utility in real-world scenarios [3][40].

4. **Historical Context**:  
   - CAP sparked discussions about distributed systems design but is now considered **historical** due to more accurate theoretical frameworks [3][41].  

In short, the CAP theorem highlights a fundamental trade-off in distributed systems but is best understood as a conceptual starting point rather than a strict rule [1][3][9].

**Sources (8):**
- [1] Designing Data Intensive Applications by Martin Kleppmann — Part II. Distributed Data > Chapter 9. Consistency and Consensus > Linearizability > The Cost of Linearizability
- [2] Designing Data Intensive Applications by Martin Kleppmann — Glossary
- [3] Designing Data Intensive Applications by Martin Kleppmann — Part II. Distributed Data > Chapter 9. Consistency and Consensus > Linearizability > The Cost of Linearizability
- [4] Designing Data Intensive Applications by Martin Kleppmann — Part II. Distributed Data > Chapter 9. Consistency and Consensus > Summary
- [5] Designing Data Intensive Applications by Martin Kleppmann — Part II. Distributed Data > Chapter 9. Consistency and Consensus > Summary
- [6] Designing Data Intensive Applications by Martin Kleppmann — Part II. Distributed Data > Chapter 7. Transactions > Summary
- [7] Designing Data Intensive Applications by Martin Kleppmann — Part III. Derived Data > Chapter 10. Batch Processing > Summary
- [8] Designing Data Intensive Applications by Martin Kleppmann — Glossary

---

## 6. What is leaderless replication?

Leaderless replication is a distributed data management approach where **any replica can directly accept writes from clients**, eliminating the need for a designated leader node. This contrasts with single-leader replication, where writes must go through a central leader to ensure order and consistency. In leaderless systems, clients send writes to multiple replicas in parallel, and the system relies on mechanisms like **quorums** (write quorum `w` and read quorum `r`) to ensure consistency and availability [1]. 

### Key Characteristics:
1. **No Single Leader**: Writes and reads can be directed to any replica, improving availability but introducing potential consistency challenges [1].  
2. **Quorum-Based Consistency**: Writes are only considered successful if they are acknowledged by at least `w` replicas. Reads require `r` replicas to confirm data, balancing availability and consistency [4].  
3. **Conflict Resolution**: Conflicts arise when writes occur concurrently across replicas. Techniques like **version vectors** or **last-write-wins** (LWW) are used, though they may not guarantee linearizability due to clock skew or network delays [1][2].  
4. **Eventual Consistency**: Leaderless systems typically prioritize **eventual consistency** over strong consistency, meaning reads may return stale data until replicas reconcile differences (e.g., via read repair or hinted handoff) [5][7].  

### Trade-offs:
- **High Availability**: Leaderless replication tolerates node failures and network partitions without requiring failover, making it suitable for distributed systems like Dynamo, Riak, Cassandra, and Voldemort [1][5].  
- **Consistency Risks**: Without strict quorums or consensus algorithms, **linearizability** (strong consistency) is not guaranteed. For example, if a node fails and data is restored from an older replica, the quorum condition (`w` or `r`) may be violated, leading to inconsistencies [4][7].  

### Example Use Cases:
- **Multi-Datacenter Operations**: Leaderless replication is ideal for geographically distributed systems, as it handles latency spikes and network interruptions without centralized coordination [5].  
- **Sloppy Quorums**: Some systems (e.g., Riak) use **sloppy quorums**, allowing writes to proceed even if not all replicas acknowledge them, improving availability at the cost of potential stale reads [7].  

In summary, leaderless replication offers high availability and fault tolerance but requires careful design to manage consistency trade-offs. It is well-suited for applications that can tolerate eventual consistency, such as large-scale distributed databases [1][5].

**Sources (8):**
- [1] Designing Data Intensive Applications by Martin Kleppmann — Part II. Distributed Data > Chapter 5. Replication > Leaderless Replication > Writing to the Database When a Node Is Down
- [2] Designing Data Intensive Applications by Martin Kleppmann — Part II. Distributed Data > Chapter 9. Consistency and Consensus > Linearizability > Implementing Linearizable Systems
- [3] Designing Data Intensive Applications by Martin Kleppmann — Part II. Distributed Data > Chapter 5. Replication > Summary
- [4] Designing Data Intensive Applications by Martin Kleppmann — Part II. Distributed Data > Chapter 5. Replication > Leaderless Replication > Limitations of Quorum Consistency
- [5] Designing Data Intensive Applications by Martin Kleppmann — Part II. Distributed Data > Chapter 5. Replication > Leaderless Replication > Detecting Concurrent Writes
- [6] Designing Data Intensive Applications by Martin Kleppmann — Part II. Distributed Data > Chapter 5. Replication > Leaderless Replication
- [7] Designing Data Intensive Applications by Martin Kleppmann — Part II. Distributed Data > Chapter 5. Replication > Leaderless Replication > Sloppy Quorums and Hinted Handoff
- [8] Designing Data Intensive Applications by Martin Kleppmann — Part II. Distributed Data > Chapter 5. Replication

---

## 7. What problems can arise from replication lag?

Replication lag in distributed systems can lead to several critical issues, as outlined in the sources:

1. **Read-Your-Own-Writes Consistency**: When a user writes data to a leader and immediately reads from a follower, the follower may not yet have the latest data due to replication delay. This creates the illusion that the write was lost, leading to user frustration [6]. For example, a user might submit a comment and then see it disappear when querying a stale replica [6].

2. **Monotonic Reads**: Replication lag can cause a user to read data from different replicas at different times, resulting in older data being seen after newer data. This "time going backward" anomaly violates monotonic reads, where reads should not appear out of order [7]. For instance, a user might first see a comment from one replica and later see it disappear when reading from another [7].

3. **Causality Violations**: If followers replicate data at different speeds, an observer might see a response before the corresponding request. For example, a follower might receive Mrs. Cake’s reply to Mr. Poons’ question before receiving the question itself, creating a paradoxical "psychic powers" effect [7]. This breaks the causal order of events.

4. **Eventual Consistency Challenges**: While eventual consistency ensures replicas will eventually synchronize, large replication lags can temporarily expose inconsistent states. Applications must account for this by designing for read-after-write guarantees or other mechanisms to avoid user-facing issues [4].

These problems highlight the trade-offs between consistency, availability, and performance in distributed systems. Solutions often involve application-level guarantees (e.g., read-after-write consistency) or architectural choices like synchronous replication, though the latter sacrifices availability [6][4].

**Sources (8):**
- [1] Designing Data Intensive Applications by Martin Kleppmann — Part II. Distributed Data > Chapter 8. The Trouble with Distributed Systems
- [2] Designing Data Intensive Applications by Martin Kleppmann — Part II. Distributed Data > Chapter 5. Replication > Leaders and Followers
- [3] Designing Data Intensive Applications by Martin Kleppmann — Part II. Distributed Data > Chapter 5. Replication > Leaderless Replication
- [4] Designing Data Intensive Applications by Martin Kleppmann — Part II. Distributed Data > Chapter 5. Replication > Problems with Replication Lag > Solutions for Replication Lag
- [5] Designing Data Intensive Applications by Martin Kleppmann — Part II. Distributed Data > Chapter 7. Transactions > The Slippery Concept of a Transaction > The Meaning of ACID
- [6] Designing Data Intensive Applications by Martin Kleppmann — Part II. Distributed Data > Chapter 5. Replication > Problems with Replication Lag > Reading Your Own Writes
- [7] Designing Data Intensive Applications by Martin Kleppmann — Part II. Distributed Data > Chapter 5. Replication > Problems with Replication Lag > Consistent Prefix Reads
- [8] Designing Data Intensive Applications by Martin Kleppmann — Part II. Distributed Data > Chapter 5. Replication > Multi-Leader Replication

---

## 8. What is the difference between optimistic and pessimistic concurrency control?

Optimistic and pessimistic concurrency control differ fundamentally in their approach to handling transaction conflicts:

1. **Pessimistic Concurrency Control** (e.g., two-phase locking, 2PL):  
   - Assumes conflicts are likely and **blocks transactions** to prevent them.  
   - Uses locks (e.g., range locks) to ensure exclusive access to resources, which can reduce contention but may lower throughput due to blocking [2].  
   - Example: If a transaction tries to modify a resource, it acquires a lock, preventing other transactions from accessing it until the lock is released.  

2. **Optimistic Concurrency Control** (e.g., Serializable Snapshot Isolation, SSI):  
   - Assumes conflicts are unlikely and **allows transactions to proceed without locks**.  
   - Transactions are validated at commit time; if conflicts are detected (e.g., serialization violations), the transaction is aborted and retried [1].  
   - Example: SSI uses snapshot isolation to read data consistently and detects write conflicts via an algorithm, aborting only conflicting transactions [2].  

**Key Trade-offs**:  
- Pessimistic methods (like 2PL) are more restrictive but avoid retries, while optimistic methods (like SSI) prioritize performance under low contention but may incur higher abort rates under high contention [1].  
- Pessimistic approaches are traditional and widely used, whereas optimistic techniques (e.g., SSI) aim to balance serializability with performance in modern systems [2].  

For systems with low contention, optimistic control often outperforms pessimistic methods, but high contention can degrade its efficiency [1].

**Sources (8):**
- [1] Designing Data Intensive Applications by Martin Kleppmann — Part II. Distributed Data > Chapter 7. Transactions > Serializability > Serializable Snapshot Isolation (SSI)
- [2] Designing Data Intensive Applications by Martin Kleppmann — Part II. Distributed Data > Chapter 7. Transactions > Serializability > Serializable Snapshot Isolation (SSI)
- [3] Designing Data Intensive Applications by Martin Kleppmann — Part II. Distributed Data > Chapter 9. Consistency and Consensus > Ordering Guarantees
- [4] Designing Data Intensive Applications by Martin Kleppmann — Index
- [5] Designing Data Intensive Applications by Martin Kleppmann — Part II. Distributed Data > Chapter 7. Transactions > Serializability > Actual Serial Execution
- [6] Designing Data Intensive Applications by Martin Kleppmann — Index
- [7] Designing Data Intensive Applications by Martin Kleppmann — Index
- [8] Designing Data Intensive Applications by Martin Kleppmann — Index

---

## 9. What is a distributed transaction?

A **distributed transaction** is a transaction that spans multiple resources or systems, ensuring atomicity across all participants. There are two primary types:

1. **Database-internal distributed transactions**: These occur within a single distributed database system (e.g., VoltDB, MySQL Cluster’s NDB storage engine). All nodes involved run the same database software, allowing optimized protocols for consistency [1].

2. **Heterogeneous distributed transactions**: These involve multiple disparate technologies (e.g., a message broker and a database). They require all participants to agree on an atomic commit protocol (e.g., XA) to ensure consistency across systems [1]. For example, a message from a queue can be acknowledged only if the associated database transaction succeeds, preventing duplicates or losses [2].

**Key characteristics**:
- **Atomicity**: All operations must succeed or fail together (e.g., via two-phase commit [2PC] protocols [4]).
- **Protocols**: Standards like XA (eXtended Architecture) enable coordination across heterogeneous systems [2].
- **Challenges**: They face performance penalties (e.g., MySQL’s distributed transactions are 10x slower than single-node ones [1]) and operational complexity [1].

Distributed transactions are critical for ensuring consistency in cross-system workflows but are often avoided due to their trade-offs [1].

**Sources (8):**
- [1] Designing Data Intensive Applications by Martin Kleppmann — Part II. Distributed Data > Chapter 9. Consistency and Consensus > Distributed Transactions and Consensus > Distributed Transactions in Practice
- [2] Designing Data Intensive Applications by Martin Kleppmann — Part II. Distributed Data > Chapter 9. Consistency and Consensus > Distributed Transactions and Consensus > Distributed Transactions in Practice
- [3] Designing Data Intensive Applications by Martin Kleppmann — Part III. Derived Data > Chapter 12. The Future of Data Systems > Data Integration > Combining Specialized Tools by Deriving Data
- [4] Designing Data Intensive Applications by Martin Kleppmann — Part II. Distributed Data > Chapter 9. Consistency and Consensus > Distributed Transactions and Consensus > Atomic Commit and Two-Phase Commit (2PC)
- [5] Designing Data Intensive Applications by Martin Kleppmann — Part II. Distributed Data > Chapter 9. Consistency and Consensus > Summary
- [6] Designing Data Intensive Applications by Martin Kleppmann — Part II. Distributed Data > Chapter 7. Transactions > The Slippery Concept of a Transaction > Single-Object and Multi-Object Operations
- [7] Designing Data Intensive Applications by Martin Kleppmann — Index
- [8] Designing Data Intensive Applications by Martin Kleppmann — Part II. Distributed Data > Chapter 9. Consistency and Consensus > Summary

---

## 10. What is the two-phase commit protocol?

The **two-phase commit (2PC)** protocol is a distributed coordination algorithm used to ensure atomicity across multiple nodes in a distributed system. It operates in two distinct phases to commit a transaction:

1. **Prepare Phase**:  
   - The **coordinator** (central node) sends a `prepare` request to all participants (nodes involved in the transaction).  
   - Each participant prepares its local commit, ensuring it can roll back if needed, and responds with a `yes` or `no` vote.  
   - If any participant replies `no` or times out, the coordinator **aborts** the transaction [1][2].

2. **Commit Phase**:  
   - If all participants vote `yes`, the coordinator sends a `commit` message to all participants.  
   - Each participant commits its local transaction and acknowledges the commit.  
   - If the coordinator fails during this phase, participants remain in an **in-doubt** state until the coordinator recovers. The coordinator then uses a **transaction log** to determine the status of unresolved transactions and either commits or aborts them [2][3].

### Key Characteristics:
- **Blocking**: 2PC can become **stuck** if the coordinator fails during the commit phase, as participants cannot proceed without confirmation [1][3].  
- **Atomicity**: Ensures all nodes either commit or abort the transaction, maintaining consistency across the system.  
- **Coordinator Dependency**: The protocol relies heavily on the coordinator’s reliability. If the coordinator crashes, participants must wait for recovery, which is resolved by logging decisions to disk [2][3].

### Limitations:
- **Performance Overhead**: Requires additional disk I/O (e.g., `fsync`) for crash recovery and multiple network round trips, leading to slower transactions compared to single-node operations [6].  
- **Unbounded Delays**: 2PC assumes bounded network delays, but in systems with unbounded delays (e.g., cloud environments), it risks **failure amplification** or **stale states** [1][3].  
- **Alternatives**: Protocols like **three-phase commit (3PC)** aim to reduce blocking but face similar challenges in real-world scenarios [1][3].

### Use Cases:
- **XA Transactions**: 2PC is often implemented via the **XA standard**, enabling distributed transactions across heterogeneous systems (e.g., databases and message brokers) [1][6].  
- **Distributed Databases**: Used in systems requiring strong consistency, though many modern systems avoid 2PC due to its operational complexity and performance costs [6][8].

For further details, refer to [1][2][3], and [6].

**Sources (8):**
- [1] Designing Data Intensive Applications by Martin Kleppmann — Index
- [2] Designing Data Intensive Applications by Martin Kleppmann — Part II. Distributed Data > Chapter 9. Consistency and Consensus > Distributed Transactions and Consensus > Atomic Commit and Two-Phase Commit (2PC)
- [3] Designing Data Intensive Applications by Martin Kleppmann — Part II. Distributed Data > Chapter 9. Consistency and Consensus > Distributed Transactions and Consensus > Atomic Commit and Two-Phase Commit (2PC)
- [4] Designing Data Intensive Applications by Martin Kleppmann — Part II. Distributed Data > Chapter 9. Consistency and Consensus > Summary
- [5] Designing Data Intensive Applications by Martin Kleppmann — Part II. Distributed Data > Chapter 9. Consistency and Consensus > Distributed Transactions and Consensus > Distributed Transactions in Practice
- [6] Designing Data Intensive Applications by Martin Kleppmann — Part II. Distributed Data > Chapter 9. Consistency and Consensus > Distributed Transactions and Consensus > Distributed Transactions in Practice
- [7] Designing Data Intensive Applications by Martin Kleppmann — Index
- [8] Designing Data Intensive Applications by Martin Kleppmann — Index

---

## 11. What is linearizability?

Linearizability is a consistency model that ensures operations on a single data item (e.g., a register) appear to occur atomically and in a single, sequential timeline, as if there were only one copy of the data [7]. It guarantees that once a write operation is successfully completed, all subsequent reads will see the updated value, ensuring **recency** and **order** [7]. This model preserves **causality**, meaning that if one operation causally precedes another, the system will reflect that order [1]. 

Key characteristics of linearizability include:
1. **Atomicity**: Operations are treated as indivisible, with no concurrency (e.g., no branching timelines) [1].
2. **Recency Guarantee**: Clients always see the most up-to-date value, avoiding stale reads [7].
3. **Causality Preservation**: It ensures that operations are ordered according to their actual occurrence, even in distributed systems [1].

Linearizability differs from **serializability**, which applies to transactions involving multiple objects and focuses on isolation rather than recency [4]. While linearizability is stricter, it can harm performance and availability in systems with network delays or geographic distribution [2]. For example, **single-leader replication** can achieve linearizability with synchronous reads and writes, but **multi-leader or leaderless systems** (e.g., Dynamo-style) often sacrifice linearizability for scalability and availability [8].

In practice, linearizability is achievable via consensus algorithms (e.g., ZooKeeper, etcd) but requires careful design to avoid trade-offs like reduced performance or data inconsistencies [2, 8].

**Sources (8):**
- [1] Designing Data Intensive Applications by Martin Kleppmann — Part II. Distributed Data > Chapter 9. Consistency and Consensus > Ordering Guarantees > Ordering and Causality
- [2] Designing Data Intensive Applications by Martin Kleppmann — Part II. Distributed Data > Chapter 9. Consistency and Consensus > Linearizability > The Cost of Linearizability
- [3] Designing Data Intensive Applications by Martin Kleppmann — Part II. Distributed Data > Chapter 9. Consistency and Consensus > Linearizability > What Makes a System Linearizable?
- [4] Designing Data Intensive Applications by Martin Kleppmann — Part II. Distributed Data > Chapter 9. Consistency and Consensus > Linearizability > What Makes a System Linearizable?
- [5] Designing Data Intensive Applications by Martin Kleppmann — Part II. Distributed Data > Chapter 9. Consistency and Consensus > Linearizability > Implementing Linearizable Systems
- [6] Designing Data Intensive Applications by Martin Kleppmann — Part II. Distributed Data > Chapter 9. Consistency and Consensus > Linearizability > Relying on Linearizability
- [7] Designing Data Intensive Applications by Martin Kleppmann — Part II. Distributed Data > Chapter 9. Consistency and Consensus > Linearizability
- [8] Designing Data Intensive Applications by Martin Kleppmann — Part II. Distributed Data > Chapter 9. Consistency and Consensus > Linearizability > Implementing Linearizable Systems

---

## 12. What is the difference between REST and RPC?

REST and RPC differ fundamentally in their design philosophies, use cases, and implementation details. Here's a structured comparison:

1. **Design Philosophy**  
   - **REST** is an architectural style based on HTTP principles, emphasizing stateless interactions, resource-based URLs, and standard HTTP methods (GET, POST, etc.). It does not hide the fact it is a network protocol [1].  
   - **RPC** (Remote Procedure Call) abstracts network communication, allowing clients to invoke procedures on remote servers as if they were local. It often uses binary encodings for efficiency and focuses on low-latency, direct communication [1].

2. **Data Formats**  
   - **REST** typically uses JSON or XML for data exchange, prioritizing human-readable formats and simplicity. It is well-suited for experimentation and debugging via tools like `curl` [1].  
   - **RPC** often employs binary formats (e.g., Protocol Buffers, Thrift) for performance, though JSON-over-HTTP is also used. Binary formats enable more compact data transfer and efficient schema evolution [1].

3. **Use Cases**  
   - **REST** is prevalent for public APIs and cross-organizational services due to its simplicity and broad language support [3].  
   - **RPC** is commonly used for internal service communication within organizations, where performance and tight integration are critical [1].

4. **Compatibility and Evolution**  
   - Both REST and RPC require compatibility mechanisms, but **RPC frameworks** (e.g., Avro, Thrift) often provide explicit rules for schema evolution, ensuring backward/forward compatibility [2].  
   - **REST** relies on application-layer conventions (e.g., versioned URLs or headers) for compatibility, as JSON lacks strict schema enforcement [2].

5. **Performance**  
   - **Custom RPC protocols** with binary encodings can outperform JSON-over-REST, especially for large data transfers [1]. However, REST benefits from a mature ecosystem of tools (e.g., caches, load balancers) and ease of use [1].

6. **Implementation**  
   - **REST** is protocol-agnostic but typically built on HTTP. **RPC** can be implemented over various transports (e.g., HTTP, TCP) and often includes features like streaming (gRPC) or asynchronous messaging [1].

In summary, REST is a style for networked APIs, while RPC is a set of protocols for efficient, low-latency communication. The choice depends on trade-offs between simplicity, performance, and ecosystem support.

**Sources (8):**
- [1] Designing Data Intensive Applications by Martin Kleppmann — Part I. Foundations of Data Systems > Chapter 4. Encoding and Evolution > Modes of Dataflow > Dataflow Through Services: REST and RPC
- [2] Designing Data Intensive Applications by Martin Kleppmann — Part I. Foundations of Data Systems > Chapter 4. Encoding and Evolution > Modes of Dataflow > Message-Passing Dataflow
- [3] Designing Data Intensive Applications by Martin Kleppmann — Part I. Foundations of Data Systems > Chapter 4. Encoding and Evolution > Modes of Dataflow > Dataflow Through Services: REST and RPC
- [4] Designing Data Intensive Applications by Martin Kleppmann — Part I. Foundations of Data Systems > Chapter 4. Encoding and Evolution > Modes of Dataflow > Dataflow Through Services: REST and RPC
- [5] Designing Data Intensive Applications by Martin Kleppmann — Part I. Foundations of Data Systems > Chapter 4. Encoding and Evolution > Summary
- [6] Designing Data Intensive Applications by Martin Kleppmann — Part III. Derived Data > Chapter 12. The Future of Data Systems > Unbundling Databases > Designing Applications Around Dataflow
- [7] Designing Data Intensive Applications by Martin Kleppmann — Part I. Foundations of Data Systems > Chapter 4. Encoding and Evolution > Formats for Encoding Data
- [8] Designing Data Intensive Applications by Martin Kleppmann — Part I. Foundations of Data Systems > Chapter 4. Encoding and Evolution > Formats for Encoding Data > Avro

---

## 13. What is a message broker used for?

A message broker is used to facilitate reliable, asynchronous communication between processes or systems by acting as an intermediary that stores and forwards messages. Its primary purposes include:  

1. **Decoupling Senders and Receivers**: It allows senders to publish messages without knowing the recipients' locations or availability, enabling logical separation between systems [1].  
2. **Reliability and Fault Tolerance**: It buffers messages if recipients are unavailable, automatically redelivers messages after crashes, and ensures durability by persisting messages (e.g., to disk) to prevent data loss [1][2].  
3. **Scalability and Load Balancing**: It supports multiple producers and consumers on the same topic, distributing messages across consumers for parallel processing (load balancing) or broadcasting to all consumers (fan-out) [3][4].  
4. **Handling Asynchronous Communication**: It enables one-way message passing, where senders do not wait for acknowledgments, and delivery occurs asynchronously [1][2].  
5. **Supporting Stream Processing**: It underpins systems like Apache Kafka, which use partitioned logs to manage high-throughput event streams, allowing scalable, fault-tolerant data pipelines [4][5].  

Message brokers are distinct from databases due to their focus on transient, ordered message delivery rather than persistent storage [2][6]. They are critical in distributed systems for ensuring reliability, scalability, and loose coupling between components.

**Sources (8):**
- [1] Designing Data Intensive Applications by Martin Kleppmann — Part I. Foundations of Data Systems > Chapter 4. Encoding and Evolution > Modes of Dataflow > Message-Passing Dataflow
- [2] Designing Data Intensive Applications by Martin Kleppmann — Part III. Derived Data > Chapter 11. Stream Processing > Transmitting Event Streams > Messaging Systems
- [3] Designing Data Intensive Applications by Martin Kleppmann — Part III. Derived Data > Chapter 11. Stream Processing > Transmitting Event Streams > Messaging Systems
- [4] Designing Data Intensive Applications by Martin Kleppmann — Part III. Derived Data > Chapter 11. Stream Processing > Transmitting Event Streams > Partitioned Logs
- [5] Designing Data Intensive Applications by Martin Kleppmann — Part III. Derived Data > Chapter 11. Stream Processing > Transmitting Event Streams > Partitioned Logs
- [6] Designing Data Intensive Applications by Martin Kleppmann — Part III. Derived Data > Chapter 11. Stream Processing > Transmitting Event Streams > Messaging Systems
- [7] Designing Data Intensive Applications by Martin Kleppmann — Index
- [8] Designing Data Intensive Applications by Martin Kleppmann — Part III. Derived Data > Chapter 11. Stream Processing > Transmitting Event Streams > Partitioned Logs

---

## 14. What is the actor model in the context of distributed systems?

The actor model in distributed systems is a programming model for concurrency that abstracts away thread management by using asynchronous message passing. In this model, actors (independent entities) communicate by sending and receiving messages, each maintaining their own local state. Key characteristics include:  

1. **Asynchronous Communication**: Actors do not wait for responses, allowing non-blocking interactions. Message delivery is not guaranteed, and losses can occur, especially in distributed settings [2].  
2. **Location Transparency**: The model handles communication whether actors are on the same node or different nodes. Messages are encoded, transmitted over the network, and decoded, abstracting physical location [2].  
3. **Decoupling**: Senders and receivers are logically decoupled; a sender publishes messages without knowing recipients, similar to message-passing dataflow [1].  
4. **Fault Tolerance**: While the model does not guarantee message delivery, it is designed to tolerate partial failures, aligning with the partially synchronous system model [3].  

Distributed actor frameworks (e.g., Akka, Orleans) integrate this model with message brokers, enabling scalability across nodes. However, upgrades require careful handling of forward/backward compatibility to manage message exchanges between different versions [2].  

Citations: [1], [2], [3].

**Sources (8):**
- [1] Designing Data Intensive Applications by Martin Kleppmann — Part I. Foundations of Data Systems > Chapter 4. Encoding and Evolution > Modes of Dataflow > Message-Passing Dataflow
- [2] Designing Data Intensive Applications by Martin Kleppmann — Part I. Foundations of Data Systems > Chapter 4. Encoding and Evolution > Modes of Dataflow > Message-Passing Dataflow
- [3] Designing Data Intensive Applications by Martin Kleppmann — Part II. Distributed Data > Chapter 8. The Trouble with Distributed Systems > Knowledge, Truth, and Lies > System Model and Reality
- [4] Designing Data Intensive Applications by Martin Kleppmann — Part I. Foundations of Data Systems > Chapter 4. Encoding and Evolution > Summary
- [5] Designing Data Intensive Applications by Martin Kleppmann — Part II. Distributed Data > Chapter 5. Replication > Leaderless Replication
- [6] Designing Data Intensive Applications by Martin Kleppmann — Glossary
- [7] Designing Data Intensive Applications by Martin Kleppmann — Part II. Distributed Data > Chapter 8. The Trouble with Distributed Systems > Knowledge, Truth, and Lies
- [8] Designing Data Intensive Applications by Martin Kleppmann — Part II. Distributed Data > Chapter 8. The Trouble with Distributed Systems > Summary

---

## 15. What is data partitioning (sharding)?

Data partitioning, also known as sharding, is a technique used to split a large dataset into smaller, manageable parts called partitions (or shards) to improve scalability and performance in distributed systems. This approach allows data to be distributed across multiple nodes in a shared-nothing architecture, where each node operates independently [1]. 

### Key Concepts and Methods:
1. **Partitioning Approaches**:
   - **Key-Range Partitioning**: Keys are sorted, and each partition owns a contiguous range of keys. This enables efficient range queries but risks "hotspots" if certain ranges are frequently accessed [2]. Partitions can be dynamically rebalanced by splitting ranges when they grow too large.
   - **Hash Partitioning**: A hash function is applied to keys, distributing them evenly across partitions. While this balances load well, it eliminates ordered key sequences, making range queries inefficient [4]. Hash partitioning often involves predefining a fixed number of partitions and redistributing them when nodes are added/removed [2].

2. **Hybrid Strategies**: Some systems use compound keys, where part of the key determines the partition (e.g., hashed) and another part defines the sort order (e.g., for range queries) [4]. Cassandra, for example, uses a hybrid approach with compound primary keys to balance hash-based distribution and sorted indexing [4].

3. **Secondary Indexes**: These must also be partitioned. 
   - **Document-Partitioned Indexes (Local)**: Stored in the same partition as the primary data, simplifying writes but requiring scatter/gather operations for reads.
   - **Term-Partitioned Indexes (Global)**: Partitioned separately based on indexed values, allowing efficient reads but requiring updates to multiple partitions during writes [2].

4. **Trade-offs**: Hash partitioning sacrifices range query efficiency, while key-range partitioning risks uneven load distribution. Hybrid methods aim to balance these trade-offs [4].

### Why Partitioning Matters:
Partitioning enables horizontal scaling by distributing data across nodes, but it introduces complexity in managing cross-partition operations (e.g., transactions) and requires careful rebalancing when nodes are added or removed [1]. It is distinct from replication, which focuses on redundancy rather than distribution [3].

For further details on rebalancing, secondary indexes, or hybrid strategies, refer to the cited sources [1][2][4].

**Sources (8):**
- [1] Designing Data Intensive Applications by Martin Kleppmann — Part II. Distributed Data > Chapter 6. Partitioning
- [2] Designing Data Intensive Applications by Martin Kleppmann — Part II. Distributed Data > Chapter 6. Partitioning > Summary
- [3] Designing Data Intensive Applications by Martin Kleppmann — Part II. Distributed Data
- [4] Designing Data Intensive Applications by Martin Kleppmann — Part II. Distributed Data > Chapter 6. Partitioning > Partitioning of Key-Value Data > Partitioning by Hash of Key
- [5] Designing Data Intensive Applications by Martin Kleppmann — Glossary
- [6] Designing Data Intensive Applications by Martin Kleppmann — Glossary
- [7] Designing Data Intensive Applications by Martin Kleppmann — Part II. Distributed Data > Chapter 6. Partitioning > Partitioning and Secondary Indexes
- [8] Designing Data Intensive Applications by Martin Kleppmann — Index

---

## 16. How does consistent hashing help with partitioning?

Consistent hashing helps with partitioning by using randomly chosen partition boundaries to distribute keys uniformly across partitions, avoiding the need for centralized control or distributed consensus during rebalancing [1]. This approach ensures that adding or removing nodes requires minimal redistribution of data, as only a fraction of partitions needs to be reassigned [8]. However, it sacrifices the ability to perform efficient range queries, as keys are scattered across partitions rather than ordered [1]. While consistent hashing is not widely used in databases due to rebalancing inefficiencies [8], it remains a foundational concept for hash-based partitioning, where hash functions like MD5 or Fowler–Noll–Vo are employed to achieve uniform data distribution [3].

**Sources (8):**
- [1] Designing Data Intensive Applications by Martin Kleppmann — Part II. Distributed Data > Chapter 6. Partitioning > Partitioning of Key-Value Data > Partitioning by Hash of Key
- [2] Designing Data Intensive Applications by Martin Kleppmann — Part II. Distributed Data > Chapter 6. Partitioning > Summary
- [3] Designing Data Intensive Applications by Martin Kleppmann — Part II. Distributed Data > Chapter 6. Partitioning > Partitioning of Key-Value Data > Partitioning by Hash of Key
- [4] Designing Data Intensive Applications by Martin Kleppmann — Part II. Distributed Data > Chapter 6. Partitioning > Summary
- [5] Designing Data Intensive Applications by Martin Kleppmann — Part II. Distributed Data > Chapter 6. Partitioning > Partitioning and Secondary Indexes
- [6] Designing Data Intensive Applications by Martin Kleppmann — Part II. Distributed Data > Chapter 6. Partitioning > Partitioning of Key-Value Data > Partitioning by Key Range
- [7] Designing Data Intensive Applications by Martin Kleppmann — Part II. Distributed Data > Chapter 6. Partitioning > Summary
- [8] Designing Data Intensive Applications by Martin Kleppmann — Part II. Distributed Data > Chapter 6. Partitioning > Rebalancing Partitions > Operations: Automatic or Manual Rebalancing

---

## 17. What is a secondary index and why is it harder to maintain in a partitioned database?

A **secondary index** is a data structure that allows efficient searching for records based on attributes other than the primary key (e.g., finding all cars with a specific color). Unlike primary keys, secondary indexes do not uniquely identify records but instead enable queries on non-key fields. 

In a **partitioned database**, maintaining secondary indexes is more complex due to the following reasons:  

1. **Partitioning vs. Index Distribution**:  
   Secondary indexes do not map neatly to partitions. For example, if a database is partitioned by document ID (document-based partitioning), a secondary index on "color" might spread entries across multiple partitions (e.g., red cars could be in partition 0 and partition 1). This requires **scatter/gather** queries, where the system must query all partitions and combine results, increasing read latency [3].  

2. **Term-Based Partitioning Challenges**:  
   Alternative approaches like term-based partitioning (grouping entries by indexed terms) require careful design. For instance, if you partition by color, all red cars must reside in the same partition. However, this can lead to **skew** (uneven data distribution) and requires dynamic rebalancing, which complicates maintenance [3].  

3. **Consistency and Asynchrony**:  
   Updates to secondary indexes in partitioned systems often involve multiple partitions. For example, adding a red car might require updating the "color:red" index across several partitions. If updates are asynchronous (e.g., in DynamoDB), there may be delays in reflecting changes in the index, leading to temporary inconsistencies [5].  

4. **Rebalancing Overhead**:  
   When partitions are rebalanced (e.g., due to node additions/removals), secondary indexes must be updated across partitions. This adds complexity, as indexes must remain consistent with the underlying data while minimizing network and I/O overhead [5].  

In summary, secondary indexes are harder to maintain in partitioned databases because their distribution must align with partitioning strategies, and updates/queries often span multiple partitions, introducing latency, consistency challenges, and operational complexity [3][5].

**Sources (8):**
- [1] Designing Data Intensive Applications by Martin Kleppmann — Part II. Distributed Data > Chapter 6. Partitioning > Partitioning and Secondary Indexes
- [2] Designing Data Intensive Applications by Martin Kleppmann — Part II. Distributed Data > Chapter 6. Partitioning > Partitioning and Secondary Indexes > Partitioning Secondary Indexes by Document
- [3] Designing Data Intensive Applications by Martin Kleppmann — Part II. Distributed Data > Chapter 6. Partitioning > Partitioning and Secondary Indexes > Partitioning Secondary Indexes by Document
- [4] Designing Data Intensive Applications by Martin Kleppmann — Index
- [5] Designing Data Intensive Applications by Martin Kleppmann — Part II. Distributed Data > Chapter 6. Partitioning > Rebalancing Partitions
- [6] Designing Data Intensive Applications by Martin Kleppmann — Part II. Distributed Data > Chapter 6. Partitioning > Summary
- [7] Designing Data Intensive Applications by Martin Kleppmann — Part I. Foundations of Data Systems > Chapter 3. Storage and Retrieval > Data Structures That Power Your Database > Other Indexing Structures
- [8] Designing Data Intensive Applications by Martin Kleppmann — Part II. Distributed Data > Chapter 6. Partitioning > Summary

---

## 18. What is the difference between batch processing and stream processing?

The primary differences between batch processing and stream processing are as follows:

1. **Data Nature**:  
   - **Batch processing** operates on **bounded datasets** with a known, finite size [1]. It processes data in bulk, often scheduled periodically (e.g., daily jobs) [2].  
   - **Stream processing** handles **unbounded datasets** that grow continuously over time [1]. It processes data in real-time or near-real-time as events arrive [11].

2. **Latency and Timing**:  
   - Batch processing prioritizes **throughput** (processing large datasets efficiently) and has higher latency [2].  
   - Stream processing emphasizes **low latency** to respond to events as they occur, enabling near-instantaneous results [11].

3. **State Management**:  
   - Batch processing uses **deterministic, pure functions** with no side effects, treating inputs as immutable [1].  
   - Stream processing extends this by managing **fault-tolerant state** (e.g., maintaining session data for joins) and handling dynamic updates [7].

4. **Fault Tolerance**:  
   - Batch systems ensure **exactly-once semantics** by replaying tasks and discarding failed outputs [7].  
   - Stream processors face challenges due to infinite data, relying on **microbatching** or **checkpointing** to tolerate failures [7].

5. **Implementation Overlap**:  
   - Tools like **Apache Spark** use microbatches to emulate stream processing on top of batch engines, while **Apache Flink** performs batch processing within a stream framework [1].  
   - The **lambda architecture** combines both approaches: batch systems reprocess historical data, and stream systems handle real-time updates [5].

These distinctions highlight how batch and stream processing complement each other in modern data systems, with trade-offs in latency, complexity, and fault tolerance [1][5][7].

**Sources (8):**
- [1] Designing Data Intensive Applications by Martin Kleppmann — Part III. Derived Data > Chapter 12. The Future of Data Systems > Data Integration > Batch and Stream Processing
- [2] Designing Data Intensive Applications by Martin Kleppmann — Part III. Derived Data > Chapter 10. Batch Processing
- [3] Designing Data Intensive Applications by Martin Kleppmann — Part III. Derived Data > Chapter 11. Stream Processing > Processing Streams
- [4] Designing Data Intensive Applications by Martin Kleppmann — Part III. Derived Data > Chapter 10. Batch Processing
- [5] Designing Data Intensive Applications by Martin Kleppmann — Part III. Derived Data > Chapter 12. The Future of Data Systems > Data Integration > Batch and Stream Processing
- [6] Designing Data Intensive Applications by Martin Kleppmann — Part III. Derived Data > Chapter 11. Stream Processing > Processing Streams > Stream Joins
- [7] Designing Data Intensive Applications by Martin Kleppmann — Part III. Derived Data > Chapter 11. Stream Processing > Processing Streams > Fault Tolerance
- [8] Designing Data Intensive Applications by Martin Kleppmann — Part III. Derived Data > Chapter 11. Stream Processing > Processing Streams > Stream Joins

---

## 19. What is exactly-once semantics in stream processing?

Exactly-once semantics in stream processing ensures that each record is processed exactly once, even in the presence of failures. This requires mechanisms to prevent duplicates or missed records, as outlined in the sources:

1. **Checkpointing and Microbatching**:  
   Stream processors like Apache Flink use periodic checkpoints to save state, allowing recovery from failures by restarting from the last checkpoint. However, once output leaves the processor (e.g., writing to a database), the framework cannot discard it, risking duplicates. This necessitates **atomic commits** to ensure all side effects (e.g., database writes, message sends) are applied together or none at all [2][92].

2. **Atomic Commit Facilities**:  
   Systems like Google Cloud Dataflow and VoltDB implement atomic commit protocols to coordinate state changes and messaging within the stream processing framework. This avoids partial updates and ensures consistency, unlike traditional distributed transactions (e.g., XA) that span heterogeneous systems [92][96].

3. **Idempotence**:  
   Idempotent operations (e.g., writing a value with a unique offset) allow retries without duplicating effects. For example, Kafka’s offsets track which messages have been processed, preventing reprocessing of the same data [97].

4. **Fault Tolerance Challenges**:  
   Stream processing differs from batch processing because outputs are continuous. Recovery mechanisms like microbatching, checkpointing, or idempotent writes are used to ensure exactly-once semantics, but they must account for external systems (e.g., databases) that may not support rollback [2][476].

5. **Transactional Messaging**:  
   Kafka’s KIP-98 proposal and similar efforts aim to provide exactly-once delivery via transactional messaging, ensuring messages are processed once and only once across the entire pipeline [95][96].

In summary, exactly-once semantics in stream processing combines checkpointing, atomic commits, idempotent operations, and coordination with external systems to guarantee reliable, duplicate-free processing [2][92][96].

**Sources (8):**
- [1] Designing Data Intensive Applications by Martin Kleppmann — Part III. Derived Data > Chapter 11. Stream Processing > Summary
- [2] Designing Data Intensive Applications by Martin Kleppmann — Part III. Derived Data > Chapter 11. Stream Processing > Processing Streams > Fault Tolerance
- [3] Designing Data Intensive Applications by Martin Kleppmann — Part III. Derived Data > Chapter 11. Stream Processing > Summary
- [4] Designing Data Intensive Applications by Martin Kleppmann — Part III. Derived Data > Chapter 11. Stream Processing > Summary
- [5] Designing Data Intensive Applications by Martin Kleppmann — Part III. Derived Data > Chapter 11. Stream Processing > Processing Streams > Fault Tolerance
- [6] Designing Data Intensive Applications by Martin Kleppmann — Part III. Derived Data > Chapter 11. Stream Processing > Processing Streams > Fault Tolerance
- [7] Designing Data Intensive Applications by Martin Kleppmann — Part III. Derived Data > Chapter 12. The Future of Data Systems > Data Integration > Batch and Stream Processing
- [8] Designing Data Intensive Applications by Martin Kleppmann — Index

---

## 20. What ethical considerations does the book raise about data systems?

The book raises several ethical considerations regarding data systems, emphasizing the responsibility of engineers and developers to consider the societal impact of their work. Key points include:  

1. **Human Impact of Data Systems**: The book highlights that datasets often involve people’s behavior, identity, and interests, requiring systems to be treated with humanity and respect. Decisions made by data systems—such as predicting recidivism, loan defaults, or insurance risks—can directly affect individuals’ lives, necessitating careful ethical evaluation [1].  

2. **Bias and Fairness**: It warns against the risks of biased algorithms, noting that predictive analytics can perpetuate inequalities (e.g., racial or socioeconomic disparities) if not designed thoughtfully. Examples include algorithms learning prejudice from historical data, leading to unfair outcomes [2][84][85].  

3. **Transparency and Accountability**: The text stresses the need for transparency in algorithmic decision-making, citing calls for regulations like the EU’s “Right to Explanation” and advocating for accountability mechanisms to ensure systems are fair and just [89][88].  

4. **Ethical Responsibility of Engineers**: Engineers are urged to prioritize human dignity over profit, acknowledging that technology’s impact depends on its use. The book critiques the cavalier attitude toward privacy and negative consequences in practice, advocating for adherence to ethical guidelines like the ACM’s Code of Ethics [1][77][78].  

5. **Consequences of Data Collection**: It raises concerns about the pervasive nature of data collection, referencing how systems like "data brokers" track individuals’ lives without consent, and how such practices can infringe on privacy and autonomy [90][110].  

These considerations underscore the book’s argument that ethical responsibility is integral to designing data systems that serve society without harm.

**Sources (8):**
- [1] Designing Data Intensive Applications by Martin Kleppmann — Part III. Derived Data > Chapter 12. The Future of Data Systems > Doing the Right Thing
- [2] Designing Data Intensive Applications by Martin Kleppmann — Part III. Derived Data > Chapter 12. The Future of Data Systems > Doing the Right Thing > Predictive Analytics
- [3] Designing Data Intensive Applications by Martin Kleppmann — Part III. Derived Data > Chapter 12. The Future of Data Systems > Summary
- [4] Designing Data Intensive Applications by Martin Kleppmann — Part III. Derived Data > Chapter 12. The Future of Data Systems > Summary
- [5] Designing Data Intensive Applications by Martin Kleppmann — Part III. Derived Data > Chapter 12. The Future of Data Systems > Unbundling Databases
- [6] Designing Data Intensive Applications by Martin Kleppmann — Preface > Scope of This Book
- [7] Designing Data Intensive Applications by Martin Kleppmann — Part III. Derived Data > Chapter 12. The Future of Data Systems > Summary
- [8] Designing Data Intensive Applications by Martin Kleppmann — Preface > Who Should Read This Book?

---
