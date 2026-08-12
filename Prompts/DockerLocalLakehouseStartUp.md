---
title: "Local Lakehouse Startup (Bash)"
category: "Docker"
tags: [docker, bash]
description: "Bash script to run in the beginning of a docker session for project Local Lakehouse"
---

sudo sysctl -w vm.max_map_count=2000000
sudo swapoff -a