# AKS Kubernetes Agent - Compact Prompt

```
AKS Kubernetes Agent - Multi-context, Cron-safe, Python/Bash CLI for Azure AKS Ubuntu.

CONTEXT: Takes -ctx <context> -ns <namespace> upfront. Auto-switches context.

PREREQUISITES: kubectl, az cli, jq. KUBECONFIG=~/.kube/config_*.yaml

ACTIONS: list-contexts | pods | details -p <pod> | logs -p <pod> [--previous] | troubleshoot -p <pod> | secrets | search-secret -s <string> | monitor | thread-dump -p <pod> | heap-dump -p <pod> | keyvault -kv <name> | all

EXAMPLES:
./aks-agent-multi.sh -ctx prod-cluster -ns production -a pods
./aks-agent-multi.sh -ctx dev -ns dev -p xyz-123 -a troubleshoot
./aks-agent-multi.sh -ctx prod -ns production -p web-app -a heap-dump
./aks-agent-multi.sh -ctx prod -ns production -s "db-password" -a search-secret

CRON: Source aks-cron-env.sh first.
FILES: aks-agent-multi.sh | aks-agent-multi.py | aks-cron-env.sh

GITHUB ACTIONS: .github/workflows/aks-*.yml
- aks-monitor.yml       : Schedule/Manual pod monitoring
- aks-diagnostics.yml   : Thread/heap dumps
- aks-secret-scan.yml   : Secret usage search
- aks-cluster-health.yml: Node/pod health
- aks-pod-health.yml    : Pod health + alerts
```
