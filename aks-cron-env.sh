#!/bin/bash
# AKS Agent - Cron Environment Setup
# SOURCE THIS FILE before running kubectl/az commands in cron
# Usage: source /path/to/aks-cron-env.sh

# ============================================
# CRON-SAFE PATH SETUP
# ============================================

# Store original PATH
ORIGINAL_PATH="$PATH"

# Common binary locations
export PATH="/usr/local/bin:/usr/bin:/bin:/sbin:/usr/local/sbin:/usr/sbin:$HOME/go/bin:$HOME/.local/bin:$HOME/bin:$PATH"

# Azure CLI locations
export PATH="$PATH:/usr/local/az-cli/bin:/opt/az/bin:$HOME/.azure/bin:/home/$(whoami)/.azure/bin"

# Kubernetes paths
export PATH="$PATH:$HOME/.krew/bin"

# Snap binaries (Ubuntu)
export PATH="$PATH:/snap/bin"

# Find kubectl
if ! command -v kubectl &> /dev/null; then
    KUBECTL_PATHS=(
        "$HOME/.kube/kubectl"
        "$HOME/bin/kubectl"
        "/usr/local/bin/kubectl"
        "/snap/bin/kubectl"
        "/opt/kubernetes/kubectl"
    )
    for k in "${KUBECTL_PATHS[@]}"; do
        if [ -f "$k" ]; then
            export PATH="$(dirname $k):$PATH"
            break
        fi
    done
fi

# Find Azure CLI (az)
if ! command -v az &> /dev/null; then
    AZ_PATHS=(
        "$HOME/.azure/bin/az"
        "/usr/local/az-cli/bin/az"
        "/opt/az/bin/az"
        "/snap/bin/az"
    )
    for a in "${AZ_PATHS[@]}"; do
        if [ -f "$a" ]; then
            export PATH="$(dirname $a):$PATH"
            break
        fi
    done
done

# ============================================
# KUBECONFIG SETUP
# ============================================

# Default kubeconfig location
export KUBECONFIG="${KUBECONFIG:-$HOME/.kube/config}"

# If KUBECONFIG is not set or file doesn't exist, try config_*.yaml
if [ ! -f "$KUBECONFIG" ]; then
    KUBE_DIR="$HOME/.kube"
    if [ -d "$KUBE_DIR" ]; then
        # Get first config_*.yaml file
        CONFIG_FILE=$(ls "$KUBE_DIR"/config_*.yaml 2>/dev/null | head -1)
        if [ -n "$CONFIG_FILE" ]; then
            export KUBECONFIG="$CONFIG_FILE"
        fi
    fi
fi

# ============================================
# AZURE CLI SETUP
# ============================================

export AZURE_CONFIG_DIR="${AZURE_CONFIG_DIR:-$HOME/.azure}"

# Ensure Azure CLI is using the correct config
export AZURE_CORE-show-AZURE_CLI_HTTP_LOGGING_CONFIG=0

# ============================================
# PROXY SETTINGS (if needed)
# ============================================

# Uncomment if behind proxy
# export HTTP_PROXY="http://proxy.example.com:8080"
# export HTTPS_PROXY="http://proxy.example.com:8080"
# export NO_PROXY="localhost,127.0.0.1,.cluster.local"

# ============================================
# KUBECTL DEFAULTS
# ============================================

# Prevent pagination issues in cron
export KUBECTL_CLI_NO_VERSION_CHECK=true

# ============================================
# HELPER FUNCTIONS
# ============================================

# Check if kubectl is available
check_kubectl() {
    if command -v kubectl &> /dev/null; then
        echo "✓ kubectl found: $(which kubectl)"
        kubectl version --client 2>/dev/null | head -1
        return 0
    else
        echo "✗ kubectl NOT found in PATH"
        echo "  Searched paths: $PATH"
        return 1
    fi
}

# Check if az CLI is available
check_az() {
    if command -v az &> /dev/null; then
        echo "✓ az CLI found: $(which az)"
        az version 2>/dev/null | head -1
        return 0
    else
        echo "⚠ az CLI NOT found (needed for KeyVault)"
        return 1
    fi
}

# Check kubectl access
check_cluster_access() {
    if kubectl auth can-i get pods &>/dev/null; then
        echo "✓ kubectl access OK"
        echo "  Context: $(kubectl config current-context 2>/dev/null)"
        return 0
    else
        echo "✗ No kubectl access or cluster unreachable"
        return 1
    fi
}

# Setup specific context
use_context() {
    local ctx="$1"
    local ns="${2:-default}"
    
    if [ -n "$ctx" ]; then
        kubectl config use-context "$ctx" 2>/dev/null
        if [ $? -eq 0 ]; then
            echo "✓ Switched to context: $ctx"
            echo "  Using namespace: $ns"
        fi
    fi
}

# Print status
print_status() {
    echo "========================================"
    echo "AKS Agent Environment Status"
    echo "========================================"
    echo "PATH: $PATH"
    echo "KUBECONFIG: $KUBECONFIG"
    echo "AZURE_CONFIG_DIR: $AZURE_CONFIG_DIR"
    echo ""
    check_kubectl
    check_az
    check_cluster_access
    echo "========================================"
}

# If run directly (not sourced), print status
if [ "$AKS_ENV_LOADED" != "true" ]; then
    if [ "$0" = "${BASH_SOURCE[0]}" ]; then
        export AKS_ENV_LOADED="true"
        print_status
    fi
fi
