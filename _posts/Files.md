---
layout: post
title: "Files in Linux"
date: 2017-10-01 12:15:00 -0000
tags: Files Linux
---

What is a file in Linux ?
  A file is a collection of data blocks and has an inode number which holds metadata about this file.

What is the inodes?
  An inode is a data structure that is pre-alocated during the filesystem creation and contains specific metadata about a file like:
    File type.
    Permissions.
    User ID (Owner).
    Group ID (Owner Group).
    logical file size.
    last access timestamp.
    last modification timestamp.
    last inode number change timestamp.
    File deletion time.
    Number of hard links.
    pointers for the data blocks.

Maybe your next question will be: where is the file name?
  The file name exists in the data block of the parent directory pointing to the inode number that has the metadata of this file.

The files structure in Linux was built to unify the operations of the files ignoring the fact that these files can be located on different filesystems, as in linux all the files on any filesystem should be treated the same because Linux uses VFS “Virtual Filesystem Switch” to access all the filesystems types transparently without the client application noticing the difference. VFS can be used to bridge the differences in Windows, classic Mac OS/macOS and Unix filesystems, so that applications can access files on local filesystems of those types without having to know what type of filesystem they are accessing.

For more information about the VFS check this link: https://www.ibm.com/developerworks/library/l-virtual-filesystem-switch/index.html

Lets talk about the file size a bit. There are several ways to check the file size like below:

    # root @ ub05ada39a41857ef4a39
    $ ls -lh zeros
    -rw-r–r– 1 root root 1 Sep 30 17:02 zeros

    # root @ ub05ada39a41857ef4a39
    $ stat zeros
    File: ‘zeros’
    Size: 1 Blocks: 8 IO Block: 4096 regular file
    Device: fc01h/64513d Inode: 7866457 Links: 1
    Access: (0644/-rw-r–r–) Uid: ( 0/ root) Gid: ( 0/ root)
    Access: 2017-09-30 16:51:53.746819123 +0200
    Modify: 2017-09-30 17:02:53.407742697 +0200
    Change: 2017-09-30 17:02:53.407742697 +0200
    Birth: –

    # root @ ub05ada39a41857ef4a39
    $ du -sh zeros
    4.0K zeros

You can notice the difference between the same file size if you use the “du” command vs the “ls” and “state” command. “du” command will show you the actual size of the file that is allocated on the physical storage which shows 4.0k. unlike the “du” and state command which shows the logical size of the file, so how does this work?

Any filesystem that doesn’t support “Variable block sizes” will never be able to allocate space less than the default block size, as each file points to a single inode, which will point to the blocks that contains the data of the file. a file’s inode can point to zero blocks if the file never had data. For example:

    # root @ ub05ada39a41857ef4a39
    $ touch noblocks

    # root @ ub05ada39a41857ef4a39
    $ ls -la noblocks
    -rw-r–r– 1 root root 0 Sep 30 17:35 noblocks

    # root @ ub05ada39a41857ef4a39
    $ stat noblocks
    File: ‘noblocks’
    Size: 0 Blocks: 0 IO Block: 4096 regular empty file
    Device: fc01h/64513d Inode: 7866459 Links: 1
    Access: (0644/-rw-r–r–) Uid: ( 0/ root) Gid: ( 0/ root)
    Access: 2017-09-30 17:35:57.023274029 +0200
    Modify: 2017-09-30 17:35:57.023274029 +0200
    Change: 2017-09-30 17:35:57.023274029 +0200
    Birth: –

    # root @ ub05ada39a41857ef4a39
    $ du -sh noblocks
    0 noblocks

This file “noblocks” has been created, but never had data in it, thus the inode didn’t point to any block to save data, however if this file contained a single byte then the inode will point to one block which will allocate the default block size of the filesystem.
The block size of any file system can be known by the below command:
blockdev –getbsz /dev/partition

    # blockdev –getbsz /dev/sdb1
    4096

A single block can’t store data of more than 1 file, as the inodes will not able to identify the length of the data that belong to each file inside the block, and expect that the data of this block belongs to a single file only.
