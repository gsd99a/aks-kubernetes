#!/bin/bash
# AKS Kubernetes Agent - Interactive Bash Script
# Run this on your Ubuntu box!

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m'

check_prerequisites() {
    echo -e "\n${BOLD}${CYAN}Checking Prerequisites...${NC}"
    
    if ! command -v kubectl &> /dev/null; then
        echo -e "${RED}✗ kubectl not found!${NC}"
        echo "  Install: sudo apt install kubectl"
        return 1
    fi
    echo -e "${GREEN}✓ kubectl found${NC}"
    
    if command -v az &> /dev/null; then
        echo -e "${GREEN}✓ Azure CLI found${NC}"
    fi
    
    if command -v jq &> /dev/null; then
        echo -e "${GREEN}✓ jq found${NC}"
    else
        echo -e "${YELLOW}⚠ jq not found (install: sudo apt install jq)${NC}"
    fi
}

list_namespaces() {
    echo -e "\n${BOLD}${CYAN}Namespaces:${NC}"
    kubectl get namespaces -o name | sed 's/namespace\///'
}

get_pods() {
    local ns=$1
    echo -e "\n${BOLD}${CYAN}Pods in namespace: $ns${NC}"
    kubectl get pods -n "$ns" -o wide
}

get_pod_details() {
    local pod=$1
    local ns=$2
    echo -e "\n${BOLD}${CYAN}Pod Details: $pod${NC}"
    kubectl describe pod "$pod" -n "$ns"
}

get_pod_logs() {
    local pod=$1
    local ns=$2
    local prev=$3
    local container=$4
    
    echo -e "\n${BOLD}${CYAN}Pod Logs: $pod${NC}"
    
    local cmd="kubectl logs $pod -n $ns"
    [ -n "$prev" ] && cmd="$cmd --previous"
    [ -n "$container" ] && cmd="$cmd -c $container"
    
    eval "$cmd | tail -100"
}

troubleshoot_pod() {
    local pod=$1
    local ns=$2
    
    echo -e "\n${BOLD}${CYAN}========================================${NC}"
    echo -e "${BOLD}Troubleshooting Pod: $pod${NC}"
    echo -e "${BOLD}${CYAN}========================================${NC}"
    
    echo -e "\n${YELLOW}[1/6] Status${NC}"
    echo "Status: $(kubectl get pod "$pod" -n "$ns" -o jsonpath='{.status.phase}')"
    
    echo -e "\n${YELLOW}[2/6] Restart Count${NC}"
    echo "Restarts: $(kubectl get pod "$pod" -n "$ns" -o jsonpath='{.status.containerStatuses[*].restartCount}')"
    
    echo -e "\n${YELLOW}[3/6] Container Status${NC}"
    kubectl get pod "$pod" -n "$ns" -o jsonpath='{.status.containerStatuses[*]}' | jq -r '.[] | "\(.name): \(.state | keys[0])"' 2>/dev/null || echo "jq not available"
    
    echo -e "\n${YELLOW}[4/6] Last Termination Message${NC}"
    local msg=$(kubectl get pod "$pod" -n "$ns" -o jsonpath='{.status.containerStatuses[*].lastState.terminated.message}')
    [ -n "$msg" ] && echo "$msg" || echo "(No previous termination)"
    
    echo -e "\n${YELLOW}[5/6] Exit Code${NC}"
    local exitcode=$(kubectl get pod "$pod" -n "$ns" -o jsonpath='{.status.containerStatuses[*].lastState.terminated.exitCode}')
    [ -n "$exitcode" ] && echo "Exit Code: $exitcode"
    
    echo -e "\n${YELLOW}[6/6] OOMKilled Check${NC}"
    local reason=$(kubectl get pod "$pod" -n "$ns" -o jsonpath='{.status.containerStatuses[*].lastState.terminated.reason}')
    if [[ "$reason" == "OOMKilled" ]]; then
        echo -e "${RED}⚠ Pod was OOMKilled!${NC}"
    else
        echo "Not OOMKilled"
    fi
    
    echo -e "\n${YELLOW}Previous Container Logs:${NC}"
    kubectl logs "$pod" -n "$ns" --previous 2>&1 | tail -50
    
    echo -e "\n${YELLOW}Pod Events:${NC}"
    kubectl get events -n "$ns" --field-selector involvedObject.name="$pod" --sort-by='.lastTimestamp'
}

list_secrets() {
    local ns=$1
    echo -e "\n${BOLD}${CYAN}Secrets in namespace: $ns${NC}"
    kubectl get secrets -n "$ns"
}

get_secret_value() {
    local secret=$1
    local ns=$2
    echo -e "\n${BOLD}${CYAN}Secret Value: $secret${NC}"
    kubectl get secret "$secret" -n "$ns" -o jsonpath='{.data}' | base64 -d
}

search_secret_usage() {
    local search=$1
    local ns=$2
    
    echo -e "\n${BOLD}${CYAN}========================================${NC}"
    echo -e "${BOLD}Searching for: '$search' in namespace: $ns${NC}"
    echo -e "${BOLD}${CYAN}========================================${NC}"
    
    echo -e "\n${YELLOW}[1/4] Kubernetes Secrets${NC}"
    kubectl get secrets -n "$ns" -o json 2>/dev/null | jq -r --arg s "$search" '.items[] | select(.data | tojson | @base64d | contains($s)) | .metadata.name' || echo "jq not available"
    
    echo -e "\n${YELLOW}[2/4] ConfigMaps${NC}"
    kubectl get configmap -n "$ns" -o json 2>/dev/null | jq -r --arg s "$search" '.items[] | select(.data | tojson | contains($s)) | .metadata.name' || echo "jq not available"
    
    echo -e "\n${YELLOW}[3/4] Deployments/Pods${NC}"
    kubectl get deployment,statefulset,daemonset,pod -n "$ns" -o json 2>/dev/null | jq -r --arg s "$search" '.items[] | select(.spec | tojson | contains($s)) | "\(.kind): \(.metadata.name)"' || echo "jq not available"
    
    echo -e "\n${YELLOW}[4/4] Events${NC}"
    kubectl get events -n "$ns" | grep -i "$search" || echo "No matches found"
}

keyvault_list() {
    local kv=$1
    echo -e "\n${BOLD}${CYAN}Azure KeyVault: $kv${NC}"
    
    echo -e "\n${YELLOW}Secrets:${NC}"
    az keyvault secret list --vault-name "$kv" --output table 2>/dev/null || echo "az CLI error or no access"
    
    echo -e "\n${YELLOW}Certificates:${NC}"
    az keyvault certificate list --vault-name "$kv" --output table 2>/dev/null || echo "az CLI error or no access"
    
    echo -e "\n${YELLOW}Keys:${NC}"
    az keyvault key list --vault-name "$kv" --output table 2>/dev/null || echo "az CLI error or no access"
}

thread_dump() {
    local pod=$1
    local ns=$2
    local container=$3
    
    echo -e "\n${BOLD}${CYAN}Generating Thread Dump: $pod${NC}"
    
    local pid_cmd="kubectl exec $pod -n $ns"
    [ -n "$container" ] && pid_cmd="$pid_cmd -c $container"
    pid_cmd="$pid_cmd -- jps -l 2>/dev/null | grep -v Jps | head -1 | awk '{print \$1}'"
    
    local java_pid=$(eval "$pid_cmd")
    
    if [ -z "$java_pid" ]; then
        echo -e "${RED}No Java process found!${NC}"
        return
    fi
    
    echo "Java PID: $java_pid"
    
    local dump_cmd="kubectl exec $pod -n $ns"
    [ -n "$container" ] && dump_cmd="$dump_cmd -c $container"
    dump_cmd="$dump_cmd -- jstack -l $java_pid"
    
    eval "$dump_cmd"
    echo -e "${GREEN}✓ Thread dump complete${NC}"
}

heap_dump() {
    local pod=$1
    local ns=$2
    local container=$3
    
    echo -e "\n${BOLD}${CYAN}Generating Heap Dump: $pod${NC}"
    
    local pid_cmd="kubectl exec $pod -n $ns"
    [ -n "$container" ] && pid_cmd="$pid_cmd -c $container"
    pid_cmd="$pid_cmd -- jps -l 2>/dev/null | grep -v Jps | head -1 | awk '{print \$1}'"
    
    local java_pid=$(eval "$pid_cmd")
    
    if [ -z "$java_pid" ]; then
        echo -e "${RED}No Java process found!${NC}"
        return
    fi
    
    echo "Java PID: $java_pid"
    
    local timestamp=$(date +%Y%m%d-%H%M%S)
    local filename="/tmp/heapdump-$timestamp.hprof"
    
    echo "Creating heap dump at $filename..."
    
    local dump_cmd="kubectl exec $pod -n $ns"
    [ -n "$container" ] && dump_cmd="$dump_cmd -c $container"
    dump_cmd="$dump_cmd -- jmap -dump:format=b,file=$filename $java_pid"
    
    eval "$dump_cmd"
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓ Heap dump created${NC}"
        echo "Copying to local machine..."
        kubectl cp "$ns/$pod:$filename" ./heapdump-$timestamp.hprof
        echo -e "${GREEN}✓ Saved as: heapdump-$timestamp.hprof${NC}"
    else
        echo -e "${RED}✗ Heap dump failed${NC}"
    fi
}

monitor_namespace() {
    local ns=$1
    
    echo -e "\n${BOLD}${CYAN}========================================${NC}"
    echo -e "${BOLD}Monitoring Namespace: $ns${NC}"
    echo -e "${BOLD}${CYAN}========================================${NC}"
    
    echo -e "\n${YELLOW}[1] Pods${NC}"
    kubectl get pods -n "$ns"
    
    echo -e "\n${YELLOW}[2] Deployments${NC}"
    kubectl get deployments -n "$ns"
    
    echo -e "\n${YELLOW}[3] Services${NC}"
    kubectl get svc -n "$ns"
    
    echo -e "\n${YELLOW}[4] ConfigMaps${NC}"
    kubectl get configmap -n "$ns"
    
    echo -e "\n${YELLOW}[5] Secrets${NC}"
    kubectl get secrets -n "$ns"
    
    echo -e "\n${YELLOW}[6] Events${NC}"
    kubectl get events -n "$ns" --sort-by='.lastTimestamp'
}

interactive_mode() {
    while true; do
        echo -e "\n${BOLD}${CYAN}========================================${NC}"
        echo -e "${BOLD}AKS Kubernetes Agent - Interactive Mode${NC}"
        echo -e "${BOLD}${CYAN}========================================${NC}"
        echo """
  1. List Pods in Namespace
  2. Get Pod Details
  3. Get Pod Logs
  4. Troubleshoot Pod
  5. List Secrets
  6. Get Secret Value
  7. Search Secret Usage
  8. Azure KeyVault (List)
  9. Monitor Namespace
 10. Thread Dump
 11. Heap Dump
  0. Exit
        """
        echo -ne "${CYAN}Select option (0-11): ${NC}"
        read choice
        
        case $choice in
            0) echo "Goodbye!"; exit 0 ;;
            1) 
                echo -ne "Namespace: "
                read ns
                [ -n "$ns" ] && get_pods "$ns"
                ;;
            2)
                echo -ne "Pod name: "
                read pod
                echo -ne "Namespace: "
                read ns
                [ -n "$pod" ] && [ -n "$ns" ] && get_pod_details "$pod" "$ns"
                ;;
            3)
                echo -ne "Pod name: "
                read pod
                echo -ne "Namespace: "
                read ns
                echo -ne "Previous logs? (y/n): "
                read prev
                echo -ne "Container (optional): "
                read container
                [ -n "$pod" ] && [ -n "$ns" ] && get_pod_logs "$pod" "$ns" "$prev" "$container"
                ;;
            4)
                echo -ne "Pod name: "
                read pod
                echo -ne "Namespace: "
                read ns
                [ -n "$pod" ] && [ -n "$ns" ] && troubleshoot_pod "$pod" "$ns"
                ;;
            5)
                echo -ne "Namespace: "
                read ns
                [ -n "$ns" ] && list_secrets "$ns"
                ;;
            6)
                echo -ne "Secret name: "
                read secret
                echo -ne "Namespace: "
                read ns
                [ -n "$secret" ] && [ -n "$ns" ] && get_secret_value "$secret" "$ns"
                ;;
            7)
                echo -ne "Search string: "
                read search
                echo -ne "Namespace: "
                read ns
                [ -n "$search" ] && [ -n "$ns" ] && search_secret_usage "$search" "$ns"
                ;;
            8)
                echo -ne "KeyVault name: "
                read kv
                [ -n "$kv" ] && keyvault_list "$kv"
                ;;
            9)
                echo -ne "Namespace: "
                read ns
                [ -n "$ns" ] && monitor_namespace "$ns"
                ;;
            10)
                echo -ne "Pod name: "
                read pod
                echo -ne "Namespace: "
                read ns
                echo -ne "Container (optional): "
                read container
                [ -n "$pod" ] && [ -n "$ns" ] && thread_dump "$pod" "$ns" "$container"
                ;;
            11)
                echo -ne "Pod name: "
                read pod
                echo -ne "Namespace: "
                read ns
                echo -ne "Container (optional): "
                read container
                [ -n "$pod" ] && [ -n "$ns" ] && heap_dump "$pod" "$ns" "$container"
                ;;
        esac
    done
}

show_help() {
    echo -e "${BOLD}AKS Kubernetes Agent${NC}"
    echo """
Usage:
  ./aks-agent.sh [options]

Options:
  -i, --interactive    Interactive menu mode
  -n, --namespace      Kubernetes namespace
  -p, --pod            Pod name
  -c, --container      Container name
  -kv, --keyvault      Azure KeyVault name
  -s, --search         Search string
  -a, --action         Action to perform

Actions:
  namespaces           List all namespaces
  pods                 Get all pods in namespace
  details              Get pod details
  logs                 Get pod logs
  troubleshoot         Troubleshoot pod issues
  secrets              List secrets
  secret-value         Get decoded secret value
  search-secret        Search for secret usage
  keyvault             List KeyVault contents
  monitor              Monitor namespace resources
  thread-dump           Generate Java thread dump
  heap-dump            Generate Java heap dump

Examples:
  ./aks-agent.sh -i
  ./aks-agent.sh -n production -a pods
  ./aks-agent.sh -n dev -p mypod -a troubleshoot
  ./aks-agent.sh -n prod -s "db-password" -a search-secret
  ./aks-agent.sh -n default -p app-123 -a heap-dump
"""
}

if [ $# -eq 0 ]; then
    check_prerequisites || exit 1
    interactive_mode
    exit 0
fi

check_prerequisites || exit 1

while [[ $# -gt 0 ]]; do
    case $1 in
        -i|--interactive) interactive_mode; exit 0 ;;
        -n|--namespace) namespace="$2"; shift 2 ;;
        -p|--pod) pod="$2"; shift 2 ;;
        -c|--container) container="$2"; shift 2 ;;
        -kv|--keyvault) keyvault="$2"; shift 2 ;;
        -s|--search) search="$2"; shift 2 ;;
        -a|--action) action="$2"; shift 2 ;;
        -h|--help) show_help; exit 0 ;;
        *) echo "Unknown option: $1"; exit 1 ;;
    esac
done

if [ "$action" == "namespaces" ]; then
    list_namespaces
elif [ "$action" == "pods" ] && [ -n "$namespace" ]; then
    get_pods "$namespace"
elif [ "$action" == "details" ] && [ -n "$pod" ] && [ -n "$namespace" ]; then
    get_pod_details "$pod" "$namespace"
elif [ "$action" == "logs" ] && [ -n "$pod" ] && [ -n "$namespace" ]; then
    get_pod_logs "$pod" "$namespace" "" "$container"
elif [ "$action" == "troubleshoot" ] && [ -n "$pod" ] && [ -n "$namespace" ]; then
    troubleshoot_pod "$pod" "$namespace"
elif [ "$action" == "secrets" ] && [ -n "$namespace" ]; then
    list_secrets "$namespace"
elif [ "$action" == "secret-value" ] && [ -n "$pod" ] && [ -n "$namespace" ]; then
    get_secret_value "$pod" "$namespace"
elif [ "$action" == "search-secret" ] && [ -n "$search" ] && [ -n "$namespace" ]; then
    search_secret_usage "$search" "$namespace"
elif [ "$action" == "keyvault" ] && [ -n "$keyvault" ]; then
    keyvault_list "$keyvault"
elif [ "$action" == "monitor" ] && [ -n "$namespace" ]; then
    monitor_namespace "$namespace"
elif [ "$action" == "thread-dump" ] && [ -n "$pod" ] && [ -n "$namespace" ]; then
    thread_dump "$pod" "$namespace" "$container"
elif [ "$action" == "heap-dump" ] && [ -n "$pod" ] && [ -n "$namespace" ]; then
    heap_dump "$pod" "$namespace" "$container"
else
    echo "Missing required arguments!"
    show_help
fi
