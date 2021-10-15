---
layout: post
title: "Ip Tables Concepts"
date: 2012-04-08 13:15:00 -0000
Author: "Mahmoud Elshenhab"
tags: Linux firewall network iptables
---

I will try -As much as I can- to explain IP-Tables Concepts in a simple way.

What is IP-Tables ?

(My Definition) The IP-Tables is a peace of software to filter the network transition (Packets).

(Wikipedia’s Definition) iptables is a user space application program that allows a system administrator to configure the tables provided by the Linux kernel firewall (implemented as different Netfilter modules) and the chains and rules it stores.

 The Contents of IP-Tables:
|Name|Description|
|-------|--------|---------|
|Tables|The Table is: A set of chains which designed to do a specific function|
|Chains|The Chain is: A set of rules that are applied on packets that traverses the chain. Every Chain have a specified purpose which you will know while we are talking.|
|Rules|A rule is a set of a condition or several conditions together with a single action. the action of a rule will be applied if all the conditions of that rule have been achieved.|

What is NAT – Network Address Translation ?

NAT allows a host or several hosts to share the same IP address in a way.

HOW ?

let’s say we have a local network consisting of 5-10 clients. We set their default gateways to point through the NAT server. Normally the packet would simply be forwarded by the gateway machine, but in the case of an NAT server it is a little bit different.

NAT servers translates the source and destination addresses of packets as we already said to different addresses. The NAT server receives the packet, rewrites the source and/or destination address and then recalculates the checksum of the packet. One of the most common usages of NAT is the SNAT (Source Network Address Translation) function. Basically, this is used in the above example if we can’t afford or see any real idea in having a real public IP for each and every one of the clients. In that case, we use one of the private IP ranges for our local network (for example, 192.168.1.0/24), and then we turn on SNAT for our local network. SNAT will then turn all 192.168.1.0 addresses into it’s own public IP (for example, 217.115.95.34). This way, there will be 5-10 clients or many many more using the same shared IP address.

There is also something called DNAT, which can be extremely helpful when it comes to setting up servers etc. First of all, you can help the greater good when it comes to saving IP space, second, you can get an more or less totally impenetrable firewall in between your server and the real server in an easy fashion, or simply share an IP for several servers that are separated into several physically different servers. For example, we may run a small company server farm containing a webserver and ftp server on the same machine, while there is a physically separated machine containing a couple of different chat services that the employees working from home or on the road can use to keep in touch with the employees that are on-site. We may then run all of these services on the same IP from the outside via DNAT.

In Linux, there are actually two separate types of NAT that can be used, either Fast-NAT or Netfilter-NAT. Fast-NAT is implemented inside the IP routing code of the Linux kernel, while Netfilter-NAT is also implemented in the Linux kernel, but inside the netfilter code. Since this article won’t touch the IP routing code too closely, we will pretty much leave it here, except for a few notes. Fast-NAT is generally called by this name since it is much faster than the netfilter NAT code. It doesn’t keep track of connections, and this is both its main pro and con. Connection tracking takes a lot of processor power, and hence it is slower, which is one of the main reasons that the Fast-NAT is faster than Netfilter-NAT. As we also said, the bad thing about Fast-NAT doesn’t track connections, which means it will not be able to do SNAT very well for whole networks, neither will it be able to NAT complex protocols such as FTP, IRC and other protocols that Netfilter-NAT is able to handle very well. It is possible, but it will take much, much more work than would be expected from the Netfilter implementation.

There is also a final word that is basically a synonym to SNAT, which is the Masquerade word. In Netfilter, masquerade is pretty much the same as SNAT with the exception that masquerading will automatically set the new source IP to the default IP address of the outgoing network interface.

## IP-Tables Chains:
|Chain|Explanation|
|---|---|
|PREROUTING|Packets will enter this chain before a routing decision is made.|
|INPUT|Packet is going to be locally delivered. (N.B.: It does not have anything to do with processes having a socket open. Local delivery is controlled by the “local-delivery” routing table: `ip route show table local`.)|
|FORWARD|All packets that have been routed and were not for local delivery will traverse this chain.“”:|
|OUTPUT|Packets sent from the machine itself will be visiting this chain.|
|POSTROUTING|Routing decision has been made. Packets enter this chain just before handing them off to the hardware.|

## IP-Tables Tables:
|Table|Explanation|
|---|---|
|NAT|The NAT table is used mainly for Network Address Translation. “NAT”ed packets get their IP addresses altered, according to our rules. Packets in a stream only traverse this table once. We assume that the first packet of a stream is allowed. The rest of the packets in the same stream are automatically “NAT”ed or Masqueraded etc, and will be subject to the same actions as the first packet. These will, in other words, not go through this table again, but will nevertheless be treated like the first packet in the stream. This is the main reason why you should not do any filtering in this table, which we will discuss at greater length further on. The PREROUTING chain is used to alter packets as soon as they get in to the firewall. The OUTPUT chain is used for altering locally generated packets (i.e., on the firewall) before they get to the routing decision. Finally we have the POSTROUTING chain which is used to alter packets just as they are about to leave the firewall.|
|MANGLE|This table is used mainly for mangling packets. Among other things, we can change the contents of different packets and that of their headers. Examples of this would be to change the TTL,TOS or MARK. Note that the MARK is not really a change to the packet, but a mark value for the packet is set in kernel space. Other rules or programs might use this mark further along in the firewall to filter or do advanced routing on; tc is one example. The table consists of five built in chains, the PREROUTING, POSTROUTING, OUTPUT, INPUT and FORWARD chains.PREROUTING is used for altering packets just as they enter the firewall and before they hit the routing decision. POSTROUTING is used to mangle packets just after all routing decisions have been made. OUTPUT is used for altering locally generated packets after they enter the routing decision. INPUT is used to alter packets after they have been routed to the local computer itself, but before the user space application actually sees the data. FORWARD is used to mangle packets after they have hit the first routing decision, but before they actually hit the last routing decision. Note that mangle can’t be used for any kind of Network Address Translation orMasquerading, the nat table was made for these kinds of operations.|
|FILTER|The filter table should be used exclusively for filtering packets. For example, we could DROP,LOG, ACCEPT or REJECT packets without problems, as we can in the other tables. There are three chains built in to this table. The first one is named FORWARD and is used on all non-locally generated packets that are not destined for our local host (the firewall, in other words). INPUT is used on all packets that are destined for our local host (the firewall) and OUTPUT is finally used for all locally generated packets.|
|RAW|Iptable’s Raw table is for configuration excemptions. Raw table has the following built-in chains.|
