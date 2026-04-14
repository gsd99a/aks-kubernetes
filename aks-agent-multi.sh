#!/bin/bash
# AKS Kubernetes Agent - Multi-Context Support
# Usage: ./aks-agent.sh -ctx <context> -ns <namespace> [options]
# Auto-detects config files from ~/.kube/config_*.yaml
# CRON-SAFE: Includes proper PATH setup for cron jobs

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m'

# ============================================
# CRON-SAFE ENVIRONMENT SETUP
# ============================================
setup_cron_environment() {
    # Add common paths for kubectl and tools
    export PATH="/usr/local/bin:/usr/bin:/bin:$HOME/go/bin:$HOME/.local/bin:$HOME/bin:$PATH"
    
    # Azure CLI paths
    export PATH="$PATH:/usr/local/az-cli/bin:/opt/az/bin:$HOME/.azure/bin"
    
    # Find kubectl if not in PATH
    if ! command -v kubectl &> /dev/null; then
        for path in /usr/local/bin/kubectl /usr/bin/kubectl $HOME/.kube/kubectl $HOME/bin/kubectl; do
            if [ -f "$path" ]; then
                export PATH="$(dirname $path):$PATH"
                break
            fi
        done
    fi
    
    # Find az CLI if not in PATH
    if ! command -v az &> /dev/null; then
        for path in /usr/local/bin/az /usr/bin/az $HOME/.azure/bin/az; do
            if [ -f "$path" ]; then
                export PATH="$(dirname $path):$PATH"
                break
            fi
        done
    fi
    
    # Kubernetes config directory
    export KUBECONFIG="${KUBECONFIG:-$HOME/.kube/config}"
    
    # Azure CLI config
    export AZURE_CONFIG_DIR="${AZURE_CONFIG_DIR:-$HOME/.azure}"
    
    # Common kubectl plugin paths
    export PATH="$PATH:$HOME/.krew/bin"
}

# Initialize cron-safe environment
setup_cron_environment

# Variables
CONTEXT=""
NAMESPACE=""
KUBECONFIG_PATH=""
POD_NAME=""
CONTAINER=""
SEARCH_STRING=""
KEYVAULT=""
ACTION=""

show_help() {
    echo -e "${BOLD}AKS Kubernetes Agent - Multi-Context${NC}"
    echo """
Usage:
  $0 -ctx <context> -ns <namespace> [options]

Required:
  -ctx, --context        Kubernetes context name
  -ns, --namespace       Kubernetes namespace

Optional:
  -kube, --kubeconfig    Path to kubeconfig file (auto-detected from ~/.kube)
  -p, --pod              Pod name for pod-specific commands
  -c, --container        Container name
  -s, --search           Search string for secret search
  -kv, --keyvault        Azure KeyVault name
  -a, --action           Action to perform

Actions:
  list-contexts           List all available contexts
  pods                    List all pods
  details                 Get pod details
  logs                    Get pod logs
  troubleshoot            Troubleshoot pod (crashes/restarts)
  secrets                 List secrets
  search-secret           Search secret usage
  monitor                 Monitor all resources
  thread-dump             Generate thread dump
  heap-dump               Generate heap dump
  all                     Full namespace overview

Examples:
  ${GREEN}# List all available contexts${NC}
  $0 --list-contexts

  ${GREEN}# Get all pods in production${NC}
  $0 -ctx prod-cluster -ns production -a pods

  ${GREEN}# Troubleshoot crashing pod${NC}
  $0 -ctx dev-cluster -ns dev -p xyz-123 -a troubleshoot

  ${GREEN}# Generate thread dump${NC}
  $0 -ctx prod-cluster -ns production -p web-app-1 -a thread-dump

  ${GREEN}# Search for secret usage${NC}
  $0 -ctx staging -ns staging -s \"db-password\" -a search-secret
"""
    exit 0
}

list_contexts() {
    echo -e "\n${BOLD}${CYAN}========================================${NC}"
    echo -e "${BOLD}Available Kubernetes Contexts${NC}"
    echo -e "${BOLD}${CYAN}========================================${NC}"
    
    echo -e "\n${YELLOW}From ~/.kube/config_*.yaml:${NC}"
    if ls ~/.kube/config_*.yaml ~/.kube/config_*.yml 2>/dev/null; then
        for config in ~/.kube/config_*.yaml ~/.kube/config_*.yml; do
            echo -e "\n${CYAN}File: $config${NC}"
            KUBECONFIG="$config" kubectl config get-contexts -o name 2>/dev/null | while read ctx; do
                [ -n "$ctx" ] && echo -e "  - ${GREEN}$ctx${NC}"
            done
        done
    else
        echo "  No config_*.yaml files found in ~/.kube"
    fi
    
    echo -e "\n${YELLOW}From default kubeconfig:${NC}"
    kubectl config get-contexts -o name 2>/dev/null | while read ctx; do
        [ -n "$ctx" ] && echo -e "  - ${GREEN}$ctx${NC}"
    done
    
    echo ""
}

switch_context() {
    local ctx=$1
    local kubeconfig=$2
    
    if [ -n "$kubeconfig" ] && [ -f "$kubeconfig" ]; then
        echo -e "${CYAN}Using kubeconfig: $kubeconfig${NC}"
        export KUBECONFIG="$kubeconfig"
    fi
    
    kubectl config use-context "$ctx" >/dev/null 2>&1
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓ Switched to context: $ctx${NC}"
        if [ -n "$NAMESPACE" ]; then
            echo -e "${CYAN}Using namespace: $NAMESPACE${NC}"
        fi
    else
        echo -e "${RED}✗ Failed to switch to context: $ctx${NC}"
        exit 1
    fi
}

run_cmd() {
    local cmd="$1"
    echo -e "\n${CYAN}>>> $cmd${NC}"
    eval "$cmd"
}

get_pods() {
    echo -e "\n${BOLD}${CYAN}========================================${NC}"
    echo -e "${BOLD}Pods in Namespace: $NAMESPACE${NC}"
    echo -e "${BOLD}${CYAN}========================================${NC}"
    run_cmd "kubectl get pods -n $NAMESPACE -o wide"
}

get_pod_details() {
    echo -e "\n${BOLD}${CYAN}========================================${NC}"
    echo -e "${BOLD}Pod Details: $POD_NAME${NC}"
    echo -e "${BOLD}${CYAN}========================================${NC}"
    run_cmd "kubectl describe pod $POD_NAME -n $NAMESPACE"
}

get_pod_logs() {
    echo -e "\n${BOLD}${CYAN}========================================${NC}"
    echo -e "${BOLD}Pod Logs: $POD_NAME${NC}"
    echo -e "${BOLD}${CYAN}========================================${NC}"
    
    local cmd="kubectl logs $POD_NAME -n $NAMESPACE"
    [ -n "$CONTAINER" ] && cmd="$cmd -c $CONTAINER"
    cmd="$cmd | tail -100"
    
    run_cmd "$cmd"
}

troubleshoot_pod() {
    echo -e "\n${BOLD}${CYAN}========================================${NC}"
    echo -e "${BOLD}Troubleshooting Pod: $POD_NAME${NC}"
    echo -e "${BOLD}${CYAN}========================================${NC}"
    
    echo -e "\n${YELLOW}[1] Status${NC}"
    run_cmd "kubectl get pod $POD_NAME -n $NAMESPACE -o jsonpath='{.status.phase}'"
    
    echo -e "\n${YELLOW}[2] Restart Count${NC}"
    run_cmd "kubectl get pod $POD_NAME -n $NAMESPACE -o jsonpath='{.status.containerStatuses[*].restartCount}'"
    
    echo -e "\n${YELLOW}[3] Exit Code${NC}"
    run_cmd "kubectl get pod $POD_NAME -n $NAMESPACE -o jsonpath='{.status.containerStatuses[*].lastState.terminated.exitCode}'"
    
    echo -e "\n${YELLOW}[4] Termination Message${NC}"
    run_cmd "kubectl get pod $POD_NAME -n $NAMESPACE -o jsonpath='{.status.containerStatuses[*].lastState.terminated.message}'"
    
    echo -e "\n${YELLOW}[5] OOMKilled Check${NC}"
    local reason=$(kubectl get pod "$POD_NAME" -n "$NAMESPACE" -o jsonpath='{.status.containerStatuses[*].lastState.terminated.reason}')
    if [[ "$reason" == "OOMKilled" ]]; then
        echo -e "${RED}⚠ Pod was OOMKilled!${NC}"
    else
        echo "Not OOMKilled"
    fi
    
    echo -e "\n${YELLOW}[6] Previous Logs${NC}"
    run_cmd "kubectl logs $POD_NAME -n $NAMESPACE --previous 2>&1 | tail -50"
    
    echo -e "\n${YELLOW}[7] Pod Events${NC}"
    run_cmd "kubectl get events -n $NAMESPACE --field-selector involvedObject.name=$POD_NAME --sort-by='.lastTimestamp'"
}

list_secrets() {
    echo -e "\n${BOLD}${CYAN}========================================${NC}"
    echo -e "${BOLD}Secrets in Namespace: $NAMESPACE${NC}"
    echo -e "${BOLD}${CYAN}========================================${NC}"
    run_cmd "kubectl get secrets -n $NAMESPACE"
}

search_secret_usage() {
    echo -e "\n${BOLD}${CYAN}========================================${NC}"
    echo -e "${BOLD}Searching for: '$SEARCH_STRING' in namespace: $NAMESPACE${NC}"
    echo -e "${BOLD}${CYAN}========================================${NC}"
    
    echo -e "\n${YELLOW}Kubernetes Secrets:${NC}"
    kubectl get secrets -n "$NAMESPACE" -o json 2>/dev/null | jq -r --arg s "$SEARCH_STRING" '.items[] | select(.data | tojson | @base64d | contains($s)) | .metadata.name' 2>/dev/null || echo "jq not available"
    
    echo -e "\n${YELLOW}ConfigMaps:${NC}"
    kubectl get configmap -n "$NAMESPACE" -o json 2>/dev/null | jq -r --arg s "$SEARCH_STRING" '.items[] | select(.data | tojson | contains($s)) | .metadata.name' 2>/dev/null || echo "jq not available"
    
    echo -e "\n${YELLOW}Deployments/Pods:${NC}"
    kubectl get deployment,statefulset,pod -n "$NAMESPACE" -o json 2>/dev/null | jq -r --arg s "$SEARCH_STRING" '.items[] | select(.spec | tojson | contains($s)) | "\(.kind): \(.metadata.name)"' 2>/dev/null || echo "jq not available"
}

monitor_namespace() {
    echo -e "\n${BOLD}${CYAN}========================================${NC}"
    echo -e "${BOLD}Monitoring Namespace: $NAMESPACE${NC}"
    echo -e "${BOLD}${CYAN}========================================${NC}"
    
    for resource in pods deployments services configmaps secrets ingresses; do
        echo -e "\n${YELLOW}$(echo $resource | tr '[:lower:]' '[:upper:]')${NC}"
        kubectl get $resource -n "$NAMESPACE" 2>/dev/null || echo "Resource not found or no access"
    done
    
    echo -e "\n${YELLOW}EVENTS${NC}"
    kubectl get events -n "$NAMESPACE" --sort-by='.lastTimestamp' 2>/dev/null
}

thread_dump() {
    echo -e "\n${BOLD}${CYAN}========================================${NC}"
    echo -e "${BOLD}Thread Dump: $POD_NAME${NC}"
    echo -e "${BOLD}${CYAN}========================================${NC}"
    
    local pid_cmd="kubectl exec $POD_NAME -n $NAMESPACE"
    [ -n "$CONTAINER" ] && pid_cmd="$pid_cmd -c $CONTAINER"
    pid_cmd="$pid_cmd -- jps -l 2>/dev/null | grep -v Jps | head -1 | awk '{print \$1}'"
    
    local java_pid=$(eval "$pid_cmd")
    
    if [ -z "$java_pid" ]; then
        echo -e "${RED}No Java process found!${NC}"
        return
    fi
    
    echo "Java PID: $java_pid"
    
    local dump_cmd="kubectl exec $POD_NAME -n $NAMESPACE"
    [ -n "$CONTAINER" ] && dump_cmd="$dump_cmd -c $CONTAINER"
    dump_cmd="$dump_cmd -- jstack -l $java_pid"
    
    eval "$dump_cmd"
    echo -e "${GREEN}✓ Thread dump complete${NC}"
}

heap_dump() {
    echo -e "\n${BOLD}${CYAN}========================================${NC}"
    echo -e "${BOLD}Heap Dump: $POD_NAME${NC}"
    echo -e "${BOLD}${CYAN}========================================${NC}"
    
    local pid_cmd="kubectl exec $POD_NAME -n $NAMESPACE"
    [ -n "$CONTAINER" ] && pid_cmd="$pid_cmd -c $CONTAINER"
    pid_cmd="$pid_cmd -- jps -l 2>/dev/null | grep -v Jps | head -1 | awk '{print \$1}'"
    
    local java_pid=$(eval "$pid_cmd")
    
    if [ -z "$java_pid" ]; then
        echo -e "${RED}No Java process found!${NC}"
        return
    fi
    
    echo "Java PID: $java_pid"
    
    local timestamp=$(date +%Y%m%d-%H%M%S)
    local filename="/tmp/heapdump-$timestamp.hprof"
    
    local dump_cmd="kubectl exec $POD_NAME -n $NAMESPACE"
    [ -n "$CONTAINER" ] && dump_cmd="$dump_cmd -c $CONTAINER"
    dump_cmd="$dump_cmd -- jmap -dump:format=b,file=$filename $java_pid"
    
    eval "$dump_cmd"
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓ Heap dump created: $filename${NC}"
        kubectl cp "$NAMESPACE/$POD_NAME:$filename" ./heapdump-$timestamp.hprof 2>/dev/null
        echo -e "${GREEN}✓ Saved: heapdump-$timestamp.hprof${NC}"
    fi
}

# Parse arguments
if [ $# -eq 0 ]; then
    show_help
fi

while [[ $# -gt 0 ]]; do
    case $1 in
        --list-contexts|-lc)
            list_contexts
            exit 0
            ;;
        -ctx|--context)
            CONTEXT="$2"
            shift 2
            ;;
        -ns|--namespace)
            NAMESPACE="$2"
            shift 2
            ;;
        -kube|--kubeconfig)
            KUBECONFIG_PATH="$2"
            shift 2
            ;;
        -p|--pod)
            POD_NAME="$2"
            shift 2
            ;;
        -c|--container)
            CONTAINER="$2"
            shift 2
            ;;
        -s|--search)
            SEARCH_STRING="$2"
            shift 2
            ;;
        -kv|--keyvault)
            KEYVAULT="$2"
            shift 2
            ;;
        -a|--action)
            ACTION="$2"
            shift 2
            ;;
        -h|--help)
            show_help
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

# Check prerequisites
if ! command -v kubectl &> /dev/null; then
    echo -e "${RED}✗ kubectl not found!${NC}"
    exit 1
fi

# Switch context
if [ -n "$CONTEXT" ]; then
    switch_context "$CONTEXT" "$KUBECONFIG_PATH"
else
    echo -e "${RED}✗ Context required! Use -ctx <context>${NC}"
    exit 1
fi

# Default action
[ -z "$ACTION" ] && ACTION="pods"

# Execute action
case $ACTION in
    pods)
        get_pods
        ;;
    details)
        [ -z "$POD_NAME" ] && echo "Pod name required!" && exit 1
        get_pod_details
        ;;
    logs)
        [ -z "$POD_NAME" ] && echo "Pod name required!" && exit 1
        get_pod_logs
        ;;
    troubleshoot)
        [ -z "$POD_NAME" ] && echo "Pod name required!" && exit 1
        troubleshoot_pod
        ;;
    secrets)
        list_secrets
        ;;
    search-secret)
        [ -z "$SEARCH_STRING" ] && echo "Search string required!" && exit 1
        search_secret_usage
        ;;
    monitor)
        monitor_namespace
        ;;
    thread-dump)
        [ -z "$POD_NAME" ] && echo "Pod name required!" && exit 1
        thread_dump
        ;;
    heap-dump)
        [ -z "$POD_NAME" ] && echo "Pod name required!" && exit 1
        heap_dump
        ;;
    all)
        get_pods
        list_secrets
        monitor_namespace
        ;;
    *)
        echo -e "${RED}Unknown action: $ACTION${NC}"
        show_help
        ;;
esac
