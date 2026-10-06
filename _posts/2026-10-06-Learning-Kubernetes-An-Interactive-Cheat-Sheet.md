---
layout: post
title: "Learning Kubernetes: An Interactive Cheat Sheet"
date: 2026-10-06 01:24:50 -0000
author: "Mahmoud Elshenhab"
tags: kubernetes k8s containers sre cloud architecture cheatsheet learning
---

I have been learning Kubernetes this year. The YAML was never the hard part. The hard part was keeping all the moving pieces straight in my head. Which part talks to which? Who remembers the state? What really happens between typing `kubectl apply` and a container running on a machine? To answer that for myself, I built a visual cheat sheet. This post walks through it, one piece at a time, in plain language.

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

There are three areas.

- **The client, on the left.** That is you, running `kubectl`. It sits outside the cluster.
- **The control plane, top box.** This is the part that *decides* what should run. It never runs your application.
- **The worker node, bottom box.** This is the part that *does the work*. Your containers live here.

A real cluster has one control plane (usually spread over a few machines for safety) and as many worker nodes as you need. The diagram shows one node to keep things readable. Every node looks the same.

## Start with you: kubectl

`kubectl` is a command-line program on your laptop, or in your CI pipeline. It is not part of Kubernetes itself. You could delete it and the cluster would carry on running exactly as before.

It does two things. It sends the cluster your YAML files, which describe what you *want* to exist. And it asks the cluster questions, like "what Pods are running?" Both go to the same place: the api-server.

That is why it sits outside the box. It is a visitor. It knocks on the front door and leaves.

## The control plane: the part that decides

The control plane has four pieces. Each one has a single, narrow job.

### api-server: the front door

Everything goes through the api-server. Every command from `kubectl`, every decision from the scheduler, every status report from a node. There is no back door.

When a request arrives, the api-server checks who you are, checks whether you are allowed to do that, checks that the YAML is valid, and then saves it. That is the whole job. It does not make decisions about where things run. It is a very strict receptionist with a very good filing system.

### etcd: the memory

etcd is a small, reliable database. It stores the full state of the cluster: every Deployment, every Pod, every Secret, every ConfigMap. If something is not in etcd, the cluster does not know about it.

Only the api-server is allowed to read from or write to etcd. Nothing else touches it. This is the single most important rule in the whole design, because it means there is exactly one copy of the truth and exactly one gatekeeper.

If you back up only one thing in a cluster, back up etcd.

### controller-manager: the fixer

Kubernetes works by comparing two things. What you *asked for*, and what is *actually happening*. The controller-manager is a bundle of small loops that do this comparison over and over, forever.

Take a simple example. You asked for three copies of a web server. One of them crashes. A controller notices that three were wanted and only two exist, and asks the api-server to create a third. It does not restart the old one. It does not panic. It just closes the gap.

Each kind of object has its own controller. There is one for Deployments, one for ReplicaSets, one for Nodes, one for Jobs, and so on. They all follow the same pattern: watch, compare, fix.

### scheduler: the matchmaker

When a new Pod is created, it has no home yet. The scheduler's job is to pick one.

It looks at every node and throws out the ones that cannot run the Pod. Maybe the node does not have enough memory, or it is marked as off-limits. Then it scores the remaining nodes and picks the best fit. Finally, it writes the chosen node name onto the Pod, through the api-server.

That is where its job ends. The scheduler never starts a container. It only writes down a decision.

## The worker node: the part that does the work

Every worker node runs the same small set of programs.

### kubelet: the node's captain

The kubelet is the Kubernetes agent on each node. It watches the api-server for Pods that have been assigned to *its* node. When it sees one, it makes sure the containers in that Pod are running and healthy. If a container dies, the kubelet restarts it. It runs the health checks. It reports the Pod's status back to the api-server.

If you have spent years looking after services on individual servers, this is the piece you will recognise. It is the init system and the monitoring agent rolled into one, and it takes orders only from the api-server.

### container runtime: the engine

The kubelet does not run containers itself. It asks the container runtime to do it. On most clusters today that is containerd, or CRI-O. The runtime pulls the image, creates the container, and starts the process.

Kubernetes talks to the runtime over a standard interface, so it does not care which engine you use.

### kube-proxy and the CNI plugin: the network

Two pieces handle networking, and they are often shown together.

The CNI plugin (Container Network Interface) gives each Pod its own IP address and connects it to the cluster network. Pods on different nodes can reach each other directly.

kube-proxy handles Services. A Service is a stable virtual address that stands in front of a group of Pods. kube-proxy programs the node's networking so that traffic sent to that address is forwarded to one of the healthy Pods behind it.

### Pod: the unit of work

A Pod is the smallest thing Kubernetes will run. It holds one or more containers that share an IP address and can share storage. Most of the time a Pod holds exactly one container.

You will rarely create a Pod by hand. You create a Deployment. The Deployment creates a ReplicaSet. The ReplicaSet creates the Pods. The reason for the layers is that each one handles a different job: the Deployment handles rolling updates, and the ReplicaSet handles keeping the right number of copies alive.

## Two rules that explain almost everything

Once I understood these two rules, the diagram stopped looking like a pile of daemons and started looking like one simple system.

**Rule one: everything goes through the api-server.** Every arrow in the diagram touches it. No component talks to another component directly. They all talk to the api-server, and the api-server talks to etcd.

**Rule two: nobody pushes, everybody watches.** The control plane never reaches out to a node and says "run this". Instead, each piece watches the api-server for changes that concern it, and acts on what it sees. The scheduler watches for unassigned Pods. The kubelet watches for Pods assigned to its node. The controllers watch for gaps between desired and actual state.

This second rule is why Kubernetes is so calm under failure. If a node loses contact with the control plane, its Pods keep running. If a controller restarts, it just starts watching again and picks up where it left off. There is no fragile chain of commands to break.

## What happens when you run kubectl apply

Here is the full sequence for a Deployment with one replica. This is the walk-through I had to trace by hand before the diagram made sense.

1. `kubectl` reads your YAML and sends it to the api-server.
2. The api-server checks your identity and permissions, validates the YAML, and saves the Deployment in etcd.
3. The Deployment controller sees a new Deployment and creates a ReplicaSet. The ReplicaSet controller sees that and creates a Pod. Both go through the api-server and both are saved in etcd. The Pod has no node yet.
4. The scheduler sees a Pod with no node, picks the best one, and writes that node's name onto the Pod.
5. The kubelet on that node sees a Pod assigned to it. It asks the container runtime to pull the image and start the container.
6. The CNI plugin gives the Pod an IP address. kube-proxy updates the routing rules so a Service can reach it.
7. The kubelet reports back that the Pod is running. From now on it keeps checking, and restarts the container if it fails.

Seven steps, five different programs, and not one of them called another directly. They all went through the front door.

## Quick recap

| Piece | Lives in | One-line job |
| --- | --- | --- |
| kubectl | Your machine | Sends your wishes to the api-server |
| api-server | Control plane | The only door in and out. Checks and saves everything |
| etcd | Control plane | Remembers the whole cluster state |
| controller-manager | Control plane | Spots gaps between wanted and actual, and fixes them |
| scheduler | Control plane | Picks a node for each new Pod |
| kubelet | Worker node | Runs and watches the Pods on its node |
| container runtime | Worker node | Actually starts and stops containers |
| kube-proxy / CNI | Worker node | Gives Pods addresses and routes traffic to them |
| Pod | Worker node | Your application, wrapped up |

## What the cheat sheet leaves out

This is the core architecture only. Services, Ingress, persistent storage, ConfigMaps, Secrets, RBAC and namespaces all sit on top of this. The good news is that they follow the same pattern every time: an object saved in etcd, a controller watching it, and the api-server in the middle. Once the core model is clear, the rest is details.

I will extend the diagram as I learn more. If you spot something wrong or misleading, I would genuinely like to hear it.
