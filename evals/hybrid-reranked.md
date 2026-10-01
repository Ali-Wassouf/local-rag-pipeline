# Phase 4 eval — hybrid + cross-encoder reranking (full Phase 4 pipeline)

Same 20 questions as evals/baseline.md, same project (Systems Books, real ~600-page DDIA book), re-run against this configuration only, per docs/build-phases.md Phase 4's requirement to measure hybrid-vs-vector and reranked-vs-unreranked *separately*.

---

## 1. What is a log-structured storage engine?

A log-structured storage engine is a type of storage system that organizes data as an **append-only sequence of records** (a log), which is periodically merged and compacted to manage storage efficiency. This approach is central to **LSM (Log-Structured Merge)-trees**, which are used in systems like LevelDB, RocksDB, and Cassandra. Key characteristics include:

1. **Append-Only Logs**: Data is written sequentially to the log, avoiding random disk access. For example, in log-structured filesystems, writes are optimized for sequential I/O [1].  
2. **Compaction**: Older, sorted segments (SSTables) are merged and compacted in the background to remove obsolete data and maintain performance. Strategies like **size-tiered** (merging smaller SSTables into larger ones) and **leveled** (splitting key ranges into levels) are used [1].  
3. **High Write Throughput**: Sequential writes on disk (via SSDs or HDDs) enable high write performance, as opposed to the random writes of traditional B-trees [1].  
4. **Bloom Filters**: These are used to optimize lookup performance by quickly identifying non-existent keys and avoiding unnecessary disk reads [1].  

This design contrasts with B-trees, which prioritize random read/write efficiency. Log-structured engines excel in scenarios with high write loads, such as time-series data or event streams [1][6].  

**Sources**: [1], [6]

**Sources (8):**
- [1] Designing Data Intensive Applications by Martin Kleppmann — Part I. Foundations of Data Systems > Chapter 3. Storage and Retrieval > Data Structures That Power Your Database > B-Trees
- [2] Designing Data Intensive Applications by Martin Kleppmann — Part I. Foundations of Data Systems > Chapter 3. Storage and Retrieval > Data Structures That Power Your Database
- [3] Designing Data Intensive Applications by Martin Kleppmann — Part III. Derived Data > Chapter 11. Stream Processing > Transmitting Event Streams > Partitioned Logs
- [4] Designing Data Intensive Applications by Martin Kleppmann — Part I. Foundations of Data Systems > Chapter 3. Storage and Retrieval > Summary
- [5] Designing Data Intensive Applications by Martin Kleppmann — Part III. Derived Data > Chapter 11. Stream Processing > Summary
- [6] Designing Data Intensive Applications by Martin Kleppmann — Part II. Distributed Data > Chapter 5. Replication > Leaders and Followers > Implementation of Replication Logs
- [7] Designing Data Intensive Applications by Martin Kleppmann — Index
- [8] Designing Data Intensive Applications by Martin Kleppmann — Index

---

## 2. What is the difference between a B-tree and an LSM-tree?

The difference between a **B-tree** and an **LSM-tree** lies in their design, performance characteristics, and trade-offs for storage systems:

1. **Write vs. Read Performance**:  
   - **B-trees** are optimized for **read-heavy workloads** and provide faster read operations due to their balanced structure [1]. However, writes are slower because every update requires modifying the tree and maintaining balance (e.g., splitting pages) [5].  
   - **LSM-trees** (Log-Structured Merge Trees) excel at **write-heavy workloads**. They achieve higher write throughput by sequentially writing data to disk (via SSTables) rather than random writes, which is faster on magnetic disks [3]. However, reads are slower because they require checking multiple SSTables and merging results during compaction [1].

2. **Write Amplification**:  
   - B-trees have **lower write amplification** since writes are localized to specific pages. However, they still involve writing to the write-ahead log (WAL) and tree pages [1].  
   - LSM-trees suffer from **higher write amplification** due to repeated compaction and merging of SSTables. This results in multiple disk writes per original write, which can degrade performance on SSDs (due to limited overwrite cycles) [3].

3. **Compaction and Disk Layout**:  
   - B-trees maintain a **balanced tree structure**, requiring frequent page splits and updates. This can lead to fragmentation and increased disk space usage [5].  
   - LSM-trees **rewrite data during compaction**, merging smaller SSTables into larger ones. This process reduces fragmentation and allows sequential disk writes, improving storage efficiency [3]. However, compaction can temporarily impact read performance [1].

4. **Use Cases**:  
   - **B-trees** are ideal for applications prioritizing **low-latency reads** (e.g., relational databases) [5].  
   - **LSM-trees** are better suited for **high-throughput writes** (e.g., time-series databases, NoSQL systems) [3].  

5. **Storage Overheads**:  
   - B-trees may leave unused disk space due to fragmentation [3].  
   - LSM-trees generally produce **smaller files** on disk due to periodic compaction and compression [3].  

In summary, **B-trees** prioritize read efficiency and balanced structures, while **LSM-trees** optimize for write throughput and sequential I/O. The choice depends on workload characteristics, with benchmarks often being workload-specific [1].

**Sources (8):**
- [1] Designing Data Intensive Applications by Martin Kleppmann — Part I. Foundations of Data Systems > Chapter 3. Storage and Retrieval > Data Structures That Power Your Database > Comparing B-Trees and LSM-Trees
- [2] Designing Data Intensive Applications by Martin Kleppmann — Index
- [3] Designing Data Intensive Applications by Martin Kleppmann — Part I. Foundations of Data Systems > Chapter 3. Storage and Retrieval > Data Structures That Power Your Database > Comparing B-Trees and LSM-Trees
- [4] Designing Data Intensive Applications by Martin Kleppmann — Index
- [5] Designing Data Intensive Applications by Martin Kleppmann — Part I. Foundations of Data Systems > Chapter 3. Storage and Retrieval > Data Structures That Power Your Database > B-Trees
- [6] Designing Data Intensive Applications by Martin Kleppmann — Index
- [7] Designing Data Intensive Applications by Martin Kleppmann — Part I. Foundations of Data Systems > Chapter 3. Storage and Retrieval > Data Structures That Power Your Database > Other Indexing Structures
- [8] Designing Data Intensive Applications by Martin Kleppmann — Index

---

## 3. What does ACID stand for in the context of databases?

ACID stands for **Atomicity, Consistency, Isolation, and Durability** in the context of databases. These properties define the characteristics of reliable transactions in database systems:

1. **Atomicity**: Ensures that a transaction is treated as a single, indivisible unit of work. If any part of the transaction fails, the entire transaction is rolled back to maintain data integrity [1].  
2. **Consistency**: Guarantees that a transaction brings the database from one valid state to another, preserving application-specific invariants (e.g., balanced credits/debits in an accounting system) [3].  
3. **Isolation**: Ensures that concurrent transactions do not interfere with each other, appearing to execute serially to avoid issues like race conditions [1].  
4. **Durability**: Ensures that once a transaction is committed, its changes are permanently saved, even in the event of system failures [1].  

While ACID is often marketed as a standard for transactional systems, its implementation varies across databases, and the term has become more of a marketing label than a strict technical definition [1]. Systems that prioritize scalability over strict ACID compliance often adopt the **BASE** model (Basically Available, Soft state, Eventual consistency) instead [1].

**Sources (8):**
- [1] Designing Data Intensive Applications by Martin Kleppmann — Part II. Distributed Data > Chapter 7. Transactions > The Slippery Concept of a Transaction > The Meaning of ACID
- [2] Designing Data Intensive Applications by Martin Kleppmann — Index
- [3] Designing Data Intensive Applications by Martin Kleppmann — Part II. Distributed Data > Chapter 7. Transactions > The Slippery Concept of a Transaction > The Meaning of ACID
- [4] Designing Data Intensive Applications by Martin Kleppmann — Part II. Distributed Data > Chapter 7. Transactions > The Slippery Concept of a Transaction > The Meaning of ACID
- [5] Designing Data Intensive Applications by Martin Kleppmann — Index
- [6] Designing Data Intensive Applications by Martin Kleppmann — Preface
- [7] Designing Data Intensive Applications by Martin Kleppmann — Index
- [8] Designing Data Intensive Applications by Martin Kleppmann — Index

---

## 4. What is eventual consistency?

Eventual consistency is a consistency model in distributed systems where, after a period of time, all replicas will reflect the same data, even if there is a temporary delay in propagation. This model is used in systems with asynchronous replication, where writes are not immediately reflected across all replicas. 

When a write occurs, the leader processes it, but followers (replicas) may lag behind due to network delays or system load. This lag can cause temporary inconsistencies if reads are performed on stale replicas. However, the system guarantees that, given enough time, all replicas will eventually synchronize and become consistent [1]. 

The term "eventual consistency" is a **liveness property** because it ensures that consistency will eventually be achieved, even if it is not immediate. In contrast, **safety properties** (like uniqueness or monotonicity) must hold at all times [3]. 

A classic example of this is when a user writes data and then immediately reads from a replica that hasn't yet received the update. The user might see outdated data, creating an apparent inconsistency. To address this, systems often implement **read-after-write consistency**, ensuring the user sees their own updates immediately [1]. 

While eventual consistency is common in NoSQL databases, it also applies to asynchronously replicated relational databases [1]. However, it is distinct from **integrity**, which ensures data correctness (e.g., avoiding errors like missing transactions) and is often more critical for applications [4]. 

In summary, eventual consistency trades immediate consistency for scalability and availability, relying on the system eventually resolving discrepancies. It is a deliberate design choice to handle the challenges of distributed data replication [1][3].

**Sources (8):**
- [1] Designing Data Intensive Applications by Martin Kleppmann — Part II. Distributed Data > Chapter 5. Replication > Problems with Replication Lag > Reading Your Own Writes
- [2] Designing Data Intensive Applications by Martin Kleppmann — Preface
- [3] Designing Data Intensive Applications by Martin Kleppmann — Part II. Distributed Data > Chapter 8. The Trouble with Distributed Systems > Knowledge, Truth, and Lies > System Model and Reality
- [4] Designing Data Intensive Applications by Martin Kleppmann — Part III. Derived Data > Chapter 12. The Future of Data Systems > Aiming for Correctness > Timeliness and Integrity
- [5] Designing Data Intensive Applications by Martin Kleppmann — Part II. Distributed Data > Chapter 9. Consistency and Consensus > Consistency Guarantees
- [6] Designing Data Intensive Applications by Martin Kleppmann — Part II. Distributed Data > Chapter 5. Replication > Problems with Replication Lag > Solutions for Replication Lag
- [7] Designing Data Intensive Applications by Martin Kleppmann — Part II. Distributed Data > Chapter 5. Replication > Leaders and Followers
- [8] Designing Data Intensive Applications by Martin Kleppmann — Part II. Distributed Data > Chapter 5. Replication > Leaderless Replication > Sloppy Quorums and Hinted Handoff

---

## 5. What is the CAP theorem?

The CAP theorem, introduced by Eric Brewer in 2000, addresses the trade-offs in distributed systems when dealing with **consistency (linearizability)**, **availability**, and **partition tolerance** [3]. Here's a concise summary:

1. **Core Trade-off**:  
   - In the event of a **network partition** (a split in connectivity between nodes), a system must choose between **consistency** (linearizability) and **availability**. It cannot guarantee both [3].  
   - This is often summarized as "CP (consistent but not available) or AP (available but not consistent)" [3].  

2. **Key Limitations**:  
   - The original CAP theorem is **not a strict rule** but a conceptual framework. It assumes **network partitions** are inevitable and focuses on **linearizability** (a specific consistency model) and **network faults** (e.g., partitions) [4].  
   - Modern systems often face **other fault types** (e.g., node failures, delays) not addressed by CAP [4].  

3. **Practical Implications**:  
   - Systems prioritizing **high availability** (e.g., AP) may tolerate eventual consistency, while those requiring **strong consistency** (e.g., CP) may sacrifice availability during partitions [3].  
   - The theorem has been **superseded by more precise results** in distributed systems research [4].  

For further details, refer to the discussion in [3] and [4].

**Sources (8):**
- [1] Designing Data Intensive Applications by Martin Kleppmann — Preface
- [2] Designing Data Intensive Applications by Martin Kleppmann — Index
- [3] Designing Data Intensive Applications by Martin Kleppmann — Part II. Distributed Data > Chapter 9. Consistency and Consensus > Linearizability > The Cost of Linearizability
- [4] Designing Data Intensive Applications by Martin Kleppmann — Part II. Distributed Data > Chapter 9. Consistency and Consensus > Linearizability > The Cost of Linearizability
- [5] Designing Data Intensive Applications by Martin Kleppmann — Index
- [6] Designing Data Intensive Applications by Martin Kleppmann — Glossary
- [7] Designing Data Intensive Applications by Martin Kleppmann — Index
- [8] Designing Data Intensive Applications by Martin Kleppmann — Index

---

## 6. What is leaderless replication?

Leaderless replication, also known as Dynamo-style replication, is a distributed data management approach where clients can directly write to any replica without a central leader node. This model eliminates a single point of failure but introduces challenges in maintaining consistency due to potential concurrent writes and network delays. Here's a structured explanation:

1. **Architecture**:  
   - Clients send writes to multiple replicas simultaneously.  
   - There is no central leader to enforce write order, allowing any replica to accept writes [2].  
   - For example, in a three-node system, different nodes might receive writes in varying sequences (e.g., Node 1 gets A’s write, Node 2 gets A then B, Node 3 gets B then A) [1].  

2. **Conflict Resolution**:  
   - **Last Write Wins (LWW)**: Conflicts are resolved by timestamps, with the latest timestamp overwriting earlier ones. However, this can discard concurrent writes and may not guarantee durability or linearizability [1].  
   - **Quorums**: Writes and reads require a majority of replicas (e.g., $ w + r > n $) to ensure consistency. For instance, with $ n = 3 $, $ w = 2 $, and $ r = 2 $, the system tolerates one unavailable node [5].  

3. **Challenges**:  
   - **Event Ordering**: Without a leader, writes may arrive out of order at different nodes, leading to inconsistencies (e.g., Node 2 thinks X is B, while others think it’s A) [1].  
   - **Eventual Consistency**: Replicas converge to the same value over time but may temporarily diverge, requiring mechanisms like version vectors or hinted handoff to resolve conflicts [2].  

4. **Use Cases**:  
   - Suitable for multi-datacenter operations, as it tolerates network interruptions and latency spikes [8].  
   - Systems like Cassandra, Riak, and Voldemort use leaderless replication, though they handle conflicts via LWW or other strategies [2].  

5. **Trade-offs**:  
   - **Availability vs. Consistency**: Leaderless replication prioritizes availability but sacrifices strong consistency, relying on eventual consistency and quorum-based guarantees [6].  
   - **Complexity**: Requires careful configuration of quorums and conflict resolution policies to avoid data loss or inconsistencies [5].  

In summary, leaderless replication enhances fault tolerance and availability but demands sophisticated mechanisms to manage concurrency and ensure data consistency. It is ideal for systems prioritizing scalability and resilience over strict linearizability [6].

**Sources (8):**
- [1] Designing Data Intensive Applications by Martin Kleppmann — Part II. Distributed Data > Chapter 5. Replication > Leaderless Replication > Detecting Concurrent Writes
- [2] Designing Data Intensive Applications by Martin Kleppmann — Part II. Distributed Data > Chapter 5. Replication > Leaderless Replication > Writing to the Database When a Node Is Down
- [3] Designing Data Intensive Applications by Martin Kleppmann — Part II. Distributed Data > Chapter 9. Consistency and Consensus > Linearizability > Implementing Linearizable Systems
- [4] Designing Data Intensive Applications by Martin Kleppmann — Part II. Distributed Data > Chapter 5. Replication
- [5] Designing Data Intensive Applications by Martin Kleppmann — Part II. Distributed Data > Chapter 5. Replication > Leaderless Replication > Writing to the Database When a Node Is Down
- [6] Designing Data Intensive Applications by Martin Kleppmann — Part II. Distributed Data > Chapter 5. Replication > Summary
- [7] Designing Data Intensive Applications by Martin Kleppmann — Part II. Distributed Data > Chapter 5. Replication > Leaderless Replication > Detecting Concurrent Writes
- [8] Designing Data Intensive Applications by Martin Kleppmann — Part II. Distributed Data > Chapter 5. Replication > Leaderless Replication > Detecting Concurrent Writes

---

## 7. What problems can arise from replication lag?

Replication lag in distributed systems can lead to several problems, primarily related to data consistency and user experience. Here are the key issues:

1. **Inconsistent Read Results**: When an application reads from an asynchronous follower that has not yet caught up with the leader, it may see outdated or inconsistent data. For example, a user might submit data (e.g., a comment) and then immediately read it back, only to find it missing because the follower hasn't replicated the write yet [1]. This is known as *eventual consistency* [22, 23].

2. **Read-After-Write Inconsistency**: Users may not see their own updates immediately after writing. For instance, if a user submits a record and then reads it from a follower, the follower might not yet have the latest data, making the user think their write failed [1]. This requires *read-after-write consistency* (or *read-your-writes consistency*) to ensure users always see their own updates [24].

3. **Monotonicity Violations**: Replication lag can cause a user to observe data that appears to "go backward in time." For example, a user might first read a comment from a fast replica, then later read the same query from a slower replica that hasn't caught up, making the comment disappear [5]. This is addressed by *monotonic reads*, which guarantee that later reads do not see older data than earlier ones [23].

4. **Causality Violations**: If writes are replicated with different delays, an observer might see events in the wrong order. For example, a follower might receive a response before the corresponding question, creating a paradox where Mrs. Cake answers Mr. Poons’s question before he asks it [3]. This is resolved by *consistent prefix reads*, ensuring writes are observed in the same order across all replicas [23].

5. **Impact on Applications**: In systems with high replication lag, these inconsistencies can degrade user experience. For example, users might lose confidence if their data doesn’t appear immediately, or applications might display incorrect or outdated information [1].

Solutions include using leader-based replication for critical reads, tracking timestamps to enforce consistency, and leveraging transactions to provide stronger guarantees [7]. However, these approaches require careful design to balance performance and correctness.

**Sources (8):**
- [1] Designing Data Intensive Applications by Martin Kleppmann — Part II. Distributed Data > Chapter 5. Replication > Problems with Replication Lag > Reading Your Own Writes
- [2] Designing Data Intensive Applications by Martin Kleppmann — Part II. Distributed Data > Chapter 5. Replication > Problems with Replication Lag
- [3] Designing Data Intensive Applications by Martin Kleppmann — Part II. Distributed Data > Chapter 5. Replication > Problems with Replication Lag > Consistent Prefix Reads
- [4] Designing Data Intensive Applications by Martin Kleppmann — Part II. Distributed Data > Chapter 5. Replication > Problems with Replication Lag > Reading Your Own Writes
- [5] Designing Data Intensive Applications by Martin Kleppmann — Part II. Distributed Data > Chapter 5. Replication > Problems with Replication Lag > Monotonic Reads
- [6] Designing Data Intensive Applications by Martin Kleppmann — Part II. Distributed Data > Chapter 8. The Trouble with Distributed Systems
- [7] Designing Data Intensive Applications by Martin Kleppmann — Part II. Distributed Data > Chapter 5. Replication > Problems with Replication Lag > Solutions for Replication Lag
- [8] Designing Data Intensive Applications by Martin Kleppmann — Part II. Distributed Data > Chapter 5. Replication > Leaders and Followers

---

## 8. What is the difference between optimistic and pessimistic concurrency control?

Optimistic and pessimistic concurrency control differ fundamentally in how they handle potential conflicts during transaction execution:

### **Pessimistic Concurrency Control**  
- **Approach**: Assumes conflicts are likely and blocks transactions to prevent them. For example, **two-phase locking (2PL)** [1] uses locks (e.g., range locks or table locks) to serialize access to data. If a transaction holds a lock, other transactions must wait, ensuring no conflicts.  
- **Trade-offs**: High performance penalties under low contention but poor scalability with high contention (e.g., many transactions accessing the same data) [2].  

### **Optimistic Concurrency Control**  
- **Approach**: Assumes conflicts are rare. Transactions proceed without locks and check for conflicts only at commit time. For example, **serializable snapshot isolation (SSI)** [1] uses snapshot isolation (reading from a consistent database snapshot) and detects serialization conflicts during commit. If conflicts are found, the transaction is aborted and retried.  
- **Trade-offs**: Performs better under low contention (as in SSI) but may experience higher abort rates under high contention [2].  

### **Key Differences**  
1. **Conflict Handling**:  
   - Pessimistic (e.g., 2PL) blocks transactions to avoid conflicts upfront.  
   - Optimistic (e.g., SSI) allows transactions to proceed and resolves conflicts later.  

2. **Performance**:  
   - Pessimistic methods have higher overhead due to locking but avoid retries.  
   - Optimistic methods reduce overhead but risk retries if conflicts arise.  

3. **Use Cases**:  
   - Pessimistic is better for systems with frequent contention (e.g., high write throughput).  
   - Optimistic is preferable for systems with low contention (e.g., read-heavy workloads).  

### **Example from Sources**  
- **Pessimistic**: Two-phase locking "blocks if something potentially dangerous happens" [1].  
- **Optimistic**: SSI "continues anyway, in the hope that everything will turn out all right" [1], with conflicts resolved at commit.  

In summary, pessimistic control prioritizes safety through blocking, while optimistic control trades safety for performance by resolving conflicts after the fact.

**Sources (8):**
- [1] Designing Data Intensive Applications by Martin Kleppmann — Part II. Distributed Data > Chapter 7. Transactions > Serializability > Serializable Snapshot Isolation (SSI)
- [2] Designing Data Intensive Applications by Martin Kleppmann — Part II. Distributed Data > Chapter 7. Transactions > Serializability > Serializable Snapshot Isolation (SSI)
- [3] Designing Data Intensive Applications by Martin Kleppmann — Index
- [4] Designing Data Intensive Applications by Martin Kleppmann — Index
- [5] Designing Data Intensive Applications by Martin Kleppmann — Index
- [6] Designing Data Intensive Applications by Martin Kleppmann — Index
- [7] Designing Data Intensive Applications by Martin Kleppmann — Part II. Distributed Data > Chapter 7. Transactions > Summary
- [8] Designing Data Intensive Applications by Martin Kleppmann — Part II. Distributed Data > Chapter 7. Transactions > Serializability > Actual Serial Execution

---

## 9. What is a distributed transaction?

A **distributed transaction** is a transaction that spans multiple distributed systems or nodes, ensuring that all participating systems either commit or abort the transaction together to maintain consistency. There are two primary types of distributed transactions:  

1. **Database-internal distributed transactions**: These occur within a single distributed database system (e.g., VoltDB or MySQL Cluster’s NDB storage engine), where all nodes run the same database software. They can leverage optimizations specific to the system and often perform well [1].  

2. **Heterogeneous distributed transactions**: These involve multiple disparate technologies (e.g., a message broker and a database) and require coordination to ensure atomic commit across systems. For example, a message from a queue can be acknowledged only if the associated database transaction succeeds, achieved via protocols like **XA transactions** [4].  

The **two-phase commit (2PC)** protocol is commonly used to implement distributed transactions. It operates in two phases:  
- **Phase 1 (Prepare)**: The coordinator asks all participants if they can commit.  
- **Phase 2 (Commit)**: If all participants agree, the coordinator instructs them to commit; otherwise, it aborts the transaction [5][6].  

**XA transactions** (defined by the X/Open standard) enable heterogeneous systems to participate in distributed transactions by providing a common interface for coordination [4]. However, distributed transactions face challenges such as performance penalties (e.g., MySQL’s distributed transactions are 10x slower than single-node ones [1]), operational complexity, and risks of **in-doubt transactions** (transactions stuck in an unresolved state due to coordinator failures [3]).  

In summary, distributed transactions ensure atomicity across distributed systems but require careful design to balance consistency, performance, and fault tolerance.

**Sources (8):**
- [1] Designing Data Intensive Applications by Martin Kleppmann — Part II. Distributed Data > Chapter 9. Consistency and Consensus > Distributed Transactions and Consensus > Distributed Transactions in Practice
- [2] Designing Data Intensive Applications by Martin Kleppmann — Part III. Derived Data > Chapter 12. The Future of Data Systems > Data Integration > Combining Specialized Tools by Deriving Data
- [3] Designing Data Intensive Applications by Martin Kleppmann — Part II. Distributed Data > Chapter 9. Consistency and Consensus > Distributed Transactions and Consensus > Distributed Transactions in Practice
- [4] Designing Data Intensive Applications by Martin Kleppmann — Part II. Distributed Data > Chapter 9. Consistency and Consensus > Distributed Transactions and Consensus > Distributed Transactions in Practice
- [5] Designing Data Intensive Applications by Martin Kleppmann — Part II. Distributed Data > Chapter 9. Consistency and Consensus > Distributed Transactions and Consensus > Atomic Commit and Two-Phase Commit (2PC)
- [6] Designing Data Intensive Applications by Martin Kleppmann — Part II. Distributed Data > Chapter 9. Consistency and Consensus > Distributed Transactions and Consensus > Atomic Commit and Two-Phase Commit (2PC)
- [7] Designing Data Intensive Applications by Martin Kleppmann — Part II. Distributed Data > Chapter 7. Transactions > The Slippery Concept of a Transaction > Single-Object and Multi-Object Operations
- [8] Designing Data Intensive Applications by Martin Kleppmann — Part II. Distributed Data > Chapter 9. Consistency and Consensus > Distributed Transactions and Consensus

---

## 10. What is the two-phase commit protocol?

The **two-phase commit (2PC)** protocol is a distributed algorithm designed to ensure **atomicity** in transactions across multiple nodes. It guarantees that either all participants commit the transaction or all abort it, preventing partial commits that could leave the system in an inconsistent state. Here's how it works:

### **Phases of 2PC**
1. **Prepare Phase**  
   - The **coordinator** (a central node) sends a **prepare request** to all participants, asking if they can commit the transaction.  
   - Each participant writes the transaction’s state to disk (to ensure durability) and responds with a "yes" or "no" based on whether they can commit.  
   - If any participant replies "no," the coordinator immediately aborts the transaction. If all reply "yes," the coordinator proceeds to the next phase.  

2. **Commit Phase**  
   - The coordinator sends a **commit request** to all participants.  
   - Participants then commit their local changes and acknowledge the commit.  
   - If the commit request fails or times out, the coordinator retries indefinitely to ensure the decision is enforced [4].  

### **Key Features**
- **Atomicity**: The protocol ensures that all nodes either commit or abort the transaction. If the coordinator crashes after the prepare phase but before committing, it recovers by reading its transaction log to determine the status of in-doubt transactions. Any without a commit record are aborted [1].  
- **Coordinator Dependency**: The coordinator is critical. If it fails during the prepare phase, the transaction could become "in-doubt" (neither committed nor aborted). However, the coordinator’s log ensures recovery [4].  
- **Blocking Nature**: 2PC is **blocking** because it can become stuck waiting for the coordinator to recover. This is why alternatives like **three-phase commit (3PC)** were proposed, though 3PC assumes bounded network delays and is less practical in systems with unbounded delays [1].  

### **Comparison to 2PL**  
- **2PC** focuses on **distributed atomicity**, while **two-phase locking (2PL)** is a **locking mechanism** for serializable isolation in single-node or distributed systems [7]. They are distinct concepts despite similar names.  

### **Use Cases**  
2PC is used in databases like **MySQL (InnoDB)** and **SQL Server** for distributed transactions, though it is not widely adopted in "NoSQL" systems due to its blocking nature [8].  

For further details, see [1], [4], and [8].

**Sources (8):**
- [1] Designing Data Intensive Applications by Martin Kleppmann — Part II. Distributed Data > Chapter 9. Consistency and Consensus > Distributed Transactions and Consensus > Atomic Commit and Two-Phase Commit (2PC)
- [2] Designing Data Intensive Applications by Martin Kleppmann — Glossary
- [3] Designing Data Intensive Applications by Martin Kleppmann — Part II. Distributed Data > Chapter 7. Transactions > Serializability > Two-Phase Locking (2PL)
- [4] Designing Data Intensive Applications by Martin Kleppmann — Part II. Distributed Data > Chapter 9. Consistency and Consensus > Distributed Transactions and Consensus > Atomic Commit and Two-Phase Commit (2PC)
- [5] Designing Data Intensive Applications by Martin Kleppmann — Part II. Distributed Data > Chapter 9. Consistency and Consensus > Distributed Transactions and Consensus > Atomic Commit and Two-Phase Commit (2PC)
- [6] Designing Data Intensive Applications by Martin Kleppmann — Part II. Distributed Data > Chapter 9. Consistency and Consensus > Distributed Transactions and Consensus > Atomic Commit and Two-Phase Commit (2PC)
- [7] Designing Data Intensive Applications by Martin Kleppmann — Part II. Distributed Data > Chapter 7. Transactions > Serializability > Two-Phase Locking (2PL)
- [8] Designing Data Intensive Applications by Martin Kleppmann — Part II. Distributed Data > Chapter 9. Consistency and Consensus > Distributed Transactions and Consensus > Atomic Commit and Two-Phase Commit (2PC)

---

## 11. What is linearizability?

Linearizability is a consistency model that ensures operations on a distributed system appear to occur instantaneously and atomically, as if there were a single copy of the data [2]. It guarantees that once a write operation completes, all subsequent reads will return the updated value, even if the write is not yet fully processed [5]. This recency guarantee means the system behaves as though there is no replication lag, and all clients see the most recent value [1].

Key aspects of linearizability include:
1. **Total Order**: Operations are ordered in a single, sequential timeline, with no concurrency [4]. If a read occurs after a write, it must see the new value, even if the write is still in progress [6].
2. **Atomicity**: Reads and writes are treated as indivisible actions. For example, a compare-and-set operation (CAS) must either succeed entirely or fail, ensuring no intermediate states [6].
3. **Conflict Resolution**: Linearizable systems avoid issues like write skew by ensuring operations are ordered strictly, though this requires coordination and can impact performance [1].

Linearizability is stricter than causal consistency, which allows for partial ordering of events (e.g., branching timelines) [8]. While linearizability provides strong consistency, it can reduce availability during network partitions (as per the CAP theorem) [7]. Systems like databases using two-phase locking or serial execution often achieve linearizability, but alternatives like causal consistency are used to balance performance and availability [8]. 

In summary, linearizability ensures strong consistency by enforcing a single, global order of operations, but it comes with trade-offs in scalability and fault tolerance compared to weaker models [1][4][7].

**Sources (8):**
- [1] Designing Data Intensive Applications by Martin Kleppmann — Part II. Distributed Data > Chapter 9. Consistency and Consensus > Linearizability > What Makes a System Linearizable?
- [2] Designing Data Intensive Applications by Martin Kleppmann — Part II. Distributed Data > Chapter 9. Consistency and Consensus > Linearizability
- [3] Designing Data Intensive Applications by Martin Kleppmann — Part II. Distributed Data > Chapter 9. Consistency and Consensus > Summary
- [4] Designing Data Intensive Applications by Martin Kleppmann — Part II. Distributed Data > Chapter 9. Consistency and Consensus > Ordering Guarantees > Ordering and Causality
- [5] Designing Data Intensive Applications by Martin Kleppmann — Part II. Distributed Data > Chapter 9. Consistency and Consensus > Linearizability > What Makes a System Linearizable?
- [6] Designing Data Intensive Applications by Martin Kleppmann — Part II. Distributed Data > Chapter 9. Consistency and Consensus > Linearizability > What Makes a System Linearizable?
- [7] Designing Data Intensive Applications by Martin Kleppmann — Part II. Distributed Data > Chapter 9. Consistency and Consensus > Linearizability > The Cost of Linearizability
- [8] Designing Data Intensive Applications by Martin Kleppmann — Part II. Distributed Data > Chapter 9. Consistency and Consensus > Ordering Guarantees > Ordering and Causality

---

## 12. What is the difference between REST and RPC?

The difference between **REST** (Representational State Transfer) and **RPC** (Remote Procedure Call) lies in their design philosophies, protocols, and use cases:  

1. **REST** is a **design philosophy** built on HTTP principles, emphasizing **stateless interactions** using standard HTTP methods (GET, POST, etc.) and URLs to identify resources. It prioritizes simplicity, scalability, and interoperability, often used in **microservices** and **web APIs** [3]. RESTful APIs typically use **JSON/XML** for data exchange and rely on **OpenAPI/Swagger** for documentation [3].  

2. **RPC** is a **protocol** for invoking procedures remotely, often over a network. It abstracts the network communication, allowing clients to call remote methods as if they were local. RPCs can use various transport protocols (e.g., HTTP, TCP) and may involve **complex serialization formats** (e.g., XML, Thrift). Examples include **SOAP** (an XML-based RPC protocol) and **gRPC** (modern RPC framework using HTTP/2) [3].  

### Key Differences:  
- **Statelessness**: REST is inherently stateless, while RPC can be stateful or stateless depending on implementation.  
- **Data Formats**: REST often uses **JSON** or **XML**, while RPC may use custom binary formats or protocols like **Thrift** or **Protocol Buffers** [3].  
- **Use Cases**: REST is ideal for **web services** and **public APIs**, whereas RPC is common in **internal systems** or **distributed applications** requiring tight integration [3].  
- **Error Handling**: REST relies on HTTP status codes (e.g., 404, 500), while RPC often uses custom error codes or exceptions [3].  

For example, **SOAP** (an RPC protocol) uses XML for messages and relies on WS-* standards, whereas **RESTful APIs** (like those in microservices) prioritize simplicity and ease of use [3].  

Sources: [3], [4]

**Sources (8):**
- [1] Designing Data Intensive Applications by Martin Kleppmann — Index
- [2] Designing Data Intensive Applications by Martin Kleppmann — Index
- [3] Designing Data Intensive Applications by Martin Kleppmann — Part I. Foundations of Data Systems > Chapter 4. Encoding and Evolution > Modes of Dataflow > Dataflow Through Services: REST and RPC
- [4] Designing Data Intensive Applications by Martin Kleppmann — Index
- [5] Designing Data Intensive Applications by Martin Kleppmann — Index
- [6] Designing Data Intensive Applications by Martin Kleppmann — Index
- [7] Designing Data Intensive Applications by Martin Kleppmann — Index
- [8] Designing Data Intensive Applications by Martin Kleppmann — Index

---

## 13. What is a message broker used for?

A message broker is used to facilitate reliable communication between processes by acting as an intermediary that stores and forwards messages. It enables **asynchronous, decoupled communication** where senders and receivers do not need to know each other's locations or statuses. Key uses include:

1. **Reliable Message Delivery**: Message brokers buffer messages, ensuring they are not lost if the recipient is unavailable or overloaded. They also support redelivery if a consumer crashes [1].  
2. **Decoupling Senders and Receivers**: Senders publish messages without knowing recipients, and receivers can subscribe to topics or queues, allowing flexible, scalable architectures [1].  
3. **Support for Multiple Messaging Patterns**:  
   - **Load balancing**: Distributes messages across multiple consumers to parallelize processing [2].  
   - **Fan-out**: Sends the same message to all consumers, enabling independent processing [2].  
4. **Durable Storage**: Some brokers (e.g., Apache Kafka) support log compaction and disk-based storage, making them suitable for persistent data retention [5].  
5. **Change Data Capture (CDC)**: Brokers can replicate database changes to other systems (e.g., search indexes) by streaming updates, ensuring derived systems stay synchronized [7][8].  

Message brokers differ from databases by focusing on **stream processing** and **event-driven workflows** rather than structured querying or long-term data storage [4][5]. They are critical for building resilient, scalable distributed systems.

**Sources (8):**
- [1] Designing Data Intensive Applications by Martin Kleppmann — Part I. Foundations of Data Systems > Chapter 4. Encoding and Evolution > Modes of Dataflow > Message-Passing Dataflow
- [2] Designing Data Intensive Applications by Martin Kleppmann — Part III. Derived Data > Chapter 11. Stream Processing > Transmitting Event Streams > Messaging Systems
- [3] Designing Data Intensive Applications by Martin Kleppmann — Part III. Derived Data > Chapter 11. Stream Processing > Transmitting Event Streams > Messaging Systems
- [4] Designing Data Intensive Applications by Martin Kleppmann — Part III. Derived Data > Chapter 11. Stream Processing > Transmitting Event Streams > Messaging Systems
- [5] Designing Data Intensive Applications by Martin Kleppmann — Part III. Derived Data > Chapter 11. Stream Processing > Databases and Streams
- [6] Designing Data Intensive Applications by Martin Kleppmann — Index
- [7] Designing Data Intensive Applications by Martin Kleppmann — Part III. Derived Data > Chapter 11. Stream Processing > Databases and Streams > Change Data Capture
- [8] Designing Data Intensive Applications by Martin Kleppmann — Part III. Derived Data > Chapter 11. Stream Processing > Databases and Streams > Change Data Capture

---

## 14. What is the actor model in the context of distributed systems?

The actor model in distributed systems is a programming model for concurrency that enables scalable, fault-tolerant applications across multiple nodes. Key characteristics include:

1. **Asynchronous Message Passing**: Actors communicate via asynchronous messages, with each actor processing one message at a time. This avoids thread management issues like race conditions and deadlocks [1].  
2. **Location Transparency**: The model treats local and remote communication uniformly. Messages are encoded into byte sequences for network transmission and decoded on the receiving end, abstracting node locations [1].  
3. **State and Isolation**: Each actor has isolated local state and operates independently, ensuring no shared state between actors [1].  
4. **Fault Tolerance**: Actors can be scheduled independently, and frameworks handle message loss (though not guaranteed). For distributed systems, this model integrates with message brokers but requires careful handling of forward/backward compatibility during upgrades [1].  

This model is distinct from RPC (Remote Procedure Call) due to its inherent tolerance for message loss and focus on asynchronous communication [1].  

**Sources**: [1], [2]

**Sources (8):**
- [1] Designing Data Intensive Applications by Martin Kleppmann — Part I. Foundations of Data Systems > Chapter 4. Encoding and Evolution > Modes of Dataflow > Message-Passing Dataflow
- [2] Designing Data Intensive Applications by Martin Kleppmann — Index
- [3] Designing Data Intensive Applications by Martin Kleppmann — Part II. Distributed Data > Chapter 8. The Trouble with Distributed Systems > Knowledge, Truth, and Lies > System Model and Reality
- [4] Designing Data Intensive Applications by Martin Kleppmann — Index
- [5] Designing Data Intensive Applications by Martin Kleppmann — Part II. Distributed Data > Chapter 8. The Trouble with Distributed Systems > Knowledge, Truth, and Lies > The Truth Is Defined by the Majority
- [6] Designing Data Intensive Applications by Martin Kleppmann — Index
- [7] Designing Data Intensive Applications by Martin Kleppmann — Part III. Derived Data > Chapter 11. Stream Processing > Processing Streams > Reasoning About Time
- [8] Designing Data Intensive Applications by Martin Kleppmann — Part II. Distributed Data > Chapter 8. The Trouble with Distributed Systems > Summary

---

## 15. What is data partitioning (sharding)?

Data partitioning, also known as sharding, is the process of dividing a large dataset into smaller, manageable subsets called partitions or shards, which are then distributed across multiple nodes in a distributed system [1]. The primary goal of partitioning is **scalability**, enabling systems to handle larger datasets and higher query throughput by distributing data and workload evenly across nodes [1]. 

### Key Concepts:
1. **Partitioning vs. Replication**:  
   - **Replication** involves maintaining multiple copies of the same data across nodes for redundancy and availability [2].  
   - **Partitioning** splits data into distinct subsets (shards) so that each partition resides on a separate node. These two techniques often work together, as illustrated in Figure II-1, where data is split into partitions and each partition has replicas [7].  

2. **Partitioning Strategies**:  
   - **Key-Value Data**: For key-value stores, partitioning typically uses hashing (e.g., consistent hashing) or range-based partitioning to distribute data evenly. Random assignment of records to nodes can lead to "hotspots" (overloaded partitions), while deterministic methods (e.g., hashing by key) avoid this [3].  
   - **Skew Avoidance**: Uneven distribution of data (skew) reduces the effectiveness of partitioning. For example, if one partition handles most queries, it becomes a bottleneck [1].  

3. **Shared-Nothing Architecture**:  
   Partitioning is central to **shared-nothing architectures**, where each node operates independently with its own resources (CPU, memory, storage). Coordination between nodes is handled via software, and data is rebalanced to ensure even load distribution [7].  

4. **Trade-offs**:  
   - Partitioning improves scalability but introduces complexity in managing distributed transactions and ensuring consistency. Cross-partition transactions require consensus protocols (e.g., Paxos) to maintain linearizability [4].  
   - It also complicates query execution, as queries may span multiple partitions, requiring coordination [3].  

### Summary:  
Partitioning (sharding) is critical for scaling distributed systems by splitting data into partitions and distributing them across nodes. It balances load, avoids bottlenecks, and enables horizontal scaling, though it requires careful design to manage skew, consistency, and coordination [1][3][7].

**Sources (8):**
- [1] Designing Data Intensive Applications by Martin Kleppmann — Part II. Distributed Data > Chapter 6. Partitioning
- [2] Designing Data Intensive Applications by Martin Kleppmann — Part II. Distributed Data > Chapter 5. Replication
- [3] Designing Data Intensive Applications by Martin Kleppmann — Part II. Distributed Data > Chapter 6. Partitioning > Partitioning of Key-Value Data
- [4] Designing Data Intensive Applications by Martin Kleppmann — Part II. Distributed Data > Chapter 9. Consistency and Consensus > Linearizability > Implementing Linearizable Systems
- [5] Designing Data Intensive Applications by Martin Kleppmann — Part II. Distributed Data > Chapter 9. Consistency and Consensus > Linearizability > The Cost of Linearizability
- [6] Designing Data Intensive Applications by Martin Kleppmann — Glossary
- [7] Designing Data Intensive Applications by Martin Kleppmann — Part II. Distributed Data
- [8] Designing Data Intensive Applications by Martin Kleppmann — Index

---

## 16. How does consistent hashing help with partitioning?

Consistent hashing helps with partitioning by distributing data across nodes in a way that minimizes the need for full redistribution when nodes are added or removed. It uses a hash function to map keys to partitions, ensuring each node handles a portion of the data. When a new node joins, it takes over a fraction of existing partitions (e.g., half of randomly selected partitions), reducing the amount of data that needs to be moved [1]. This approach avoids the need for centralized coordination or consensus, as described in the original definition of consistent hashing [5]. However, it can lead to uneven splits, which systems like Cassandra mitigate with optimized rebalancing algorithms [1]. While consistent hashing is less effective for databases compared to other methods, it remains a foundational technique for dynamic partitioning in distributed systems [5].

**Sources (8):**
- [1] Designing Data Intensive Applications by Martin Kleppmann — Part II. Distributed Data > Chapter 6. Partitioning > Rebalancing Partitions > Operations: Automatic or Manual Rebalancing
- [2] Designing Data Intensive Applications by Martin Kleppmann — Index
- [3] Designing Data Intensive Applications by Martin Kleppmann — Index
- [4] Designing Data Intensive Applications by Martin Kleppmann — Part II. Distributed Data > Chapter 6. Partitioning > Rebalancing Partitions > Strategies for Rebalancing
- [5] Designing Data Intensive Applications by Martin Kleppmann — Part II. Distributed Data > Chapter 6. Partitioning > Partitioning of Key-Value Data > Partitioning by Hash of Key
- [6] Designing Data Intensive Applications by Martin Kleppmann — Part II. Distributed Data > Chapter 6. Partitioning > Partitioning of Key-Value Data > Skewed Workloads and Relieving Hot Spots
- [7] Designing Data Intensive Applications by Martin Kleppmann — Part II. Distributed Data > Chapter 6. Partitioning > Summary
- [8] Designing Data Intensive Applications by Martin Kleppmann — Part II. Distributed Data > Chapter 6. Partitioning > Rebalancing Partitions

---

## 17. What is a secondary index and why is it harder to maintain in a partitioned database?

A **secondary index** is an additional data structure that enables efficient searching for records based on attributes other than the primary key (e.g., finding all red cars by indexing the "color" field). Maintaining secondary indexes in a **partitioned database** is more complex due to the interplay between partitioning schemes and index design. Here's why:

1. **Partitioning and Index Scope**:  
   Secondary indexes often span multiple partitions, unlike primary keys, which are directly tied to partitioning. For example, in a document-partitioned system (e.g., partitioning by document ID), a secondary index on "color" might spread entries across partitions (e.g., red cars could exist in partition 0 and partition 1) [1]. This requires **scatter/gather queries**, where the system must query all relevant partitions and combine results, increasing latency [3].

2. **Write Complexity**:  
   In term-partitioned indexes (e.g., partitioning by indexed terms like "color:red"), updates to a document may affect multiple partitions. For instance, adding a red car might require updating the "color:red" index in one partition and the "make:Toyota" index in another. This necessitates coordination across partitions, complicating write operations and increasing the risk of consistency issues [4]. Databases like DynamoDB acknowledge this by allowing asynchronous updates, which can delay index synchronization [5].

3. **Consistency Challenges**:  
   Global secondary indexes (term-partitioned) require distributed transactions to ensure consistency across partitions, which is not supported by all databases [5]. Even with support, maintaining real-time consistency during writes can lead to performance trade-offs, as updates must propagate across partitions.

4. **Rebalancing Overhead**:  
   When partitions are rebalanced (e.g., due to node additions/removals), secondary indexes must also be redistributed. This adds complexity, as indexes may need to be split or merged across partitions, and their partitioning logic (e.g., term-based) must align with the primary data partitioning [6].

In summary, secondary indexes are harder to maintain in partitioned systems because their scope often transcends partition boundaries, requiring specialized partitioning strategies (document-based or term-based) and careful management of read/write consistency and rebalancing. These challenges highlight the trade-offs between scalability and index efficiency in distributed databases [1][4][5].

**Sources (8):**
- [1] Designing Data Intensive Applications by Martin Kleppmann — Part II. Distributed Data > Chapter 6. Partitioning > Partitioning and Secondary Indexes > Partitioning Secondary Indexes by Document
- [2] Designing Data Intensive Applications by Martin Kleppmann — Part III. Derived Data > Chapter 12. The Future of Data Systems > Unbundling Databases > Designing Applications Around Dataflow
- [3] Designing Data Intensive Applications by Martin Kleppmann — Part II. Distributed Data > Chapter 6. Partitioning > Partitioning and Secondary Indexes > Partitioning Secondary Indexes by Document
- [4] Designing Data Intensive Applications by Martin Kleppmann — Part II. Distributed Data > Chapter 6. Partitioning > Partitioning and Secondary Indexes > Partitioning Secondary Indexes by Term
- [5] Designing Data Intensive Applications by Martin Kleppmann — Part II. Distributed Data > Chapter 6. Partitioning > Rebalancing Partitions
- [6] Designing Data Intensive Applications by Martin Kleppmann — Part II. Distributed Data > Chapter 6. Partitioning > Summary
- [7] Designing Data Intensive Applications by Martin Kleppmann — Part I. Foundations of Data Systems > Chapter 3. Storage and Retrieval > Data Structures That Power Your Database > Other Indexing Structures
- [8] Designing Data Intensive Applications by Martin Kleppmann — Glossary

---

## 18. What is the difference between batch processing and stream processing?

The primary difference between batch processing and stream processing lies in the nature of their input data and how they handle processing:  

1. **Data Nature**:  
   - **Batch processing** operates on **bounded datasets** of **known, finite size** [1]. Inputs are static, and processing occurs in discrete jobs (e.g., daily or hourly tasks).  
   - **Stream processing** handles **unbounded datasets** that arrive incrementally over time (e.g., real-time data feeds) [1]. Streams are continuous and potentially infinite.  

2. **State and Fault Tolerance**:  
   - Batch processing emphasizes **deterministic, pure functions** with no side effects, treating inputs as immutable and outputs as append-only [1].  
   - Stream processing extends this by allowing **managed, fault-tolerant state** (e.g., maintaining user profiles or caches) and handling failures through mechanisms like checkpointing [1].  

3. **Latency and Use Cases**:  
   - Batch processing is suited for **historical data reprocessing** (e.g., generating reports) and **large-scale analytics** [2].  
   - Stream processing excels in **low-latency scenarios** (e.g., real-time recommendations) and **continuous updates** (e.g., monitoring metrics) [1].  

4. **Implementation Differences**:  
   - Batch systems (e.g., Hadoop) process fixed datasets, while stream systems (e.g., Apache Flink) handle continuous flows. Some systems (like Spark) blend both by using microbatches [1].  
   - Stream processing often relies on **event time** (timestamps embedded in data) for accurate time-based computations, whereas batch processing may use **processing time** (system clock) [8].  

In summary, batch processing is for static, finite data with predictable outcomes, while stream processing is for dynamic, continuous data requiring real-time or near-real-time responses [1][2].

**Sources (8):**
- [1] Designing Data Intensive Applications by Martin Kleppmann — Part III. Derived Data > Chapter 12. The Future of Data Systems > Data Integration > Batch and Stream Processing
- [2] Designing Data Intensive Applications by Martin Kleppmann — Part III. Derived Data > Chapter 12. The Future of Data Systems > Data Integration > Batch and Stream Processing
- [3] Designing Data Intensive Applications by Martin Kleppmann — Part III. Derived Data > Chapter 11. Stream Processing > Transmitting Event Streams
- [4] Designing Data Intensive Applications by Martin Kleppmann — Part III. Derived Data > Chapter 10. Batch Processing
- [5] Designing Data Intensive Applications by Martin Kleppmann — Part III. Derived Data > Chapter 12. The Future of Data Systems > Data Integration > Batch and Stream Processing
- [6] Designing Data Intensive Applications by Martin Kleppmann — Part III. Derived Data > Chapter 11. Stream Processing > Processing Streams > Stream Joins
- [7] Designing Data Intensive Applications by Martin Kleppmann — Part III. Derived Data > Chapter 11. Stream Processing
- [8] Designing Data Intensive Applications by Martin Kleppmann — Part III. Derived Data > Chapter 11. Stream Processing > Processing Streams > Reasoning About Time

---

## 19. What is exactly-once semantics in stream processing?

Exactly-once semantics in stream processing ensures that each event is processed exactly once, even in the presence of failures, thereby preserving data integrity. This is achieved through mechanisms like **checkpointing**, **microbatching**, and **idempotent writes** [1][2][3]. 

1. **Checkpointing and Microbatching**: Systems like Apache Flink periodically generate checkpoints of state, allowing restarts from the last known good state after failures. Microbatching (e.g., Spark Streaming) processes data in small batches, implicitly providing tumbling windows and enabling recovery from partial failures [2]. However, once output leaves the stream processor (e.g., written to a database), the framework cannot discard it, necessitating idempotent operations to avoid duplicates [2].

2. **Idempotent Writes**: To handle failures, operations must be idempotent, meaning they produce the same result whether executed once or multiple times. This prevents issues like duplicate transactions or lost updates [3][4]. For example, a credit card transaction must ensure a charge is applied exactly once, even if the system retries due to a fault [4].

3. **Fault Tolerance and Atomicity**: Exactly-once semantics rely on fault-tolerant message delivery and mechanisms like **atomic commits** or **two-phase commit (2PC)** protocols. These ensure that all side effects of processing an event (e.g., database writes, state updates) are applied atomically or not at all, maintaining consistency [3][4].

4. **Integration with Batch Systems**: Modern systems like Apache Beam and Google Cloud Dataflow unify batch and stream processing, enabling exactly-once semantics across both paradigms by leveraging event time windowing and durable state management [1][3].

In summary, exactly-once semantics in stream processing is critical for integrity, achieved through a combination of checkpointing, idempotence, and atomicity, ensuring no duplicates or lost updates even during failures [1][2][3][4].

**Sources (8):**
- [1] Designing Data Intensive Applications by Martin Kleppmann — Part III. Derived Data > Chapter 12. The Future of Data Systems > Data Integration > Batch and Stream Processing
- [2] Designing Data Intensive Applications by Martin Kleppmann — Part III. Derived Data > Chapter 11. Stream Processing > Processing Streams > Fault Tolerance
- [3] Designing Data Intensive Applications by Martin Kleppmann — Part III. Derived Data > Chapter 12. The Future of Data Systems > Aiming for Correctness > Timeliness and Integrity
- [4] Designing Data Intensive Applications by Martin Kleppmann — Part III. Derived Data > Chapter 12. The Future of Data Systems > Aiming for Correctness > The End-to-End Argument for Databases
- [5] Designing Data Intensive Applications by Martin Kleppmann — Part III. Derived Data > Chapter 11. Stream Processing > Summary
- [6] Designing Data Intensive Applications by Martin Kleppmann — Part III. Derived Data > Chapter 12. The Future of Data Systems > Unbundling Databases > Composing Data Storage Technologies
- [7] Designing Data Intensive Applications by Martin Kleppmann — Index
- [8] Designing Data Intensive Applications by Martin Kleppmann — Index

---

## 20. What ethical considerations does the book raise about data systems?

The book raises several ethical considerations regarding data systems, emphasizing the responsibilities of engineers and the potential societal impacts of their work. Key points include:

1. **Ethical Use of Predictive Analytics**: The book warns that while predictive analytics can be beneficial (e.g., forecasting disease spread), its application in high-stakes scenarios (e.g., criminal recidivism predictions, loan defaults, or insurance risk assessments) directly affects individuals' lives. It stresses that such tools must be used with care to avoid harm and ensure fairness [1].

2. **Engineers' Responsibility**: The text underscores that software engineers have an ethical duty to consider the consequences of their systems. It critiques the cavalier attitude toward privacy and negative outcomes often seen in practice, advocating for adherence to ethical guidelines like the ACM’s *Software Engineering Code of Ethics and Professional Practice* [1][77].

3. **Technology as a Tool, Not Intrinsic Good/Bad**: The book argues that the ethical implications of a technology depend on its use. For example, a search engine (a data system) can have vastly different societal impacts compared to a weapon like a gun. Engineers must balance innovation with accountability for their systems' effects [1].

4. **Bias and Fairness**: While not explicitly detailed in the provided sources, the broader context of the book (e.g., discussions on algorithmic transparency and derived data) implies concerns about biased outcomes in data systems, aligning with external critiques of machine learning ethics [78][79][84][85].

5. **Transparency and Accountability**: The text highlights the need for transparency in data systems, particularly in areas like auditing and cryptographic practices (e.g., certificate transparency), to ensure trust and prevent misuse [1][75].

In summary, the book calls for ethical vigilance in designing data systems, emphasizing the importance of balancing technical innovation with societal responsibility.

**Sources (8):**
- [1] Designing Data Intensive Applications by Martin Kleppmann — Part III. Derived Data > Chapter 12. The Future of Data Systems > Doing the Right Thing > Predictive Analytics
- [2] Designing Data Intensive Applications by Martin Kleppmann — Part I. Foundations of Data Systems > Chapter 1. Reliable, Scalable, and Maintainable Applications > Thinking About Data Systems
- [3] Designing Data Intensive Applications by Martin Kleppmann — Part III. Derived Data > Chapter 12. The Future of Data Systems > Summary
- [4] Designing Data Intensive Applications by Martin Kleppmann — Part I. Foundations of Data Systems > Chapter 1. Reliable, Scalable, and Maintainable Applications > Summary
- [5] Designing Data Intensive Applications by Martin Kleppmann — Preface > Who Should Read This Book?
- [6] Designing Data Intensive Applications by Martin Kleppmann — Preface > Scope of This Book
- [7] Designing Data Intensive Applications by Martin Kleppmann — Part I. Foundations of Data Systems
- [8] Designing Data Intensive Applications by Martin Kleppmann — Part III. Derived Data

---
