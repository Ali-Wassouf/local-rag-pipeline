# Baseline evals — Phase 3 (vector-only, no hybrid, no reranking)

20 real questions run against the actual system (real embedder, real generator, real retrieval — no mocks), to be re-run and diffed against once Phase 4 adds hybrid search (RRF) and the cross-encoder reranker. Per docs/build-phases.md Phase 4's "Done when": hybrid-vs-vector and reranked-vs-unreranked must be measured *separately* against this baseline, so we know which change earned its keep.

**Setup:**
- Document: *Designing Data-Intensive Applications* by Martin Kleppmann (real ~600-page book, not a fixture)
- Project: "Systems Books"
- Retrieval: vector-only, top 8 chunks by cosine distance, mandatory project filter
- Generator: `rag-gen` (qwen3:8b, num_ctx=8192, temperature=0.2)
- Each question asked in its own fresh conversation (no prior turns influencing retrieval)
- Every answer below streamed token-by-token in real time and was persisted with `message_citations` exactly as shown

---

## 1. What is a log-structured storage engine?

A **log-structured storage engine** is a type of storage system that organizes data as an **append-only log** of records, where new data is always added to the end of the log rather than modifying existing entries. This approach is inspired by log-structured file systems [11] and is central to **LSM-trees** (Log-Structured Merge-Trees). Here’s how it works:

1. **Append-Only Logs**:  
   Data is written sequentially to a log file, similar to how databases like LevelDB or RocksDB operate. For example, the `db_set` function in the Bash example appends key-value pairs to a file [1]. This ensures efficient writes, as appending to a file is fast.

2. **SSTables and Compaction**:  
   Periodically, the log is converted into **sorted, immutable files** called **SSTables** (Sorted Table Files). These SSTables are then merged and compacted to remove duplicates and optimize storage. For instance, LevelDB and RocksDB use this process to manage data [3]. Compaction strategies like **leveled** or **size-tiered** are employed to balance write and read performance [16].

3. **Write Amplification**:  
   Log-structured systems often involve multiple disk writes over time due to compaction and merging of SSTables. This is called **write amplification**, which can be particularly impactful on SSDs with limited write endurance [8].

4. **Performance Trade-offs**:  
   - **Advantages**: High write throughput due to sequential writes, efficient range queries when data is sorted [2].  
   - **Disadvantages**: Higher latency for read operations compared to B-trees, and potential performance bottlenecks during compaction [28].

5. **Comparison to B-Trees**:  
   Unlike B-trees, which allow in-place updates and are optimized for random access, log-structured engines prioritize sequential writes. They are better suited for write-heavy workloads but may struggle with complex queries requiring frequent disk seeks [26].

In summary, log-structured storage engines leverage append-only logs and periodic compaction to balance write performance and storage efficiency, making them popular in systems like Cassandra, HBase, and Lucene [10].

**Sources (8):**
- [1] Designing Data Intensive Applications by Martin Kleppmann — Part I. Foundations of Data Systems > Chapter 3. Storage and Retrieval > Data Structures That Power Your Database
- [2] Designing Data Intensive Applications by Martin Kleppmann — Part I. Foundations of Data Systems > Chapter 3. Storage and Retrieval > Data Structures That Power Your Database > B-Trees
- [3] Designing Data Intensive Applications by Martin Kleppmann — Part I. Foundations of Data Systems > Chapter 3. Storage and Retrieval > Data Structures That Power Your Database > SSTables and LSM-Trees
- [4] Designing Data Intensive Applications by Martin Kleppmann — Part I. Foundations of Data Systems > Chapter 3. Storage and Retrieval > Summary
- [5] Designing Data Intensive Applications by Martin Kleppmann — Part I. Foundations of Data Systems > Chapter 3. Storage and Retrieval > Summary
- [6] Designing Data Intensive Applications by Martin Kleppmann — Part I. Foundations of Data Systems > Chapter 3. Storage and Retrieval > Data Structures That Power Your Database > Other Indexing Structures
- [7] Designing Data Intensive Applications by Martin Kleppmann — Part I. Foundations of Data Systems > Chapter 3. Storage and Retrieval > Summary
- [8] Designing Data Intensive Applications by Martin Kleppmann — Part I. Foundations of Data Systems > Chapter 3. Storage and Retrieval > Data Structures That Power Your Database > Comparing B-Trees and LSM-Trees

---

## 2. What is the difference between a B-tree and an LSM-tree?

The differences between B-trees and LSM-trees lie in their design, performance characteristics, and use cases. Here's a structured comparison:

1. **Structure and Data Organization**:
   - **B-trees**: Divide data into fixed-size blocks (pages), typically 4 KB, and read/write one page at a time. They maintain sorted key-value pairs, enabling efficient range queries and random access [7]. 
   - **LSM-trees**: Use variable-size segments (e.g., SSTables) written sequentially. Data is organized into sorted files that are merged during compaction, allowing sequential writes and reducing disk seeks [1]. 

2. **Write Performance**:
   - **B-trees**: Writes are random and require updating pages, which can be slower, especially for large datasets. Writes are also duplicated (e.g., write-ahead logs) [1]. 
   - **LSM-trees**: Excel in write-heavy workloads due to sequential writes to SSTables. They sustain higher write throughput, partly because they avoid random writes and reduce write amplification (though this depends on configuration) [4]. 

3. **Read Performance**:
   - **B-trees**: Generally faster for reads, as they minimize disk seeks and maintain a compact structure. However, reads can be slower if pages are not sequentially laid out [1]. 
   - **LSM-trees**: Slower for reads due to needing to check multiple SSTables and compaction stages. Range queries are efficient because data is stored in sorted, sequential files [1]. 

4. **Disk I/O and Compaction**:
   - **B-trees**: Random writes can lead to fragmentation, leaving unused disk space. 
   - **LSM-trees**: Sequential writes reduce fragmentation and allow better compression, resulting in smaller files. Compaction merges SSTables, though it can temporarily impact read/write performance [4]. 

5. **Use Cases**:
   - **B-trees**: Ideal for read-heavy workloads with random access, such as traditional relational databases [7]. 
   - **LSM-trees**: Preferred for write-heavy applications (e.g., time-series data) and systems requiring high write throughput, like LevelDB and RocksDB [1][4]. 

In summary, B-trees prioritize read efficiency and random access, while LSM-trees optimize for write performance and sequential I/O. The choice depends on workload characteristics and system requirements [1][4].

**Sources (8):**
- [1] Designing Data Intensive Applications by Martin Kleppmann — Part I. Foundations of Data Systems > Chapter 3. Storage and Retrieval > Data Structures That Power Your Database > Comparing B-Trees and LSM-Trees
- [2] Designing Data Intensive Applications by Martin Kleppmann — Part I. Foundations of Data Systems > Chapter 3. Storage and Retrieval > Data Structures That Power Your Database > B-Trees
- [3] Designing Data Intensive Applications by Martin Kleppmann — Part I. Foundations of Data Systems > Chapter 3. Storage and Retrieval > Summary
- [4] Designing Data Intensive Applications by Martin Kleppmann — Part I. Foundations of Data Systems > Chapter 3. Storage and Retrieval > Data Structures That Power Your Database > Comparing B-Trees and LSM-Trees
- [5] Designing Data Intensive Applications by Martin Kleppmann — Part I. Foundations of Data Systems > Chapter 3. Storage and Retrieval > Data Structures That Power Your Database > SSTables and LSM-Trees
- [6] Designing Data Intensive Applications by Martin Kleppmann — Index
- [7] Designing Data Intensive Applications by Martin Kleppmann — Part I. Foundations of Data Systems > Chapter 3. Storage and Retrieval > Data Structures That Power Your Database > B-Trees
- [8] Designing Data Intensive Applications by Martin Kleppmann — Part I. Foundations of Data Systems > Chapter 3. Storage and Retrieval > Summary

---

## 3. What does ACID stand for in the context of databases?

ACID stands for **Atomicity, Consistency, Isolation, and Durability** in the context of databases. These properties define the characteristics of reliable transactions in database systems:

1. **Atomicity**: Ensures that a transaction is treated as a single, indivisible unit of work. If any part of the transaction fails, the entire transaction is rolled back to maintain data integrity [1].  
2. **Consistency**: Guarantees that a transaction brings the database from one valid state to another, preserving predefined invariants (e.g., financial balances in an accounting system) [1].  
3. **Isolation**: Ensures that concurrent transactions do not interfere with each other, appearing to execute serially to avoid issues like race conditions [1].  
4. **Durability**: Ensures that once a transaction is committed, its changes persist even in the event of system failures [1].  

The acronym was coined in 1983 by Theo Härder and Andreas Reuter to formalize fault-tolerance mechanisms in databases [1]. While implementations of ACID vary across systems, the term is widely used to describe transactional guarantees.

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

Eventual consistency is a consistency model in distributed systems where, after a period of time, all replicas will agree on the same value, even if there are temporary inconsistencies due to network delays or replication lag [1]. This model allows for weaker guarantees compared to stronger models like linearizability, meaning reads might not immediately reflect the latest writes [3]. For example, if a write occurs and a read happens shortly after, the read might not see the updated value if it is directed to a replica that hasn't yet received the write [4]. However, the system will eventually converge to a consistent state once all replicas are synchronized [7]. This model is often used in systems prioritizing availability and partition tolerance over strict consistency, as described in the CAP theorem.

**Sources (8):**
- [1] Designing Data Intensive Applications by Martin Kleppmann — Part II. Distributed Data > Chapter 9. Consistency and Consensus > Consistency Guarantees
- [2] Designing Data Intensive Applications by Martin Kleppmann — Part II. Distributed Data > Chapter 9. Consistency and Consensus > Ordering Guarantees
- [3] Designing Data Intensive Applications by Martin Kleppmann — Part II. Distributed Data > Chapter 9. Consistency and Consensus > Linearizability
- [4] Designing Data Intensive Applications by Martin Kleppmann — Part II. Distributed Data > Chapter 5. Replication > Problems with Replication Lag > Reading Your Own Writes
- [5] Designing Data Intensive Applications by Martin Kleppmann — Part II. Distributed Data > Chapter 5. Replication > Leaderless Replication > Detecting Concurrent Writes
- [6] Designing Data Intensive Applications by Martin Kleppmann — Index
- [7] Designing Data Intensive Applications by Martin Kleppmann — Index
- [8] Designing Data Intensive Applications by Martin Kleppmann — Part II. Distributed Data > Chapter 9. Consistency and Consensus > Summary

---

## 5. What is the CAP theorem?

The CAP theorem, introduced by Eric Brewer in 2000 [29], addresses the trade-offs in distributed systems when dealing with **network partitions** (unreliable networks). It states that in the event of a network partition, a system cannot simultaneously guarantee **Consistency** (linearizability), **Availability**, and **Partition tolerance**. Instead, it must prioritize two out of the three [1]. 

### Key Points:
1. **Consistency vs. Availability**:  
   - If a system requires **linearizability** (strong consistency), it may become unavailable during a network partition [1]. For example, if replicas cannot communicate, some clients may experience outages until the network is restored [1].  
   - If **availability** is prioritized, the system may sacrifice consistency (e.g., allowing stale reads) to remain operational during partitions [1].  

2. **Partition Tolerance as a Given**:  
   Network partitions are inevitable in distributed systems [3], so the theorem emphasizes that systems must **choose between consistency and availability** during such events. The phrasing "pick two out of three" is misleading because partition tolerance is not optional—it is a reality of distributed systems [3].  

3. **Limitations of the Theorem**:  
   - The formal CAP theorem [30] focuses only on **linearizability** (a specific consistency model) and **network partitions** (a specific fault type). It ignores other factors like network delays, dead nodes, or trade-offs beyond these [3].  
   - Many systems labeled "highly available" do not meet the theorem’s strict definition of availability [3].  

4. **Practical Implications**:  
   - Applications requiring linearizability (e.g., financial systems) must tolerate downtime during partitions [1].  
   - Systems prioritizing availability (e.g., web services) may use eventual consistency or relaxed models [1].  

5. **Criticism and Evolution**:  
   While historically influential, the CAP theorem is now considered **less practical** for modern system design due to its narrow scope [3]. More precise results have since superseded it [42].  

For further reading, see the formalization by Seth Gilbert and Nancy Lynch [30] and critiques by Martin Kleppmann [40].

**Sources (8):**
- [1] Designing Data Intensive Applications by Martin Kleppmann — Part II. Distributed Data > Chapter 9. Consistency and Consensus > Linearizability > The Cost of Linearizability
- [2] Designing Data Intensive Applications by Martin Kleppmann — Glossary
- [3] Designing Data Intensive Applications by Martin Kleppmann — Part II. Distributed Data > Chapter 9. Consistency and Consensus > Linearizability > The Cost of Linearizability
- [4] Designing Data Intensive Applications by Martin Kleppmann — Part II. Distributed Data > Chapter 9. Consistency and Consensus > Summary
- [5] Designing Data Intensive Applications by Martin Kleppmann — Part II. Distributed Data > Chapter 9. Consistency and Consensus > Ordering Guarantees
- [6] Designing Data Intensive Applications by Martin Kleppmann — Glossary
- [7] Designing Data Intensive Applications by Martin Kleppmann — Part II. Distributed Data > Chapter 9. Consistency and Consensus > Summary
- [8] Designing Data Intensive Applications by Martin Kleppmann — Index

---

## 6. What is leaderless replication?

Leaderless replication is a distributed database architecture where **any replica can directly accept writes from clients**, eliminating the need for a centralized leader to coordinate writes [1]. This approach contrasts with leader-based replication (e.g., master-slave models), where writes must go through a single leader node [6]. 

### Key Characteristics of Leaderless Replication:
1. **No Single Point of Failure**:  
   - Clients send writes to multiple replicas in parallel. If a node is down, writes are still accepted by other replicas, avoiding the need for failover [3]. For example, in a three-replica system, writes are considered successful if two out of three replicas acknowledge them [5].

2. **Quorum-Based Consistency**:  
   - Writes and reads require a quorum (e.g., `w` writes and `r` reads) to ensure data consistency. If a node is unavailable, the system tolerates partial failures but risks stale reads until the node rejoins and undergoes **read repair** [4]. 

3. **Eventual Consistency**:  
   - Leaderless systems typically provide **eventual consistency**, meaning reads may return stale values if some replicas lag. This is mitigated by **anti-entropy processes** (background data synchronization) and **read repair** (clients fix inconsistencies by overwriting stale values) [5]. 

4. **No Causal Ordering**:  
   - Unlike leader-based systems, leaderless replication does not enforce causal ordering of writes. This can lead to conflicts, as seen in systems like PostgreSQL BDR and Tungsten Replicator, which lack mechanisms to detect or resolve concurrent writes [3]. 

5. **Trade-offs**:  
   - **High Availability vs. Consistency**: Leaderless systems prioritize availability and low latency but may sacrifice linearizability (strict consistency). For example, Dynamo-style systems cannot guarantee linearizability without synchronous read repair, which reduces performance [7].  
   - **Stale Reads**: If a node is offline, reads from it may return outdated values. This is addressed by sending read requests to multiple replicas and using version vectors to detect and resolve conflicts [5].  

### Use Cases:  
Leaderless replication is ideal for applications that tolerate eventual consistency, such as **multi-datacenter deployments** or systems requiring high availability with occasional stale reads [7]. Examples include **Riak**, **Cassandra**, and **Voldemort**, which are inspired by Amazon’s Dynamo [1].  

### Challenges:  
- **Conflict Detection**: Poorly implemented conflict resolution can lead to data inconsistencies [3].  
- **Staleness Management**: Without proper metrics or anti-entropy processes, stale reads may persist [4].  

In summary, leaderless replication offers high availability and scalability but requires careful design to handle conflicts, staleness, and consistency guarantees [1][3][5].

**Sources (8):**
- [1] Designing Data Intensive Applications by Martin Kleppmann — Part II. Distributed Data > Chapter 5. Replication > Leaderless Replication
- [2] Designing Data Intensive Applications by Martin Kleppmann — Part II. Distributed Data > Chapter 5. Replication > Multi-Leader Replication
- [3] Designing Data Intensive Applications by Martin Kleppmann — Part II. Distributed Data > Chapter 5. Replication > Leaderless Replication > Writing to the Database When a Node Is Down
- [4] Designing Data Intensive Applications by Martin Kleppmann — Part II. Distributed Data > Chapter 5. Replication > Leaderless Replication > Sloppy Quorums and Hinted Handoff
- [5] Designing Data Intensive Applications by Martin Kleppmann — Part II. Distributed Data > Chapter 5. Replication > Leaderless Replication > Writing to the Database When a Node Is Down
- [6] Designing Data Intensive Applications by Martin Kleppmann — Part II. Distributed Data > Chapter 5. Replication > Leaders and Followers
- [7] Designing Data Intensive Applications by Martin Kleppmann — Part II. Distributed Data > Chapter 9. Consistency and Consensus > Linearizability > The Cost of Linearizability
- [8] Designing Data Intensive Applications by Martin Kleppmann — Part II. Distributed Data > Chapter 5. Replication > Leaders and Followers > Setting Up New Followers

---

## 7. What problems can arise from replication lag?

Replication lag can lead to several issues in distributed systems, including:

1. **Read-after-write inconsistency**: If a user submits data (e.g., a comment) and then reads it back from a follower replica, they might not see their data immediately due to replication delays. This creates the illusion that their write "disappeared," leading to frustration [2][3]. For example, a user might see their data briefly, then it vanishes until replication catches up [3].

2. **Stale reads**: Applications reading from asynchronous followers may encounter outdated data, resulting in inconsistent states. For instance, a query on a follower might return an older version of data compared to the leader, violating expectations of up-to-date results [2][3].

3. **Causality violations**: Replication lag can cause events to appear out of order. For example, a follower might receive a reply to a query before receiving the original query itself, creating the false impression that a user "predicted" a response [4][6]. This breaks the logical sequence of operations and confuses users or systems relying on temporal order.

4. **Eventual consistency challenges**: While systems eventually converge to consistency, the delay during lag can degrade user experiences. Applications must account for this by designing around weaker consistency guarantees (e.g., read-after-write consistency) or accepting potential temporary inconsistencies [2][7].

These issues highlight the trade-offs between availability, consistency, and performance in replicated systems. Solutions often involve mechanisms like read-after-write consistency, monotonic reads, or consistent prefix reads to mitigate the impact of replication lag [2][3][4][7].

**Sources (8):**
- [1] Designing Data Intensive Applications by Martin Kleppmann — Part II. Distributed Data > Chapter 5. Replication > Leaderless Replication
- [2] Designing Data Intensive Applications by Martin Kleppmann — Part II. Distributed Data > Chapter 5. Replication > Problems with Replication Lag > Solutions for Replication Lag
- [3] Designing Data Intensive Applications by Martin Kleppmann — Part II. Distributed Data > Chapter 5. Replication > Problems with Replication Lag > Reading Your Own Writes
- [4] Designing Data Intensive Applications by Martin Kleppmann — Part II. Distributed Data > Chapter 5. Replication > Problems with Replication Lag > Consistent Prefix Reads
- [5] Designing Data Intensive Applications by Martin Kleppmann — Part II. Distributed Data > Chapter 5. Replication > Multi-Leader Replication
- [6] Designing Data Intensive Applications by Martin Kleppmann — Part II. Distributed Data > Chapter 5. Replication > Multi-Leader Replication > Multi-Leader Replication Topologies
- [7] Designing Data Intensive Applications by Martin Kleppmann — Part II. Distributed Data > Chapter 5. Replication > Summary
- [8] Designing Data Intensive Applications by Martin Kleppmann — Glossary

---

## 8. What is the difference between optimistic and pessimistic concurrency control?

Optimistic and pessimistic concurrency control differ fundamentally in their approach to handling potential conflicts during transaction execution:

1. **Pessimistic Concurrency Control** (e.g., two-phase locking, 2PL):  
   - Assumes conflicts are likely and blocks transactions to prevent them. Transactions acquire locks on resources before proceeding, ensuring serializability by design.  
   - Example: If a transaction wants to write to a database, it must lock the resource, blocking other transactions until it completes. This avoids conflicts but introduces overhead and reduces concurrency [1].  
   - Trade-off: Higher performance penalties under low contention but ensures safety through blocking [1].

2. **Optimistic Concurrency Control** (e.g., Serializable Snapshot Isolation, SSI):  
   - Assumes conflicts are rare and allows transactions to proceed without locks. Conflicts are detected only at commit time, and transactions are aborted and retried if violations occur.  
   - Example: SSI uses snapshot isolation (reads from a consistent database snapshot) and detects write conflicts during commit. Only serializable transactions are allowed to commit [1].  
   - Trade-off: Lower overhead under low contention but may lead to retries and reduced throughput under high contention [2].

**Key Difference**:  
Pessimistic approaches block transactions to prevent conflicts, while optimistic approaches allow transactions to proceed and resolve conflicts later, trading predictability for scalability [1].

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

A **distributed transaction** is a transaction that spans multiple resources or systems, ensuring atomicity across all participants. It can be categorized into two main types:  

1. **Database-internal distributed transactions**: These occur within a single distributed database system (e.g., VoltDB or MySQL Cluster’s NDB engine), where all nodes run the same database software. They leverage optimizations specific to the system and can achieve good performance [1].  

2. **Heterogeneous distributed transactions**: These involve multiple disparate technologies (e.g., a message broker and a database) that must coordinate to ensure atomic commit. For example, a message from a queue can be acknowledged only if the corresponding database transaction succeeds, ensuring "exactly once" processing [1].  

### Key Characteristics and Challenges  
- **Atomicity**: All participants must commit or rollback together. This is often achieved via protocols like **two-phase commit (2PC)**, though it introduces performance overhead due to network round-trips and disk forcing (fsync) for crash recovery [1][8].  
- **Coordination**: Heterogeneous transactions require all systems to support the same protocol (e.g., XA transactions [76]), which can be difficult to achieve. If a participant fails, the transaction may need to be retried, risking duplicates unless side effects are rolled back [8].  
- **Performance Trade-offs**: Distributed transactions are often slower than single-node transactions (e.g., MySQL’s distributed transactions are 10x slower [87]). Many cloud services avoid them due to operational complexity and performance costs [1][4].  

### Example: XA Transactions  
The **XA standard** (eXtended Architecture) defines a protocol for two-phase commit across heterogeneous systems, such as databases and message brokers. It relies on a transaction coordinator to manage prepare/commit/abort phases, though it requires all participants to support XA [8].  

In summary, distributed transactions provide strong consistency guarantees but come with trade-offs in performance, complexity, and coordination requirements. Their use depends on the specific use case and system architecture [1][4][8].

**Sources (8):**
- [1] Designing Data Intensive Applications by Martin Kleppmann — Part II. Distributed Data > Chapter 9. Consistency and Consensus > Distributed Transactions and Consensus > Distributed Transactions in Practice
- [2] Designing Data Intensive Applications by Martin Kleppmann — Part III. Derived Data > Chapter 12. The Future of Data Systems > Aiming for Correctness > Enforcing Constraints
- [3] Designing Data Intensive Applications by Martin Kleppmann — Index
- [4] Designing Data Intensive Applications by Martin Kleppmann — Part II. Distributed Data > Chapter 7. Transactions
- [5] Designing Data Intensive Applications by Martin Kleppmann — Part II. Distributed Data
- [6] Designing Data Intensive Applications by Martin Kleppmann — Part II. Distributed Data > Chapter 9. Consistency and Consensus > Summary
- [7] Designing Data Intensive Applications by Martin Kleppmann — Table of Contents
- [8] Designing Data Intensive Applications by Martin Kleppmann — Part II. Distributed Data > Chapter 9. Consistency and Consensus > Distributed Transactions and Consensus > Distributed Transactions in Practice

---

## 10. What is the two-phase commit protocol?

The **two-phase commit (2PC)** protocol is a distributed coordination algorithm used to ensure atomicity across multiple database nodes in a distributed system. It operates in two distinct phases to guarantee that all participants either commit or abort a transaction consistently [2]. Here's a breakdown:

### **Phases of 2PC**
1. **Prepare Phase**  
   - The **coordinator** (a central component) sends a *prepare request* to all participants, asking if they can commit the transaction.  
   - Participants respond with "yes" (indicating readiness to commit) or "no" (indicating inability to commit).  
   - If any participant replies "no," the coordinator immediately aborts the transaction [3].

2. **Commit Phase**  
   - If all participants reply "yes," the coordinator sends a *commit request* to all participants.  
   - Participants then commit their local changes and respond with a "committed" message.  
   - If a participant fails during this phase, the coordinator retries the commit request [3].

### **Key Components**
- **Coordinator**: Manages the transaction, ensuring all participants agree to commit. It must persist its decisions (e.g., commit/abort) to a transaction log on disk to recover from failures [2].  
- **Participants**: Database nodes that execute the transaction and report their status to the coordinator.

### **Handling Failures**
- **Coordinator Failure**: If the coordinator crashes after the prepare phase but before sending the commit request, participants are left in an *in-doubt* state. They cannot proceed without the coordinator’s decision. Upon recovery, the coordinator reads its transaction log to determine the status of in-doubt transactions and resolves them accordingly [7].  
- **Participant Failure**: If a participant fails during the prepare phase, the coordinator aborts the transaction. If a participant fails during the commit phase, the coordinator retries the commit request [3].

### **Challenges**
- **Blocking Nature**: 2PC can become stuck if the coordinator fails during the commit phase, as participants cannot proceed without its decision. This is why it’s called a *blocking atomic commit protocol* [2].  
- **Unbounded Delays**: In networks with unbounded delays, 2PC may not guarantee atomicity, leading to alternatives like three-phase commit (3PC) [2].

### **Comparison to Other Concepts**
- **2PC vs. 2PL (Two-Phase Locking)**: While 2PC ensures atomicity in distributed transactions, **two-phase locking (2PL)** ensures serializable isolation in single-node systems. They are distinct concepts despite similar names [3].

In summary, 2PC ensures atomicity by splitting the commit process into two phases and relying on a coordinator to resolve conflicts, though it has limitations in handling failures and unbounded network delays [2][3].

**Sources (8):**
- [1] Designing Data Intensive Applications by Martin Kleppmann — Index
- [2] Designing Data Intensive Applications by Martin Kleppmann — Part II. Distributed Data > Chapter 9. Consistency and Consensus > Distributed Transactions and Consensus > Atomic Commit and Two-Phase Commit (2PC)
- [3] Designing Data Intensive Applications by Martin Kleppmann — Part II. Distributed Data > Chapter 9. Consistency and Consensus > Distributed Transactions and Consensus > Atomic Commit and Two-Phase Commit (2PC)
- [4] Designing Data Intensive Applications by Martin Kleppmann — Index
- [5] Designing Data Intensive Applications by Martin Kleppmann — Glossary
- [6] Designing Data Intensive Applications by Martin Kleppmann — Index
- [7] Designing Data Intensive Applications by Martin Kleppmann — Part II. Distributed Data > Chapter 9. Consistency and Consensus > Distributed Transactions and Consensus > Atomic Commit and Two-Phase Commit (2PC)
- [8] Designing Data Intensive Applications by Martin Kleppmann — Part II. Distributed Data > Chapter 7. Transactions > The Slippery Concept of a Transaction > Single-Object and Multi-Object Operations

---

## 11. What is linearizability?

Linearizability is a consistency model that ensures operations on a single data item (e.g., a register) appear to occur instantaneously and in a globally ordered sequence, even in distributed systems. It guarantees that once a write operation completes, all subsequent reads will return the updated value, ensuring **recency** [1]. This model treats the system as if it has a single, atomic copy of the data, with operations executed in a sequential order that reflects their actual timing [7]. 

Key aspects include:  
1. **Recency Guarantee**: A read operation always returns the most recent value written, even if the write has not yet completed. For example, if client A writes a value, client B’s subsequent read will see that value, regardless of network delays [3].  
2. **Causality Preservation**: Linearizability implies **causal consistency**, ensuring that operations are ordered such that if one event causally precedes another, its effects are visible in the same order [6].  
3. **Conflict Resolution**: Unlike serializability, linearizability does not inherently prevent issues like write skew unless additional measures (e.g., conflict materialization) are used [1].  

However, achieving linearizability can impact **performance and availability**, especially in geographically distributed systems, as it requires strict coordination to maintain consistency [8]. Systems like Dynamo-style quorums can approximate linearizability with reduced performance, while single-leader replication may sacrifice availability during network partitions [8].  

In summary, linearizability ensures a strong, intuitive consistency model but comes with trade-offs in scalability and fault tolerance [6].

**Sources (8):**
- [1] Designing Data Intensive Applications by Martin Kleppmann — Part II. Distributed Data > Chapter 9. Consistency and Consensus > Linearizability > What Makes a System Linearizable?
- [2] Designing Data Intensive Applications by Martin Kleppmann — Part II. Distributed Data > Chapter 9. Consistency and Consensus > Linearizability > Relying on Linearizability
- [3] Designing Data Intensive Applications by Martin Kleppmann — Part II. Distributed Data > Chapter 9. Consistency and Consensus > Linearizability > What Makes a System Linearizable?
- [4] Designing Data Intensive Applications by Martin Kleppmann — Part II. Distributed Data > Chapter 9. Consistency and Consensus > Linearizability > What Makes a System Linearizable?
- [5] Designing Data Intensive Applications by Martin Kleppmann — Part II. Distributed Data > Chapter 9. Consistency and Consensus > Linearizability > What Makes a System Linearizable?
- [6] Designing Data Intensive Applications by Martin Kleppmann — Part II. Distributed Data > Chapter 9. Consistency and Consensus > Ordering Guarantees > Ordering and Causality
- [7] Designing Data Intensive Applications by Martin Kleppmann — Part II. Distributed Data > Chapter 9. Consistency and Consensus > Linearizability
- [8] Designing Data Intensive Applications by Martin Kleppmann — Part II. Distributed Data > Chapter 9. Consistency and Consensus > Linearizability > The Cost of Linearizability

---

## 12. What is the difference between REST and RPC?

REST and RPC differ fundamentally in their design philosophies and implementation approaches. Here's a breakdown of their key distinctions:

1. **Design Philosophy**:  
   - **REST** is a design philosophy built on HTTP principles, emphasizing stateless interactions, simple data formats (e.g., JSON), and leveraging HTTP methods (GET, POST, etc.) for resource manipulation [34, 35]. It avoids hiding the network layer, making it transparent that communication occurs over HTTP [1].  
   - **RPC** (Remote Procedure Call) aims to abstract network communication so that a client can invoke a remote procedure as if it were a local function. This abstraction (called *location transparency*) can lead to challenges like handling network failures or latency, as RPC frameworks must manage data translation between languages and systems [42].

2. **Data Encoding and Compatibility**:  
   - **REST** typically uses JSON or XML for data exchange, with backward/forward compatibility managed through versioning (e.g., URL paths or headers) [48]. It is flexible for experimentation and debugging, as tools like `curl` can interact with RESTful APIs directly [1].  
   - **RPC** frameworks (e.g., gRPC, Thrift) often use binary encodings (e.g., Protocol Buffers) for efficiency, but they require stricter compatibility rules between client and server versions. For example, Thrift and Avro RPC rely on their encoding formats’ compatibility rules, while SOAP’s XML-based approach can face pitfalls during evolution [47].

3. **Use Cases and Ecosystem**:  
   - **REST** is prevalent for public APIs and cross-organizational integration due to its simplicity and broad language support [36]. It benefits from a vast ecosystem of tools (e.g., load balancers, caches) and is often associated with microservices [31].  
   - **RPC** is more common within organizations for internal service communication, where performance and tight integration are prioritized. Frameworks like gRPC support advanced features like streaming and asynchronous calls via *futures* [45], while others (e.g., Finagle) use *promises* for handling failures [1].

4. **Error Handling and Latency**:  
   - **REST** treats network requests as inherently unreliable, requiring clients to handle retries, timeouts, and idempotency [44].  
   - **RPC** frameworks often abstract these concerns but may still struggle with latency variability and network unreliability, as they mimic local function calls [42].

In summary, REST prioritizes simplicity, flexibility, and broad accessibility, while RPC focuses on efficient, abstracted remote procedure execution, often within controlled environments. Both have evolved to address modern challenges, with REST favoring human-readable formats and RPC emphasizing performance and language interoperability [1, 34, 42].

**Sources (8):**
- [1] Designing Data Intensive Applications by Martin Kleppmann — Part I. Foundations of Data Systems > Chapter 4. Encoding and Evolution > Modes of Dataflow > Dataflow Through Services: REST and RPC
- [2] Designing Data Intensive Applications by Martin Kleppmann — Part I. Foundations of Data Systems > Chapter 4. Encoding and Evolution > Modes of Dataflow > Message-Passing Dataflow
- [3] Designing Data Intensive Applications by Martin Kleppmann — Part I. Foundations of Data Systems > Chapter 4. Encoding and Evolution > Modes of Dataflow > Dataflow Through Services: REST and RPC
- [4] Designing Data Intensive Applications by Martin Kleppmann — Part I. Foundations of Data Systems > Chapter 4. Encoding and Evolution > Modes of Dataflow > Dataflow Through Services: REST and RPC
- [5] Designing Data Intensive Applications by Martin Kleppmann — Part I. Foundations of Data Systems > Chapter 4. Encoding and Evolution > Modes of Dataflow > Dataflow Through Services: REST and RPC
- [6] Designing Data Intensive Applications by Martin Kleppmann — Part I. Foundations of Data Systems > Chapter 4. Encoding and Evolution > Summary
- [7] Designing Data Intensive Applications by Martin Kleppmann — Part I. Foundations of Data Systems > Chapter 4. Encoding and Evolution > Modes of Dataflow > Dataflow Through Services: REST and RPC
- [8] Designing Data Intensive Applications by Martin Kleppmann — Part I. Foundations of Data Systems > Chapter 4. Encoding and Evolution > Summary

---

## 13. What is a message broker used for?

A **message broker** is used to facilitate **reliable, asynchronous communication** between processes or systems by acting as an intermediary that stores and forwards messages. Its primary purposes include:  

1. **Decoupling producers and consumers**:  
   - It allows senders (producers) and receivers (consumers) to operate independently, without direct knowledge of each other’s locations or availability [1].  
   - This decoupling improves system reliability and scalability, especially in distributed environments [1].  

2. **Ensuring reliability and durability**:  
   - Message brokers buffer messages if recipients are unavailable or overloaded, preventing data loss [1].  
   - They support **redelivery** of messages in case of consumer failures, ensuring no data is lost [1].  
   - Some brokers persist messages to disk to survive broker crashes [2].  

3. **Supporting multiple consumers**:  
   - Brokers enable **load balancing** (messages distributed among consumers) and **fan-out** (messages sent to all consumers simultaneously) [3].  
   - This is critical for parallel processing and independent event handling [3].  

4. **Asynchronous communication**:  
   - Producers do not wait for confirmation of delivery, sending messages and forgetting about them [1].  
   - Consumers process messages at their own pace, with delivery happening asynchronously [2].  

5. **Stream processing and log-based systems**:  
   - Modern brokers like **Apache Kafka** or **Amazon Kinesis Streams** use log-based architectures to store messages persistently, enabling features like **message replay** and **low-latency event streaming** [4].  
   - These systems handle slow consumers by buffering messages and allow replaying historical data for analysis or debugging [4].  

6. **Replacing direct RPC/messaging**:  
   - Unlike direct RPC, message brokers avoid exposing network details (e.g., IP addresses) and handle dynamic environments like cloud deployments [1].  
   - They are often preferred over traditional messaging systems for their scalability and fault tolerance [2].  

In summary, message brokers are essential for **reliable, scalable, and decoupled communication** in distributed systems, with applications in stream processing, event-driven architectures, and real-time data pipelines [1][2][4].

**Sources (8):**
- [1] Designing Data Intensive Applications by Martin Kleppmann — Part I. Foundations of Data Systems > Chapter 4. Encoding and Evolution > Modes of Dataflow > Message-Passing Dataflow
- [2] Designing Data Intensive Applications by Martin Kleppmann — Part III. Derived Data > Chapter 11. Stream Processing > Transmitting Event Streams > Messaging Systems
- [3] Designing Data Intensive Applications by Martin Kleppmann — Part III. Derived Data > Chapter 11. Stream Processing > Transmitting Event Streams > Messaging Systems
- [4] Designing Data Intensive Applications by Martin Kleppmann — Part III. Derived Data > Chapter 11. Stream Processing > Databases and Streams
- [5] Designing Data Intensive Applications by Martin Kleppmann — Index
- [6] Designing Data Intensive Applications by Martin Kleppmann — Part III. Derived Data > Chapter 11. Stream Processing > Transmitting Event Streams > Messaging Systems
- [7] Designing Data Intensive Applications by Martin Kleppmann — Part III. Derived Data > Chapter 11. Stream Processing > Summary
- [8] Designing Data Intensive Applications by Martin Kleppmann — Part III. Derived Data > Chapter 11. Stream Processing > Transmitting Event Streams > Partitioned Logs

---

## 14. What is the actor model in the context of distributed systems?

The actor model in distributed systems is a programming model for concurrency that extends its single-process capabilities to multiple nodes. In this model, actors—entities that encapsulate logic and state—communicate via asynchronous message passing. Key characteristics include:  
- **Message-passing mechanism**: Messages are sent asynchronously between actors, regardless of whether they reside on the same node or different nodes. If actors are on separate nodes, messages are encoded into byte sequences, transmitted over the network, and decoded on the receiving end [1].  
- **Location transparency**: The actor model inherently handles network latency and potential message loss, making it more robust than RPC (Remote Procedure Call) models, which often assume reliable communication [1].  
- **Decentralized scheduling**: Each actor is scheduled independently, avoiding thread management complexities like race conditions or deadlocks [1].  
- **Challenges**: Distributed actor frameworks must address forward and backward compatibility when upgrading nodes, as messages may travel between old and new versions [1].  

This model is foundational for systems requiring scalability and fault tolerance, such as distributed actor frameworks like Akka or Orleans [1].

**Sources (8):**
- [1] Designing Data Intensive Applications by Martin Kleppmann — Part I. Foundations of Data Systems > Chapter 4. Encoding and Evolution > Modes of Dataflow > Message-Passing Dataflow
- [2] Designing Data Intensive Applications by Martin Kleppmann — Part II. Distributed Data > Chapter 8. The Trouble with Distributed Systems > Knowledge, Truth, and Lies > System Model and Reality
- [3] Designing Data Intensive Applications by Martin Kleppmann — Part I. Foundations of Data Systems > Chapter 4. Encoding and Evolution > Summary
- [4] Designing Data Intensive Applications by Martin Kleppmann — Part II. Distributed Data > Chapter 5. Replication > Leaderless Replication
- [5] Designing Data Intensive Applications by Martin Kleppmann — Glossary
- [6] Designing Data Intensive Applications by Martin Kleppmann — Part II. Distributed Data > Chapter 8. The Trouble with Distributed Systems > Knowledge, Truth, and Lies
- [7] Designing Data Intensive Applications by Martin Kleppmann — Part II. Distributed Data > Chapter 8. The Trouble with Distributed Systems > Summary
- [8] Designing Data Intensive Applications by Martin Kleppmann — Index

---

## 15. What is data partitioning (sharding)?

Data partitioning, also known as sharding, is the process of dividing a large dataset into smaller, more manageable parts called partitions or shards. Each partition is stored on a separate node in a distributed system, enabling scalability by distributing data and query loads across multiple machines [1]. This approach avoids "hot spots" (nodes with disproportionately high load) and allows systems to handle larger datasets or higher query throughput than a single machine could manage [1].

Key aspects of partitioning include:
1. **Partitioning Strategies**: Data can be partitioned by key range (e.g., assigning contiguous key ranges to partitions, like volumes in an encyclopedia) [6], or using hashing (e.g., consistent hashing for even distribution) [7]. The choice depends on data characteristics and access patterns.
2. **Replication**: Partitions are often replicated across multiple nodes for fault tolerance, ensuring data availability even if a node fails [5].
3. **Routing**: Systems use routing tiers (e.g., ZooKeeper, Moxi) or gossip protocols (e.g., Cassandra, Riak) to direct requests to the correct partition [8].
4. **Scalability**: Partitioning enables shared-nothing architectures, where nodes operate independently, scaling horizontally by adding more machines [5].

Different systems use varying terminology (e.g., "shard" in MongoDB, "tablet" in Bigtable), but the core concept of partitioning remains consistent across distributed databases and datastores [1].

**Sources (8):**
- [1] Designing Data Intensive Applications by Martin Kleppmann — Part II. Distributed Data > Chapter 6. Partitioning
- [2] Designing Data Intensive Applications by Martin Kleppmann — Part II. Distributed Data > Chapter 6. Partitioning > Partitioning and Secondary Indexes
- [3] Designing Data Intensive Applications by Martin Kleppmann — Part II. Distributed Data > Chapter 6. Partitioning > Request Routing > Parallel Query Execution
- [4] Designing Data Intensive Applications by Martin Kleppmann — Part II. Distributed Data > Chapter 6. Partitioning > Summary
- [5] Designing Data Intensive Applications by Martin Kleppmann — Part II. Distributed Data > Chapter 6. Partitioning > Partitioning and Replication
- [6] Designing Data Intensive Applications by Martin Kleppmann — Part II. Distributed Data > Chapter 6. Partitioning > Partitioning of Key-Value Data > Partitioning by Key Range
- [7] Designing Data Intensive Applications by Martin Kleppmann — Part II. Distributed Data > Chapter 6. Partitioning > Summary
- [8] Designing Data Intensive Applications by Martin Kleppmann — Part II. Distributed Data > Chapter 6. Partitioning > Summary

---

## 16. How does consistent hashing help with partitioning?

Consistent hashing helps with partitioning by using randomly chosen partition boundaries to distribute data across nodes without requiring centralized control or distributed consensus [1]. This approach minimizes the need for full data redistribution when nodes are added or removed, as only a subset of data needs to be moved [8]. For example, when a new node joins, it randomly takes ownership of a portion of existing partitions, maintaining load balance without rehashing all keys [23, 27, 28]. 

However, consistent hashing sacrifices the ability to perform efficient range queries, as keys are scattered across partitions rather than ordered [1]. This trade-off makes it suitable for systems prioritizing scalability over range-based operations, such as distributed caches. Despite its advantages, it is rarely used in databases due to rebalancing inefficiencies [1]. 

In summary, consistent hashing simplifies dynamic scaling but introduces challenges for range queries and rebalancing, as noted in the sources [1][7][8].

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

1. **Partitioning vs. Index Mapping**:  
   Secondary indexes do not align neatly with partition boundaries. For example, if a database is partitioned by document ID (e.g., partition 0 contains IDs 0–499), a secondary index on "color" might spread entries across multiple partitions (e.g., red cars could exist in partition 0 and partition 1). This requires **scatter/gather** queries, where the system must query all partitions and combine results, increasing read latency [1][3].  

2. **Update Complexity**:  
   When updating a record, the system must ensure the secondary index remains consistent. For **document-partitioned indexes** (local indexes), updates only affect the partition containing the document ID, but for **term-partitioned indexes** (global indexes), updates may require modifying multiple partitions (e.g., all partitions containing "color:red") [1][3]. This increases the risk of inconsistencies if not handled carefully.  

3. **Asynchronous Updates**:  
   In distributed systems, secondary indexes are often updated asynchronously. For instance, Amazon DynamoDB’s global secondary indexes may take milliseconds to propagate changes, leading to potential stale reads if not managed properly [5].  

4. **Rebalancing Challenges**:  
   When partitions are rebalanced (e.g., due to node additions/removals), secondary indexes must be updated to reflect new data distribution. This requires coordination across partitions and can introduce overhead [1][5].  

5. **Consistency Trade-offs**:  
   Maintaining global secondary indexes (term-based) requires distributed transactions or eventual consistency, which are complex to implement. For example, writing to a term-partitioned index might involve updating multiple partitions, risking partial failures or data skew [1][5].  

In summary, secondary indexes in partitioned databases are harder to maintain due to the need for cross-partition coordination, asynchronous updates, and ensuring consistency during rebalancing. These challenges are why some systems (e.g., HBase) avoid secondary indexes, while others (e.g., Elasticsearch) optimize for them [1][3][5].

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

The primary difference between batch processing and stream processing lies in the nature of their input data and processing timing. Batch processing handles **bounded datasets** of known, finite size, where the process completes once all input is received [3]. In contrast, stream processing operates on **unbounded datasets** that arrive incrementally over time, requiring continuous or near-real-time processing [3]. 

Additionally, batch processing typically uses fixed time intervals (e.g., daily or hourly chunks) to process data, while stream processing handles data as it arrives, enabling lower latency for real-time applications [4]. 

Functionally, batch processing emphasizes deterministic, pure functions with no side effects, whereas stream processing extends this by managing fault-tolerant state, allowing for operations like joins and aggregations across continuously arriving data [3]. 

These distinctions are further amplified by differences in implementation, such as Spark’s microbatching approach versus Flink’s unified stream and batch processing model [5].

**Sources (8):**
- [1] Designing Data Intensive Applications by Martin Kleppmann — Part III. Derived Data > Chapter 10. Batch Processing > Beyond MapReduce
- [2] Designing Data Intensive Applications by Martin Kleppmann — Part III. Derived Data > Chapter 10. Batch Processing > Batch Processing with Unix Tools
- [3] Designing Data Intensive Applications by Martin Kleppmann — Part III. Derived Data > Chapter 12. The Future of Data Systems > Data Integration > Batch and Stream Processing
- [4] Designing Data Intensive Applications by Martin Kleppmann — Part III. Derived Data > Chapter 11. Stream Processing
- [5] Designing Data Intensive Applications by Martin Kleppmann — Part III. Derived Data > Chapter 12. The Future of Data Systems > Data Integration > Batch and Stream Processing
- [6] Designing Data Intensive Applications by Martin Kleppmann — Part III. Derived Data > Chapter 11. Stream Processing > Processing Streams
- [7] Designing Data Intensive Applications by Martin Kleppmann — Part III. Derived Data > Chapter 10. Batch Processing
- [8] Designing Data Intensive Applications by Martin Kleppmann — Part III. Derived Data > Chapter 11. Stream Processing > Summary

---

## 19. What is exactly-once semantics in stream processing?

Exactly-once semantics in stream processing ensures that each record is processed exactly once, even in the presence of failures, avoiding duplicates or missed records. This is achieved through mechanisms like **checkpointing**, **idempotence**, and **transactional messaging**. 

1. **Checkpointing and Microbatching**:  
   Stream processors like Apache Flink periodically generate checkpoints of the system state, allowing restarts from the last checkpoint if a failure occurs. This ensures that outputs are not duplicated, though once data leaves the processor (e.g., written to a database), the framework cannot discard it if a failure happens afterward. This requires coordination with external systems to prevent duplicates [2][92].

2. **Idempotence**:  
   Operations are designed to be idempotent, meaning repeated processing of the same record yields the same result. For example, writing a value to a database with a unique identifier (like a Kafka message offset) ensures updates are applied only once, even if retried [97].

3. **Transactional Messaging**:  
   Systems like Apache Kafka and Apache Flink support transactional messaging, ensuring that messages are delivered exactly once. This involves atomic commits that guarantee all side effects (e.g., database writes, acknowledgments) are applied together or not at all [95][96].

4. **Atomic Commit**:  
   Similar to distributed transactions, atomic commit ensures that all outputs and side effects of processing an event are either fully applied or rolled back. This avoids inconsistencies if a task fails [90].

Challenges arise when outputs leave the stream processor (e.g., to a database), as the framework cannot control external systems. Thus, idempotence or transactional guarantees must be enforced externally [2][97].

**Sources (8):**
- [1] Designing Data Intensive Applications by Martin Kleppmann — Part III. Derived Data > Chapter 11. Stream Processing > Summary
- [2] Designing Data Intensive Applications by Martin Kleppmann — Part III. Derived Data > Chapter 11. Stream Processing > Processing Streams > Fault Tolerance
- [3] Designing Data Intensive Applications by Martin Kleppmann — Part III. Derived Data > Chapter 11. Stream Processing > Summary
- [4] Designing Data Intensive Applications by Martin Kleppmann — Part III. Derived Data > Chapter 11. Stream Processing > Processing Streams > Fault Tolerance
- [5] Designing Data Intensive Applications by Martin Kleppmann — Part III. Derived Data > Chapter 11. Stream Processing > Processing Streams > Fault Tolerance
- [6] Designing Data Intensive Applications by Martin Kleppmann — Part III. Derived Data > Chapter 11. Stream Processing > Summary
- [7] Designing Data Intensive Applications by Martin Kleppmann — Index
- [8] Designing Data Intensive Applications by Martin Kleppmann — Part III. Derived Data > Chapter 12. The Future of Data Systems > Data Integration > Batch and Stream Processing

---

## 20. What ethical considerations does the book raise about data systems?

The book raises several ethical considerations regarding data systems, emphasizing the responsibility of engineers and developers to consider the societal impact of their work. Key points include:  

1. **Impact on Individuals**: Data systems often involve sensitive information about people, such as behavior, identity, and interests. The book stresses that such data must be treated with humanity and respect, as decisions made by systems (e.g., predictive analytics) can directly affect individuals’ lives, such as in criminal justice, finance, or hiring [2].  

2. **Ethical Use of Predictive Analytics**: While predictive analytics can be beneficial (e.g., forecasting disease spread), its misuse—such as predicting recidivism or loan defaults—raises concerns about fairness, bias, and potential harm to individuals [2]. The book warns against cavalier attitudes toward privacy and negative consequences, urging engineers to prioritize ethical considerations over purely technical outcomes.  

3. **Accountability and Transparency**: The text highlights the need for accountability in algorithmic decision-making, referencing EU regulations that grant individuals a “right to explanation” for automated decisions [4]. It also cites works like Cathy O’Neil’s *Weapons of Math Destruction* to illustrate how biased algorithms can exacerbate inequality [4].  

4. **Engineering Ethics**: The book underscores the importance of adhering to ethical guidelines, such as the ACM’s Software Engineering Code of Ethics [2], even though these are often not rigorously applied in practice. It argues that engineers must actively engage with ethical questions rather than ignoring them [2].  

5. **Societal Consequences**: The author warns that technology is not inherently good or bad; its impact depends on how it is used. Engineers must consider both intended and unintended consequences, recognizing that their work shapes the world in profound ways [2].  

These considerations are tied to broader discussions about privacy, fairness, and the moral responsibilities of technologists, as detailed in cited works like *Data and Goliath* [96] and *Thinking in Systems* [92].

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
