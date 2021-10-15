---
layout: post
title: "SMTP-Gated"
date: 2012-04-08 12:15:00 -0000
tags: Linux mail smtp spam
---

What is SMTP-Gated ?

It is a server which have the ability to Scan, Recognize, and  Block Mails that Containing Spam or Viruses.

How it works ?

It acts like proxy, intercepting outgoing SMTP connections and scanning session data on-the-fly. When messages is infected, the SMTP session is terminated.

Features:

    Transparency – is meant to be totally transparent for users, but stone-build for worms 😉
    Message data is intercepted on-the-fly, and scanned just before acknowledged to SMTP server
    Does not break AUTH, PIPELINING or STARTTLS (TLS without scanning)
    Can block messages if AUTH is not used (optionally passing if AUTH is not supported by MSA)
    Can insert source IP (pre-NAT) and ident* into message header
    Can block any mail from infected hosts for defined time
    Logging of MAIL FROM and RCPT TO (plain or as base64-ed MD5)
    Logging of HELO/EHLO hostname
    Can impose some limits on number of SMTP sessions: total, per IP, per ident*
    Can reject connections when load exceeds some limit
    Can skip spam-scanning if load is high
    Executing user script on certain events
    Scanning limited to messages up to configured size
    Can be used to build scanning-farm for one or more routers*
    Logs all connections via syslog
    Has nifty status screen 😉
    Message size limit (since 1.4.16-rc1)
    Outgoing XCLIENT support (since 1.4.16-rc1)
    Conditional content scanning depending on SMTP-AUTH status (since 1.4.16-rc1)
    Regular expression (regex) conditions for HELO/MAIL FROM/RCPT TO (since 1.4.16-rc1)
    SPF checking (since 1.4.16-rc1)

Supports:

    Content scanning:
        Clam AntiVirus daemon (clamd)
        mksd – daemonised version of mks_vir
        SpamAssassin antispam scanning
    Access checking:
        libpcre for HELO/MAIL FROM/RCPT TO regular expressions (not-)match
        libspf2 for SPF (tested with debian libspf2 1.2.1)
    Uses various NAT frameworks (for standalone mode), or ident/proxy-helper* for external mode
        patched ident daemon
        proxy-helper daemon
        netfilter framework of Linux
        ipfw on FreeBSD
        BSD/pf (packetfilter)
        BSD/ipfilter
