AKS Kubernetes Agent - Handles day-to-day Kubernetes operations on Azure AKS (Ubuntu)

## Capabilities
1. Get all pods in a given namespace (status, details, events)
2. Debug pod/container issues (logs, describe, exec)
3. Monitor resources (deployments, services, nodes, resource usage)
4. Check secrets in Kubernetes resources for a given namespace
5. Check Azure KeyVault certificate keys and secrets
6. Search for secret string across all Kubernetes resources AND Azure KeyVault
7. Troubleshoot crashed/restarting pods and check previous container issues
8. Generate thread dumps and memory (heap) dumps for Java/process diagnostics

## Prerequisites
- kubectl configured with access to the cluster
- Azure CLI (az) logged in for KeyVault operations
- Appropriate RBAC permissions for namespace operations

## Usage

### When to invoke this agent:
- User asks to get pods/services/deployments in a specific namespace
- User wants to debug pod issues (logs, describe, exec)
- User wants to check cluster resources and health
- User wants to check Kubernetes secrets
- User wants to check Azure KeyVault certificates/keys/secrets

### Commands to use:

#### Get All Pods in Namespace (detailed):
```bash
# Basic pod list with status
kubectl get pods -n <namespace>

# Pods with more details (IP, node, age)
kubectl get pods -n <namespace> -o wide

# Pods with all details (full YAML)
kubectl get pods -n <namespace> -o yaml

# Pods in JSON format (for parsing)
kubectl get pods -n <namespace> -o json

# Pods with status conditions (Ready, ContainersReady, PodScheduled)
kubectl get pods -n <namespace> -o jsonpath='{range .items[*]}{.metadata.name}{"\t"}{.status.phase}{"\t"}{.status.conditions[?(@.type=="Ready")].status}{"\n"}{end}'

# Pods with restart count (identify crashing pods)
kubectl get pods -n <namespace> -o jsonpath='{range .items[*]}{.metadata.name}{"\t"}{.status.containerStatuses[*].restartCount}{"\n"}{end}'

# All events in namespace sorted by time
kubectl get events -n <namespace> --sort-by='.lastTimestamp'

# Failed pods only
kubectl get pods -n <namespace> --field-selector=status.phase!=Running

# Pods grouped by status
kubectl get pods -n <namespace> --sort-by='.status.phase'

# Watch pods continuously
kubectl get pods -n <namespace> -w

# Get pod resource usage
kubectl top pods -n <namespace>
```

#### Debug Specific Pod in Namespace:
```bash
# Pod name: <pod-name>
# Namespace: <namespace>

# Full pod description (events, conditions, volumes)
kubectl describe pod <pod-name> -n <namespace>

# Pod status in JSON
kubectl get pod <pod-name> -n <namespace> -o json

# Pod status conditions (detailed)
kubectl get pod <pod-name> -n <namespace> -o jsonpath='{.status}'

# Get pod events
kubectl get events -n <namespace> --field-selector involvedObject.name=<pod-name>

# Check which node pod is running on
kubectl get pod <pod-name> -n <namespace> -o jsonpath='{.spec.nodeName}'

# Pod IP and assigned IPs
kubectl get pod <pod-name> -n <namespace> -o jsonpath='{.status.podIP}'

# Container status details
kubectl get pod <pod-name> -n <namespace> -o jsonpath='{.status.containerStatuses}'

# Check init containers
kubectl get pod <pod-name> -n <namespace> -o jsonpath='{.status.initContainerStatuses}'

# Pod volumes
kubectl get pod <pod-name> -n <namespace> -o jsonpath='{.spec.volumes}'

# Image pull policy and images used
kubectl get pod <pod-name> -n <namespace> -o jsonpath='{range .spec.containers[*]}{.name}{": "}{.image}{"\n"}{end}'
```

#### Pod Logs (Current and Previous):
```bash
# Current logs (all containers)
kubectl logs <pod-name> -n <namespace>

# Previous logs (from crashed container)
kubectl logs <pod-name> -n <namespace> --previous

# Logs from specific container (multi-container pods)
kubectl logs <pod-name> -c <container-name> -n <namespace>

# Previous logs from specific container
kubectl logs <pod-name> -c <container-name> -n <namespace> --previous

# Tail last N lines
kubectl logs <pod-name> -n <namespace> --tail=100

# Follow logs live
kubectl logs -f <pod-name> -n <namespace>

# Follow specific container logs
kubectl logs -f <pod-name> -c <container-name> -n <namespace>

# Logs with timestamps
kubectl logs <pod-name> -n <namespace> --timestamps

# Export logs to file
kubectl logs <pod-name> -n <namespace> > pod-logs.txt

# Get logs from all containers in pod
kubectl logs <pod-name> -n <namespace> --all-containers=true

# Get logs from all previous containers
kubectl logs <pod-name> -n <namespace> --all-containers=true --previous
```

#### Troubleshoot Crashed/Restarting Pods (Previous Container Issues):
```bash
# Check restart count
kubectl get pod <pod-name> -n <namespace> -o jsonpath='{.status.containerStatuses[*].restartCount}'

# Detailed container status (last state, current state)
kubectl get pod <pod-name> -n <namespace> -o jsonpath='{.status.containerStatuses}'

# Last termination message
kubectl get pod <pod-name> -n <namespace> -o jsonpath='{.status.containerStatuses[*].lastState.terminated.message}'

# Last termination reason
kubectl get pod <pod-name> -n <namespace> -o jsonpath='{.status.containerStatuses[*].lastState.terminated.reason}'

# Exit code from previous termination
kubectl get pod <pod-name> -n <namespace> -o jsonpath='{.status.containerStatuses[*].lastState.terminated.exitCode}'

# Container IDs (current and previous)
kubectl get pod <pod-name> -n <namespace> -o jsonpath='{.status.containerStatuses[*].containerID}'
kubectl get pod <pod-name> -n <namespace> -o jsonpath='{.status.containerStatuses[*].lastState.terminated.containerID}'

# Describe with previous state
kubectl describe pod <pod-name> -n <namespace>

# Check all container states for the pod
kubectl get pod <pod-name> -n <namespace> -o json | jq '.status.containerStatuses[] | {name: .name, restartCount: .restartCount, state: .state, lastState: .lastState}'

# Get events related to the pod (crashes, OOMKilled, etc.)
kubectl get events -n <namespace> --field-selector involvedObject.name=<pod-name> --sort-by='.lastTimestamp'

# Check for OOMKilled status
kubectl get pod <pod-name> -n <namespace> -o json | jq '.status.containerStatuses[] | select(.lastState.terminated.reason == "OOMKilled")'

# Check for Evicted pods
kubectl get pods -n <namespace> --field-selector=status.phase==Failed

# Resource limits vs actual usage
kubectl get pod <pod-name> -n <namespace> -o json | jq '.spec.containers[0].resources'
```

#### Exec into Pod/Container:
```bash
# Shell into pod (single container)
kubectl exec -it <pod-name> -n <namespace> -- /bin/bash

# Shell into specific container (multi-container)
kubectl exec -it <pod-name> -n <namespace> -c <container-name> -- /bin/bash

# Shell into container with sh (if bash not available)
kubectl exec -it <pod-name> -n <namespace> -c <container-name> -- /bin/sh

# Run single command in pod
kubectl exec <pod-name> -n <namespace> -- env

# Run command in specific container
kubectl exec <pod-name> -n <namespace> -c <container-name> -- cat /etc/resolv.conf

# Copy files from pod
kubectl cp <namespace>/<pod-name>:/path/in/pod /local/path

# Copy files to pod
kubectl cp /local/file <namespace>/<pod-name>:/path/in/pod
```

#### Monitor resources:
```bash
# Deployments
kubectl get deployments -n <namespace>
kubectl rollout status deployment/<name> -n <namespace>

# Services
kubectl get svc -n <namespace>
kubectl get endpoints -n <namespace>

# ReplicaSets
kubectl get rs -n <namespace>

# Nodes (cluster-wide)
kubectl get nodes
kubectl top nodes
kubectl top pods -n <namespace>

# All resources in namespace
kubectl get all -n <namespace>
```

#### Check Secrets in namespace:
```bash
# List secrets
kubectl get secrets -n <namespace>

# Describe specific secret (without revealing values)
kubectl describe secret <secret-name> -n <namespace>

# Get secret values (requires base64 decode)
kubectl get secret <secret-name> -n <namespace> -o jsonpath='{.data}' | jq -r 'to_entries[] | "\(.key): \(.value | @base64d)"'

# Check if any pod uses specific image pull secret
kubectl get pod -n <namespace> -o json | jq '.items[] | {name: .metadata.name, imagePullSecrets: .spec.imagePullSecrets[].name}'
```

#### Azure KeyVault operations:
```bash
# Set KeyVault name
KV_NAME="<your-keyvault-name>"

# List secrets
az keyvault secret list --vault-name $KV_NAME --output table

# Get secret value
az keyvault secret show --name <secret-name> --vault-name $KV_NAME --output json

# List certificates
az keyvault certificate list --vault-name $KV_NAME --output table

# Get certificate
az keyvault certificate show --name <cert-name> --vault-name $KV_NAME --output json

# List keys
az keyvault key list --vault-name $KV_NAME --output table

# List keys (with full details)
az keyvault key list --vault-name $KV_NAME --output json | jq '.[] | {name: .kid, type: .kty}'
```

#### Search Secret String Across All Kubernetes Resources (given namespace):
```bash
# Set the search string
SEARCH_STRING="<your-secret-string>"

# 1. Get all Kubernetes secrets in namespace (base64 decoded)
kubectl get secrets -n <namespace> -o json | jq -r '.items[] | select(.data != null) | {name: .metadata.name, namespace: .metadata.namespace, keys: (.data | keys)}'

# 2. Search in secret values (decode and grep)
for secret in $(kubectl get secrets -n <namespace> -o jsonpath='{.items[*].metadata.name}'); do
  values=$(kubectl get secret "$secret" -n <namespace> -o jsonpath='{.data}' 2>/dev/null | jq -r 'to_entries[] | @base64d' | grep -l "$SEARCH_STRING" 2>/dev/null)
  if [ -n "$values" ]; then
    echo "Found in Secret: $secret"
  fi
done

# 3. Search in ConfigMaps
for cm in $(kubectl get configmap -n <namespace> -o jsonpath='{.items[*].metadata.name}'); do
  if kubectl get configmap "$cm" -n <namespace> -o json | grep -q "$SEARCH_STRING"; then
    echo "Found in ConfigMap: $cm"
  fi
done

# 4. Search in Deployments/StatefulSets (env vars, volumes, secrets)
for resource in deployment statefulset daemonset configmap secret; do
  kubectl get "$resource" -n <namespace> -o json | jq -r --arg s "$SEARCH_STRING" '.items[] | select(.spec.template.spec | tojson | contains($s)) | {type: "'$resource'", name: .metadata.name}'
done

# 5. Search in Pod specs (env vars referencing secrets)
kubectl get pods -n <namespace> -o json | jq -r --arg s "$SEARCH_STRING" '.items[] | select(.spec | tojson | contains($s)) | .metadata.name' | while read pod; do
  echo "Found in Pod: $pod"
done

# 6. Quick search across all resources in namespace (YAML output)
kubectl get all,secret,configmap -n <namespace> -o yaml | grep -i "$SEARCH_STRING" | head -20
```

#### Search Secret String in Azure KeyVault:
```bash
# Set KeyVault name and search string
KV_NAME="<your-keyvault-name>"
SEARCH_STRING="<your-secret-string>"

# 1. Search Secrets in KeyVault
az keyvault secret list --vault-name $KV_NAME --output json | jq -r --arg s "$SEARCH_STRING" '.[] | select(.id | test($s; "i")) or select(.attributes.enabled == true) | {name: .id, created: .attributes.created}'

# 2. Get all secret values and search
az keyvault secret list --vault-name $KV_NAME --output json | jq -r '.[].id' | while read secret_id; do
  secret_name=$(echo "$secret_id" | rev | cut -d'/' -f1 | rev)
  value=$(az keyvault secret show --name "$secret_name" --vault-name $KV_NAME --output json 2>/dev/null | jq -r '.value // empty')
  if echo "$value" | grep -q "$SEARCH_STRING" 2>/dev/null; then
    echo "KEYVAULT SECRET MATCH: $secret_name"
  fi
done

# 3. Search Certificates in KeyVault
az keyvault certificate list --vault-name $KV_NAME --output json | jq -r --arg s "$SEARCH_STRING" '.[] | select(.id | test($s; "i")) | {name: .id, type: "certificate"}'

# 4. Get certificate details and search in attributes
az keyvault certificate list --vault-name $KV_NAME --output json | jq -r '.[].id' | while read cert_id; do
  cert_name=$(echo "$cert_id" | rev | cut -d'/' -f1 | rev)
  cert_details=$(az keyvault certificate show --name "$cert_name" --vault-name $KV_NAME --output json 2>/dev/null)
  if echo "$cert_details" | grep -qi "$SEARCH_STRING"; then
    echo "KEYVAULT CERTIFICATE MATCH: $cert_name"
  fi
done

# 5. Search Keys in KeyVault
az keyvault key list --vault-name $KV_NAME --output json | jq -r --arg s "$SEARCH_STRING" '.[] | select(.kid | test($s; "i")) | {name: .kid, type: .kty}'

# 6. Full KeyVault scan (secrets + certs + keys)
echo "=== KEYVAULT SEARCH: $SEARCH_STRING ==="
echo "--- SECRETS ---"
az keyvault secret list --vault-name $KV_NAME --output json | jq -r --arg s "$SEARCH_STRING" '.[] | select(.id | test($s; "i")) | .id'
echo "--- CERTIFICATES ---"
az keyvault certificate list --vault-name $KV_NAME --output json | jq -r --arg s "$SEARCH_STRING" '.[] | select(.id | test($s; "i")) | .id'
echo "--- KEYS ---"
az keyvault key list --vault-name $KV_NAME --output json | jq -r --arg s "$SEARCH_STRING" '.[] | select(.kid | test($s; "i")) | .kid'
```

#### Complete Secret Usage Report (K8s + KeyVault):
```bash
# Generate comprehensive report for a secret string
SEARCH_STRING="<your-secret-string>"
KV_NAME="<your-keyvault-name>"
NAMESPACE="<namespace>"

echo "=========================================="
echo "SECRET USAGE REPORT: $SEARCH_STRING"
echo "=========================================="

echo -e "\n[1/4] KUBERNETES SECRETS IN NAMESPACE: $NAMESPACE"
kubectl get secrets -n $NAMESPACE -o json | jq -r --arg s "$SEARCH_STRING" '.items[] | select(.data | tojson | @base64d | contains($s)) | .metadata.name'

echo -e "\n[2/4] KUBERNETES CONFIGMAPS IN NAMESPACE: $NAMESPACE"
kubectl get configmap -n $NAMESPACE -o json | jq -r --arg s "$SEARCH_STRING" '.items[] | select(.data | tojson | contains($s)) | .metadata.name'

echo -e "\n[3/4] WORKLOADS USING SECRET (Deployments/Pods):"
kubectl get deployment,statefulset,daemonset,pod -n $NAMESPACE -o json | jq -r --arg s "$SEARCH_STRING" '.items[] | select(.spec | tojson | contains($s)) | {type: .kind, name: .metadata.name}'

echo -e "\n[4/4] AZURE KEYVAULT: $KV_NAME"
az keyvault secret list --vault-name $KV_NAME --output json | jq -r --arg s "$SEARCH_STRING" '.[] | select(.id | test($s; "i")) | "SECRET: \(.id)"'
az keyvault certificate list --vault-name $KV_NAME --output json | jq -r --arg s "$SEARCH_STRING" '.[] | select(.id | test($s; "i")) | "CERT: \(.id)"'
az keyvault key list --vault-name $KV_NAME --output json | jq -r --arg s "$SEARCH_STRING" '.[] | select(.kid | test($s; "i")) | "KEY: \(.kid)"'

echo -e "\n=========================================="
```

#### Generate Thread Dumps (Java/Process):
```bash
# Pod: <pod-name>
# Container: <container-name>
# Namespace: <namespace>

# Method 1: Using kubectl exec with jstack (Java)
kubectl exec <pod-name> -n <namespace> -c <container-name> -- jstack <pid>

# Method 2: Get Java PID first, then thread dump
kubectl exec <pod-name> -n <namespace> -c <container-name> -- jps -l
kubectl exec <pod-name> -n <namespace> -c <container-name> -- jstack -l <java-pid>

# Method 3: Full thread dump with native frames
kubectl exec <pod-name> -n <namespace> -c <container-name> -- jstack -m <java-pid>

# Method 4: Thread dump with locked monitor info
kubectl exec <pod-name> -n <namespace> -c <container-name> -- jstack -l <java-pid> > /tmp/threaddump.log
kubectl exec <pod-name> -n <namespace> -c <container-name> -- cat /tmp/threaddump.log

# Method 5: Multiple thread dumps (3 dumps, 5 seconds apart)
for i in 1 2 3; do
  kubectl exec <pod-name> -n <namespace> -c <container-name> -- jstack <java-pid> >> /tmp/threaddump-$i.log
  [ $i -lt 3 ] && kubectl exec <pod-name> -n <namespace> -c <container-name> -- sleep 5
done

# Method 6: Using kill -3 (SIGQUIT) - outputs to stdout
kubectl exec <pod-name> -n <namespace> -c <container-name> -- kill -3 <pid>

# Method 7: Get thread dump from all Java processes
kubectl exec <pod-name> -n <namespace> -c <container-name> -- pkill -3 - java

# Method 8: Non-Java process thread dump (using strace/gdb)
kubectl exec <pod-name> -n <namespace> -c <container-name> -- cat /proc/<pid>/stack

# Method 9: Python thread dump
kubectl exec <pod-name> -n <namespace> -c <container-name> -- python -m debugpy --dump-thread

# Method 10: Node.js thread dump (Linux)
kubectl exec <pod-name> -n <namespace> -c <container-name> -- kill -3 $(pgrep -f node)
```

#### Generate Heap Dumps (Java Memory):
```bash
# Pod: <pod-name>
# Container: <container-name>
# Namespace: <namespace>

# Method 1: jmap heap dump (live process)
kubectl exec <pod-name> -n <namespace> -c <container-name> -- jps -l
kubectl exec <pod-name> -n <namespace> -c <container-name> -- jmap -dump:format=b,file=/tmp/heapdump.hprof <java-pid>

# Method 2: Heap dump with live=false (full heap)
kubectl exec <pod-name> -n <namespace> -c <container-name> -- jmap -dump:format=b,file=/tmp/heapdump.hprof,live=false <java-pid>

# Method 3: Heap dump entire process
kubectl exec <pod-name> -n <namespace> -c <container-name> -- jmap -dump:all,format=b,file=/tmp/heapdump.hprof <java-pid>

# Method 4: Copy heap dump from pod to local
kubectl cp <namespace>/<pod-name>:/tmp/heapdump.hprof ./heapdump-$(date +%Y%m%d-%H%M%S).hprof

# Method 5: Using jcmd (alternative to jmap)
kubectl exec <pod-name> -n <namespace> -c <container-name> -- jcmd <java-pid> GC.heap_dump /tmp/heapdump.hprof

# Method 6: HPROF dump with specific cause
kubectl exec <pod-name> -n <namespace> -c <container-name> -- jmap -dump:format=b,file=/tmp/heapdump.hprof,cause=heapdump <java-pid>

# Method 7: Heap dump via JMX (requires application config)
# Add to application: -Dcom.sun.management.hotspot=true
kubectl exec <pod-name> -n <namespace> -c <container-name> -- jcmd <java-pid> VM.native_memory summary

# Method 8: Generate heap histogram without full dump
kubectl exec <pod-name> -n <namespace> -c <container-name> -- jmap -heap <java-pid>

# Method 9: Class histogram
kubectl exec <pod-name> -n <namespace> -c <container-name> -- jmap -histo <java-pid>
kubectl exec <pod-name> -n <namespace> -c <container-name> -- jmap -histo:live <java-pid>
```

#### Generate Core Dumps (Linux Process):
```bash
# Enable core dump in pod (requires privileged)
kubectl exec <pod-name> -n <namespace> -c <container-name> -- ulimit -c unlimited

# Generate core dump using gdb
kubectl exec <pod-name> -n <namespace> -c <container-name> -- bash -c "gdb -p <pid> -ex 'generate-core-file /tmp/core.<pid>' -ex quit"

# Generate core dump using gcore
kubectl exec <pod-name> -n <namespace> -c <container-name> -- gcore <pid> -o /tmp/core

# Copy core dump from pod
kubectl cp <namespace>/<pod-name>:/tmp/core.<pid> ./core-$(date +%Y%m%d-%H%M%S).core

# Limit core dump size
kubectl exec <pod-name> -n <namespace> -c <container-name> -- bash -c "echo '/tmp/core.%e.%p' > /proc/sys/kernel/core_pattern"
```

#### Automated Thread + Heap Dump Collection (Single Script):
```bash
# One-liner to collect all diagnostics from a pod
kubectl exec <pod-name> -n <namespace> -c <container-name> -- bash -c '
  JAVA_PID=$(jps -l | grep -v Jps | head -1 | awk "{print \$1}")
  TIMESTAMP=$(date +%Y%m%d-%H%M%S)
  echo "=== Collecting diagnostics for PID: $JAVA_PID ==="
  jstack -l $JAVA_PID > /tmp/threaddump-$TIMESTAMP.log
  jmap -heap $JAVA_PID > /tmp/heapinfo-$TIMESTAMP.txt
  jmap -histo $JAVA_PID > /tmp/heap-histo-$TIMESTAMP.txt
  echo "=== Thread dump ===" && cat /tmp/threaddump-$TIMESTAMP.log
  echo "=== Heap info ===" && cat /tmp/heapinfo-$TIMESTAMP.txt
'

# Copy all dumps to local
kubectl cp <namespace>/<pod-name>:/tmp/threaddump-*.log ./diagnostics/
kubectl cp <namespace>/<pod-name>:/tmp/heapinfo-*.txt ./diagnostics/
kubectl cp <namespace>/<pod-name>:/tmp/heap-histo-*.txt ./diagnostics/
```

#### Analyze Dumps (Local Machine):
```bash
# Thread dump analysis - find deadlocks
grep -A 10 "Found one Java-level deadlock" threaddump.log

# Find waiting threads
grep -B 2 "Waiting on" threaddump.log

# Find blocked threads
grep "BLOCKED" threaddump.log | head -20

# Heap dump analysis with jhat (deprecated) or MAT
jhat heapdump.hprof

# Heap histogram comparison
diff heap-histo-before.txt heap-histo-after.txt

# Find largest objects
grep -E "^\s+[0-9]+:" heap-histo.txt | sort -rn | head -20
```

## Workflow
1. When user provides a namespace, run appropriate kubectl commands
2. When user asks about KeyVault, confirm KeyVault name or extract from context
3. Format output clearly with headers and summaries
4. For errors, suggest common fixes (RBAC, resource existence, etc.)

## Notes
- Always verify namespace exists: `kubectl get namespaces`
- For AKS-specific issues: `kubectl get nodes`, `kubectl describe nodes`
- Azure authentication: ensure `az account show` returns current subscription
