# AKS Kubernetes Agent - Multi-Context Version

## What's New

**Auto-switches context and namespace upfront** - no need to specify `-n` each time!

---

## Quick Start

### 1. List All Available Contexts
```bash
./aks-agent-multi.sh --list-contexts
```

Output shows all contexts from your `~/.kube/config_*.yaml` files.

### 2. Run Commands with Context + Namespace
```bash
./aks-agent-multi.sh -ctx <context> -ns <namespace> -a <action>
```

**That's it!** The script:
1. Switches to the correct context
2. Uses the specified namespace for ALL commands
3. No need to type `-n namespace` repeatedly

---

## File Structure

```
C:\Opencode-project-working\
├── aks-agent-multi.py     ← Python (recommended)
├── aks-agent-multi.sh     ← Bash version
├── aks-agent.py           ← Original single-context
└── aks-agent.sh           ← Original single-context
```

---

## Usage Examples

### Example 1: Get all pods
```bash
./aks-agent-multi.sh -ctx prod-cluster -ns production -a pods
```

### Example 2: Troubleshoot crashing pod
```bash
./aks-agent-multi.sh -ctx dev-cluster -ns dev -p xyz-123 -a troubleshoot
```

### Example 3: Generate thread dump
```bash
./aks-agent-multi.sh -ctx staging -ns staging -p web-app-1 -a thread-dump
```

### Example 4: Search secret usage
```bash
./aks-agent-multi.sh -ctx prod -ns production -s "db-password" -a search-secret
```

### Example 5: Full namespace overview
```bash
./aks-agent-multi.sh -ctx prod-cluster -ns production -a all
```

---

## Command Reference

| Action | Command | Description |
|--------|---------|-------------|
| List contexts | `--list-contexts` | Show all available contexts |
| Get pods | `-a pods` | List all pods |
| Pod details | `-a details -p <pod>` | Full pod info |
| Pod logs | `-a logs -p <pod>` | Current logs |
| Troubleshoot | `-a troubleshoot -p <pod>` | Complete diagnosis |
| Secrets | `-a secrets` | List secrets |
| Search secret | `-a search-secret -s <string>` | Find secret usage |
| Monitor | `-a monitor` | All resources + events |
| Thread dump | `-a thread-dump -p <pod>` | Java thread dump |
| Heap dump | `-a heap-dump -p <pod>` | Java heap dump |
| All | `-a all` | Pods + Secrets + Monitor |

---

## For Your 15 Config Files

Your setup likely looks like:
```
~/.kube/
├── config_cluster1.yaml
├── config_cluster2.yaml
├── config_dev.yaml
├── config_prod.yaml
├── config_staging.yaml
└── ... (15 files)
```

### Step 1: Set environment variable
```bash
# Add to ~/.bashrc for permanent
export KUBECONFIG=~/.kube/config_*.yaml
```

### Step 2: List contexts
```bash
./aks-agent-multi.sh --list-contexts
```

### Step 3: Use specific context
```bash
# Use context from specific config file
KUBECONFIG=~/.kube/config_prod.yaml ./aks-agent-multi.sh -ctx prod-cluster -ns production -a pods
```

### Step 4: Or merge all configs
```bash
# Merge all config files
KUBECONFIG=~/.kube/config_*.yaml kubectl config get-contexts
```

---

## Download Files

```
C:\Opencode-project-working\
├── aks-agent-multi.py     ← Python multi-context app
├── aks-agent-multi.sh     ← Bash multi-context script
└── aks-agent-multi-README.md  ← This file
```

### Copy to Ubuntu:
```bash
# Method 1: SCP
scp user@windows:C:/Opencode-project-working/aks-agent-multi.py .
scp user@windows:C:/Opencode-project-working/aks-agent-multi.sh .

# Method 2: WSL
cp /mnt/c/Opencode-project-working/aks-agent-multi.py ~
cp /mnt/c/Opencode-project-working/aks-agent-multi.sh ~

# Method 3: USB
# Copy files to USB, then to Ubuntu
```

---

## Comparison: Single vs Multi Context

| Feature | Original | Multi-Context |
|---------|----------|---------------|
| Context switching | Manual | Automatic |
| Namespace each command | `-n ns` | `-ns ns` once |
| Multiple config files | Manual KUBECONFIG | Auto-detect |
| Best for | One cluster | Multiple clusters |

---

## Troubleshooting

### "No context found"
```bash
# Check your config files exist
ls ~/.kube/config_*.yaml

# List all contexts
./aks-agent-multi.sh --list-contexts
```

### "Failed to switch context"
```bash
# Verify context exists
kubectl config get-contexts -o name

# Check config file path
KUBECONFIG=~/.kube/your-config.yaml kubectl config get-contexts
```

### "Permission denied"
```bash
# Check kubectl access
kubectl auth can-i get pods --namespace=default

# Verify credentials
az aks get-credentials --resource-group <rg> --name <cluster> --overwrite-existing
```

---

## Complete Workflow Example

```bash
# 1. See all your contexts
./aks-agent-multi.sh --list-contexts

# 2. Work on production cluster
./aks-agent-multi.sh -ctx prod-aks -ns production -a pods
./aks-agent-multi.sh -ctx prod-aks -ns production -a secrets
./aks-agent-multi.sh -ctx prod-aks -ns production -p web-xyz -a troubleshoot

# 3. Switch to dev cluster
./aks-agent-multi.sh -ctx dev-aks -ns dev -a pods

# 4. Switch to staging
./aks-agent-multi.sh -ctx staging-aks -ns staging -a all
```

---

## Environment Variables

| Variable | Purpose | Example |
|----------|---------|---------|
| `KUBECONFIG` | Path to kubeconfig | `~/.kube/config_prod.yaml` |

---

## Files Reference

| File | Description |
|------|-------------|
| `aks-agent-multi.py` | Python app (recommended) |
| `aks-agent-multi.sh` | Bash script (lighter) |
| `AKS-AGENT-INSTALL.md` | Full installation guide |
| `AKS-AGENT-README.md` | Command reference |
