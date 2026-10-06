---
layout: post
title: "Learning Kubernetes: An Interactive Cheat Sheet"
date: 2026-10-06 01:24:50 -0000
author: "Mahmoud Elshenhab"
tags: kubernetes k8s containers sre cloud architecture cheatsheet learning
---

I have been learning Kubernetes properly this year. The YAML was never the hard part. The hard part was holding all the moving pieces in my head at once: which component talks to which, who owns the state, and what actually happens between typing `kubectl apply` and a container running on a node. So I built myself a visual cheat sheet, and I am sharing it here in case it helps you too.

Hover over or click any component in the diagram below. The panel underneath explains what that piece does and highlights the paths it talks over.

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

## The one rule that made it click

Every arrow in that diagram either starts or ends at the **api-server**. That is not a simplification for the drawing. It is how Kubernetes is built. `kubectl` talks to the api-server. The scheduler talks to the api-server. The controllers talk to the api-server. Every kubelet on every node talks to the api-server. Nothing talks to **etcd** except the api-server.

Once I internalised that, the rest stopped looking like a pile of daemons and started looking like one hub with a set of watchers around it.

## The control plane: the brain

The control plane decides what *should* be running. It does not run your workloads.

- **api-server**: the front door. It validates every request, enforces authentication and RBAC, and is the only thing allowed to read from or write to etcd.
- **etcd**: a consistent key-value store that holds the entire cluster state. Every object you have ever applied lives here. If you back up only one thing in a cluster, back up this.
- **controller-manager**: a bundle of reconcile loops. Each controller watches the api-server for a kind of object, compares desired state with observed state, and asks the api-server to fix the difference. A Pod crashed and the Deployment says three replicas? The ReplicaSet controller notices and requests a new Pod.
- **scheduler**: watches for Pods that have no node assigned. It filters out nodes that cannot run the Pod, scores the ones that can on resource requests, affinity, taints and tolerations, and writes the chosen node back to the Pod through the api-server. That is all it does. It never starts anything itself.

## The worker node: the muscle

Worker nodes run the workloads. Each node runs the same small set of agents.

- **kubelet**: the node's agent. It watches the api-server for Pods bound to its node, makes sure their containers are running and healthy, runs the probes, and reports status back. Coming from years of babysitting daemons by hand, this is the piece I find most satisfying.
- **container runtime**: containerd or CRI-O. The kubelet talks to it over the Container Runtime Interface to pull images and start and stop containers. Kubernetes never touches a container directly.
- **kube-proxy and the CNI plugin**: networking. The CNI plugin gives each Pod an IP and wires it into the cluster network. kube-proxy programs the node so that traffic to a Service's virtual IP lands on a healthy Pod behind it.
- **Pod**: the smallest thing Kubernetes will schedule. One or more containers sharing a network namespace, an IP address and volumes. You almost never create Pods directly. A Deployment creates a ReplicaSet, and the ReplicaSet creates the Pods.

## What actually happens on `kubectl apply`

This is the sequence I had to trace by hand before the diagram made sense.

1. `kubectl` sends your Deployment manifest to the api-server, which validates it and writes it to etcd.
2. The Deployment controller sees a new Deployment and creates a ReplicaSet. The ReplicaSet controller sees that and creates the Pods. Both go through the api-server, and both end up in etcd.
3. The scheduler sees Pods with no node assigned, picks a node for each one, and writes the binding back.
4. The kubelet on the chosen node sees a Pod bound to it, asks the container runtime to pull the image and start the containers, and reports the Pod's status back to the api-server.
5. The CNI plugin gives the Pod an IP, and kube-proxy updates the routing rules so Service traffic can reach it.

Notice that nothing in that list is pushed to a node. The control plane never reaches out and says "run this". Every component watches the api-server and acts on what it sees. That pull model is why a node can lose contact with the control plane and keep its Pods running, and why the whole thing recovers so calmly when a piece restarts.

## What the cheat sheet does not cover

This is the core architecture only. Services, Ingress, persistent storage, ConfigMaps and Secrets, RBAC and namespaces all sit on top of this model, and they all follow the same pattern: an object in etcd, a controller watching it, and the api-server in the middle. I will extend the diagram as I get further in. If you spot something wrong or misleading, I would genuinely like to hear it.
