---
layout: post
title: "How MySQL Replication Works?"
date: 2022-05-30 10:37:00 -0000
author: "Mahmoud Elshenhab"
tags: MySQL Database Engine Replication
---

# MySQL Binary Log Replication.
MySQL binary Log replication is one the most used feature in MySQL flavoured Databases as it is the most simple way to replicate data changes across several MySQL nodes. And because it is an Asynchronous replication it has low to no impact on the Master node(s).

## Binary Log
### What is binary log?
> The binary log is a set of log files that contain information about data modifications made to a MySQL server instance. It contains all statements that update data. It also contains statements that potentially could have updated it (for example, a DELETE which matched no rows), unless row-based logging is used. Statements are stored in the form of "events" that describe the modifications. The binary log also contains information about how long each statement took that updated data.

### What is the Purpose of the Binary log?
- The binary log has two important purposes:
>1.  For replication, the binary log is used on master replication servers as a record of the statements to be sent to slave servers. Many details of binary log format and handling are specific to this purpose. The master server sends the events contained in its binary log to its slaves, which execute those events to make the same data changes that were made on the master. A slave stores events received from the master in its relay log until they can be executed. The relay log has the same format as the binary log.
> 1. Certain data recovery operations require use of the binary log. After a backup file has been restored, the events in the binary log that were recorded after the backup was made are re-executed. These events bring databases up to date from the point of the backup.


### Types of binary logging:
- There are two types of binary logging:
> 1. Statement-based logging: Events contain SQL statements that produce data changes (inserts, updates, deletes).
> 1. Row-based logging: Events describe changes to individual rows.
> 1. Mixed logging uses statement-based logging by default but switches to row-based logging automatically as necessary.

#### Is there a tool to explore Binary logging?
> mysqlbinlog is a utility that can be used to print binary or relay log contents in readable form.

## Replication
The MySQL replication feature allows a server - the master - to send all changes to another server - the slave - and the slave tries to apply all changes to keep up-to-date with the master. Replication works as follows:
- Whenever the master's database is modified, the change is written to a file (binary log, or binlog). This is done by the client thread that executed the query that modified the database.
- **Binary log dump thread.** The source creates a thread to send the binary log contents to a replica when the replica connects. The binary log dump thread acquires a lock on the source's binary log for reading each event that is to be sent to the replica. As soon as the event has been read, the lock is released, even before the event is sent to the replica.
-  **Replication I/O receiver thread.** When a `START REPLICA` statement is issued on a replica server, the replica creates an I/O (receiver) thread, which connects to the source and asks it to send the updates recorded in its binary logs. The replication receiver thread reads the updates that the source's  `Binlog Dump`  thread sends (see previous item) and copies them to local files that comprise the replica's relay log.
- **Replication SQL applier thread.** The replica creates an SQL (applier) thread to read the relay log that is written by the replication receiver thread and execute the transactions contained in it.

### MySQL is a lying
Something that you need to know that MySQL is a big lier because it always lies about the Slave lag behind the Master.
The logical definition of lag is the amount of time needed for the slave to be able to reach the data state of the master, however this is not what MySQL Slave is reporting. 
The Thread that reports the second behind master (lag) is the SQL thread of the slave itself. and it calculates it by getting the difference between the current machine time and the timestamp of the last executed log from the relay log, and this don't reflect the actual lag by any means.
This is because the single threaded nature of the binary log threads, and that there is no calculations occurs on the relay log before executing it.
