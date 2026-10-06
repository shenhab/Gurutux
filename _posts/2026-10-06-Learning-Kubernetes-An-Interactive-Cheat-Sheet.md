---
layout: post
title: "Learning Kubernetes: An Interactive Cheat Sheet"
date: 2026-10-06 01:24:50 -0000
author: "Mahmoud Elshenhab"
tags: kubernetes k8s containers sre cloud architecture cheatsheet learning
---

I started learning Kubernetes tonight. I did not begin with the YAML. I went straight to the architecture, because I wanted to understand what the pieces are and how they talk to each other before writing a single manifest. This post is a full explanation of the architecture in the diagram below, one component at a time, in plain language.

Hover over or click any box in the diagram. The panel under it tells you what that piece does and lights up the paths it uses.

<div class="k8s-widget" style="margin: 1.5em 0;">
  <iframe id="k8s-cheat-sheet"
          src="/assets/widgets/k8s-visual-cheat-sheet.html"
          title="Kubernetes Visual Cheat Sheet"
          loading="lazy"
          style="width: 100%; height: 900px; border: 1px solid #eee; border-radius: 12px; background: #fdfdfd;"></iframe>
  <p style="font-size: 0.9em; color: #666; margin-top: 0.5em;">
    Having trouble with the embed? <a href="/assets/widgets/k8s-visual-cheat-sheet.html" target="_blank" rel="noopener">Open the cheat sheet in its own tab</a>.
  </p>
</div>
<script>
  (function () {
    var frame = document.getElementById('k8s-cheat-sheet');
    if (!frame) return;
    function fit(h) { if (h && h > 200) frame.style.height = (h + 4) + 'px'; }
    window.addEventListener('message', function (e) {
      if (e.source === frame.contentWindow && e.data && e.data.type === 'widget-resize') fit(e.data.height);
    });
    frame.addEventListener('load', function () {
      try { fit(frame.contentDocument.documentElement.scrollHeight); } catch (err) { /* cross-origin, rely on messages */ }
    });
  })();
</script>

## How to read the diagram

The diagram has three areas.

- **The client, on the left.** This is `kubectl`, the command-line tool. It sits outside the cluster.
- **The control plane, top box.** This is the part that *decides* what should run. It never runs your application.
- **The worker node, bottom box.** This is the part that *does the work*. Your containers live here.

A real cluster has one control plane, usually spread across several machines so it survives failures, and as many worker nodes as the workload needs. The diagram shows one node to keep things readable. Every node runs the same set of agents.

The arrows show who talks to whom. Every single arrow either starts or ends at the api-server. That is the most important thing to notice, and the rest of this post explains why.

## The client: kubectl

`kubectl` is a program that runs on a laptop or in a CI pipeline. It is not part of the cluster. If you removed it, the cluster would keep running exactly as before.

It does two things. It sends the cluster a description of what you *want* to exist, written in YAML. And it asks the cluster questions, such as which Pods are running. Both go to the same place: the api-server.

That is why it sits outside the box. It is a visitor. It knocks on the front door, hands over a request, and leaves.

## The control plane: the part that decides

The control plane has four components. Each one has a single, narrow job.

### api-server: the front door

Everything goes through the api-server. Every request from `kubectl`, every decision from the scheduler, every status report from a node. There is no other way in.

When a request arrives, the api-server checks who sent it, checks whether they are allowed to do that, checks that the content is valid, and then saves it. That is the whole job. It does not decide where things run. It is a strict receptionist with a very good filing system.

The api-server holds no state of its own. Everything it knows is in etcd. This matters for scaling, and we come back to it below.

### etcd: the memory

etcd is a small, reliable key-value database. It stores the full state of the cluster: every Deployment, every Pod, every Secret, every ConfigMap, and the current status of each one. If something is not in etcd, the cluster does not know about it.

Only the api-server is allowed to read from or write to etcd. No other component touches it. This means there is exactly one copy of the truth and exactly one gatekeeper in front of it.

etcd runs as a group of members, usually three or five, and uses a consensus protocol called Raft. A write is only accepted once a majority of the members have agreed to it. That majority is called the **quorum**. With three members, two must agree. With five, three must agree. This is why etcd clusters use an odd number of members: an even number gives you no extra safety, only an extra machine that can fail.

If etcd loses quorum, it stops accepting writes. The api-server can then no longer save anything, so the cluster freezes. Pods that are already running keep running, because the kubelets on the nodes do not need etcd to keep a container alive. But nothing new can be created, scheduled, or changed until quorum comes back.

etcd is very sensitive to slow disks and slow networks, because every write has to be confirmed by a majority before it returns. At hyperscale, etcd is kept on its own dedicated machines, separate from the api-servers. If etcd shares a machine with a busy api-server, the two compete for disk and CPU, etcd slows down, and every api-server waiting on it freezes with it. Keeping etcd alone keeps the api-servers responsive.

### controller-manager: the fixer

Kubernetes works by comparing two things: what you *asked for*, and what is *actually happening*. The controller-manager is a bundle of small loops that run this comparison over and over, forever.

A simple example. You asked for three copies of a web server. One of them crashes. A controller notices that three were wanted and only two exist, and asks the api-server to create a third. It does not restart the old one. It does not alarm anyone. It just closes the gap.

Each kind of object has its own controller. There is one for Deployments, one for ReplicaSets, one for Nodes, one for Jobs, and so on. They all follow the same pattern: watch the api-server, compare, fix.

### scheduler: the matchmaker

When a new Pod is created, it has no home yet. The scheduler's job is to pick one.

It looks at every node and removes the ones that cannot run the Pod. Maybe the node does not have enough free memory, or it has been marked as off-limits. Then it scores the remaining nodes and picks the best fit. Finally, it writes the chosen node's name onto the Pod, through the api-server.

That is where its job ends. The scheduler never starts a container. It only writes down a decision.

## The worker node: the part that does the work

Every worker node runs the same small set of programs.

### kubelet: the node's captain

The kubelet is the Kubernetes agent on each node. It watches the api-server for Pods that have been assigned to *its* node. When it sees one, it makes sure the containers in that Pod are running and healthy. If a container dies, the kubelet restarts it. It runs the health checks. It reports the Pod's status back to the api-server.

The kubelet takes orders only from the api-server, and it never talks to etcd, the scheduler, or the controllers directly.

### container runtime: the engine

The kubelet does not run containers itself. It asks the container runtime to do it. On most clusters today that is containerd or CRI-O. The runtime pulls the image, creates the container, and starts the process.

The kubelet talks to the runtime over a standard interface called the Container Runtime Interface, so Kubernetes does not care which engine is underneath.

### kube-proxy and the CNI plugin: the network

Two pieces handle networking, and the diagram shows them together.

The CNI plugin (Container Network Interface) gives each Pod its own IP address and connects it to the cluster network. Pods on different nodes can reach each other directly.

kube-proxy handles Services. A Service is a stable virtual address that stands in front of a group of Pods. kube-proxy programs the node's networking so that traffic sent to that address is forwarded to one of the healthy Pods behind it.

### Pod: the unit of work

A Pod is the smallest thing Kubernetes will run. It holds one or more containers that share an IP address and can share storage. Most of the time a Pod holds exactly one container.

Pods are rarely created by hand. You create a Deployment. The Deployment creates a ReplicaSet. The ReplicaSet creates the Pods. Each layer has a different job: the Deployment handles rolling updates, and the ReplicaSet handles keeping the right number of copies alive.

## Two rules that explain almost everything

**Rule one: everything goes through the api-server.** Every arrow in the diagram touches it. No component talks to another component directly. They all talk to the api-server, and only the api-server talks to etcd.

**Rule two: nobody pushes, everybody watches.** The control plane never reaches out to a node and says "run this". Instead, each piece watches the api-server for changes that concern it, and acts on what it sees. The scheduler watches for unassigned Pods. The kubelet watches for Pods assigned to its node. The controllers watch for gaps between desired and actual state.

The second rule is why Kubernetes stays calm under failure. If a node loses contact with the control plane, its Pods keep running. If a controller restarts, it simply starts watching again and picks up where it left off. There is no fragile chain of commands to break.

## Scaling the control plane

Rule one has a consequence. Because the api-server keeps no state of its own, you can run as many copies of it as you like, behind a load balancer. Each copy reads and writes the same etcd. Clients cannot tell them apart.

At hyperscale, this goes one step further: Kubernetes can be hosted on Kubernetes. The control plane components of a cluster, including its api-servers, run as ordinary Pods on another, underlying cluster. The underlying cluster then treats the api-servers like any other workload. Need more api-server capacity? Scale the Deployment. Lose a machine? The controllers replace the Pod. This is how the large managed Kubernetes services run thousands of customer control planes, and it is why their api-servers can scale seamlessly.

etcd is the exception. It is stateful, it depends on quorum, and it is sensitive to latency, so it does not scale by adding copies the way the api-server does. That is why, at scale, it is run alone on dedicated machines and treated with more care than everything else in the control plane.

## What happens when you run kubectl apply

Here is the full sequence for a Deployment with one replica, following the arrows in the diagram.

1. `kubectl` reads the YAML and sends it to the api-server.
2. The api-server checks identity and permissions, validates the content, and saves the Deployment in etcd. etcd confirms the write once a quorum of its members has it.
3. The Deployment controller sees a new Deployment and creates a ReplicaSet. The ReplicaSet controller sees that and creates a Pod. Both go through the api-server and both are saved in etcd. The Pod has no node yet.
4. The scheduler sees a Pod with no node, picks the best one, and writes that node's name onto the Pod.
5. The kubelet on that node sees a Pod assigned to it. It asks the container runtime to pull the image and start the container.
6. The CNI plugin gives the Pod an IP address. kube-proxy updates the routing rules so a Service can reach it.
7. The kubelet reports back that the Pod is running. From then on it keeps checking, and restarts the container if it fails.

Seven steps, five different programs, and not one of them called another directly. They all went through the front door.

## Quick recap

| Piece | Lives in | One-line job |
| --- | --- | --- |
| kubectl | Outside the cluster | Sends requests to the api-server |
| api-server | Control plane | The only door in and out. Checks and saves everything. Stateless, so it scales out |
| etcd | Control plane | Remembers the whole cluster state. Needs quorum. Kept on its own machines at scale |
| controller-manager | Control plane | Spots gaps between wanted and actual, and fixes them |
| scheduler | Control plane | Picks a node for each new Pod |
| kubelet | Worker node | Runs and watches the Pods on its node |
| container runtime | Worker node | Actually starts and stops containers |
| kube-proxy / CNI | Worker node | Gives Pods addresses and routes traffic to them |
| Pod | Worker node | Your application, wrapped up |

## What the diagram leaves out

This is the core architecture only. Services, Ingress, persistent storage, ConfigMaps, Secrets, RBAC and namespaces all sit on top of it. They follow the same pattern every time: an object saved in etcd, a controller watching it, and the api-server in the middle.

I am still learning. This is the first piece.
