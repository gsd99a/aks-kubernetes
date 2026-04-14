# AKS Kubernetes Agent - Complete Summary

## Overview
An AI agent for day-to-day Kubernetes/AKS operations on Ubuntu. Handles debugging, monitoring, secrets management, and diagnostics.

---

## Capabilities (8 Core Functions)

| # | Capability | Description |
|---|------------|-------------|
| 1 | **Get All Pods** | List pods with status, restarts, IPs, events |
| 2 | **Debug Pods** | Logs, describe, exec into containers |
| 3 | **Monitor Resources** | Deployments, services, nodes, resource usage |
| 4 | **Check K8s Secrets** | List, inspect, decode secrets in namespace |
| 5 | **Azure KeyVault** | Check secrets, certificates, keys |
| 6 | **Search Secret Usage** | Find where a secret is used (K8s + KeyVault) |
| 7 | **Troubleshoot Pods** | Check previous containers, crash logs, exit codes |
| 8 | **Thread/Heap Dumps** | Generate Java diagnostics (thread, heap, core dumps) |

---

## Quick Start

### Usage Examples

```
# 1. Get all pods in a namespace
> "Get all pods in namespace production"

# 2. Debug a specific pod
> "Debug pod xyz-123 in namespace dev"

# 3. Troubleshoot crashed pod (check previous container)
> "Troubleshoot pod xyz-123 in namespace dev - check previous container"

# 4. Check secrets in namespace
> "Check secrets in namespace staging"

# 5. Search where a secret is used
> "Find where 'db-password' is used in namespace prod and keyvault myvault"

# 6. Generate thread dump
> "Generate thread dump for pod web-app-123 in namespace production"

# 7. Generate heap dump
> "Get heap dump for pod api-service in namespace prod"

# 8. Check Azure KeyVault
> "List all secrets in keyvault myvault"
```

---

## Prerequisites

```bash
# 1. kubectl configured with cluster access
kubectl get nodes

# 2. Azure CLI logged in
az login
az account show

# 3. jq installed (for JSON parsing)
apt install jq   # Ubuntu

# 4. RBAC permissions for namespace operations
```

---

## File Structure

```
C:\Opencode-project-working\
├── agents\
│   └── aks-agent.md          # Main agent file (all commands)
└── skills\
    └── aks-kubernetes-agent.json  # Skill definition
```

---

## Download Instructions

### Option 1: Copy Files Directly

```
Agent File:  C:\Opencode-project-working\agents\aks-agent.md
Skill File:  C:\Opencode-project-working\skills\aks-kubernetes-agent.json
```

### Option 2: Export/Backup

```bash
# On Windows (PowerShell)
Copy-Item -Path "C:\Opencode-project-working\agents\aks-agent.md" -Destination "$env:USERPROFILE\Desktop\aks-agent.md"
Copy-Item -Path "C:\Opencode-project-working\skills\aks-kubernetes-agent.json" -Destination "$env:USERPROFILE\Desktop\aks-kubernetes-skill.json"

# On Linux/Mac
cp /mnt/c/Opencode-project-working/agents/aks-agent.md ~/Desktop/
cp /mnt/c/Opencode-project-working/skills/aks-kubernetes-agent.json ~/Desktop/
```

### Option 3: Git Clone (if repo exists)

```bash
git clone <repository-url>
cd <repo>
```

---

## Command Reference by Task

### Task 1: Get All Pods
```bash
kubectl get pods -n <namespace>
kubectl get pods -n <namespace> -o wide
kubectl get events -n <namespace> --sort-by='.lastTimestamp'
kubectl top pods -n <namespace>
```

### Task 2: Debug Pod
```bash
kubectl describe pod <pod-name> -n <namespace>
kubectl logs <pod-name> -n <namespace>
kubectl logs <pod-name> -n <namespace> --previous
kubectl exec -it <pod-name> -n <namespace> -- /bin/bash
```

### Task 3: Troubleshoot Crashed Pod
```bash
# Check restart count
kubectl get pod <pod-name> -n <namespace> -o jsonpath='{.status.containerStatuses[*].restartCount}'

# Exit code
kubectl get pod <pod-name> -n <namespace> -o jsonpath='{.status.containerStatuses[*].lastState.terminated.exitCode}'

# Previous logs
kubectl logs <pod-name> -n <namespace> --previous

# Check OOMKilled
kubectl get pod <pod-name> -n <namespace> -o json | jq '.status.containerStatuses[] | select(.lastState.terminated.reason == "OOMKilled")'
```

### Task 4: Check Secrets
```bash
kubectl get secrets -n <namespace>
kubectl describe secret <secret-name> -n <namespace>
kubectl get secret <secret-name> -n <namespace> -o jsonpath='{.data}' | jq -r 'to_entries[] | "\(.key): \(.value | @base64d)"'
```

### Task 5: Azure KeyVault
```bash
az keyvault secret list --vault-name <keyvault-name>
az keyvault certificate list --vault-name <keyvault-name>
az keyvault key list --vault-name <keyvault-name>
```

### Task 6: Search Secret Usage
```bash
SEARCH_STRING="<secret-string>"
NAMESPACE="<namespace>"
KV_NAME="<keyvault-name>"

# K8s secrets
kubectl get secrets -n $NAMESPACE -o json | jq -r --arg s "$SEARCH_STRING" '.items[] | select(.data | tojson | @base64d | contains($s)) | .metadata.name'

# KeyVault
az keyvault secret list --vault-name $KV_NAME --output json | jq -r --arg s "$SEARCH_STRING" '.[] | select(.id | test($s; "i")) | .id'
```

### Task 7: Thread Dump
```bash
# Get Java PID
kubectl exec <pod-name> -n <namespace> -c <container> -- jps -l

# Thread dump
kubectl exec <pod-name> -n <namespace> -c <container> -- jstack -l <java-pid>

# Copy to local
kubectl cp <namespace>/<pod-name>:/tmp/threaddump.log ./threaddump.log
```

### Task 8: Heap Dump
```bash
# Generate heap dump
kubectl exec <pod-name> -n <namespace> -c <container> -- jmap -dump:format=b,file=/tmp/heapdump.hprof <java-pid>

# Copy to local
kubectl cp <namespace>/<pod-name>:/tmp/heapdump.hprof ./heapdump.hprof
```

---

## Troubleshooting Reference

| Issue | Command |
|-------|---------|
| Namespace not found | `kubectl get namespaces` |
| Auth problems | `az login` + `kubectl config current-context` |
| Permission denied | Check RBAC bindings |
| Pod not starting | `kubectl describe pod <name> -n <ns>` |
| CrashLoopBackOff | `kubectl logs <name> -n <ns> --previous` |
| OOMKilled | `kubectl get pod <name> -n <ns> -o json \| jq '.status.containerStatuses'` |

---

## Files Location

| File | Full Path |
|------|-----------|
| Agent | `C:\Opencode-project-working\agents\aks-agent.md` |
| Skill | `C:\Opencode-project-working\skills\aks-kubernetes-agent.json` |

---

## Support

For issues or feature requests, check:
- `kubectl get events -n <namespace>` for cluster events
- `kubectl describe nodes` for node health
- `az aks show -n <cluster-name> -g <resource-group>` for cluster info
