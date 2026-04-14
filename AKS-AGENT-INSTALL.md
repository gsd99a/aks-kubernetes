# AKS Kubernetes Agent - Application Package

## What's Included

| File | Description | Language | Use Case |
|------|-------------|----------|----------|
| `aks-agent.py` | Full-featured CLI application | Python 3 | All features + KeyVault |
| `aks-agent.sh` | Bash script (lighter weight) | Bash | Linux/Ubuntu only |
| `AKS-AGENT-README.md` | Command reference guide | - | Quick commands |
| `agents/aks-agent.md` | Complete agent with all commands | - | For OpenCode AI |

---

## Quick Install (Ubuntu/Linux)

### Option 1: Python Version (Recommended - Full Features)

```bash
# Download the file
wget https://your-server/aks-agent.py
# OR copy from this folder

# Make executable
chmod +x aks-agent.py

# Run
./aks-agent.py --interactive
```

### Option 2: Bash Version (Lighter)

```bash
# Download the file
wget https://your-server/aks-agent.sh
# OR copy from this folder

# Make executable
chmod +x aks-agent.sh

# Run
./aks-agent.sh --interactive
```

---

## Installation Steps

### Step 1: Prerequisites

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install kubectl
sudo apt install -y kubectl

# Install Azure CLI (for KeyVault)
curl -sL https://aka.ms/InstallAzureCLIDeb | sudo bash

# Install jq (for JSON parsing)
sudo apt install -y jq

# Login to Azure
az login

# Configure kubectl for your cluster
az aks get-credentials --resource-group <rg-name> --name <cluster-name>
```

### Step 2: Test Installation

```bash
# Check everything works
kubectl get nodes
az account show
```

### Step 3: Download Application

**From this folder:**
```
C:\Opencode-project-working\aks-agent.py
C:\Opencode-project-working\aks-agent.sh
```

**Copy to Ubuntu:**
```bash
# Using scp
scp user@your-pc:C:/Opencode-project-working/aks-agent.py .
scp user@your-pc:C:/Opencode-project-working/aks-agent.sh .

# Using rsync
rsync -avz user@your-pc:/mnt/c/Opencode-project-working/aks-agent.py .

# Or download from shared location
```

### Step 4: Run

```bash
# Interactive mode
./aks-agent.py --interactive

# Single command mode
./aks-agent.py -n production -a pods
```

---

## How to Use

### Interactive Mode (Menu)

```bash
./aks-agent.py --interactive
```

You'll see:
```
============================================================
AKS Kubernetes Agent - Interactive Mode
============================================================

  1. List Pods in Namespace
  2. Get Pod Details
  3. Get Pod Logs
  4. Troubleshoot Pod (Crashes/Restarts)
  5. List Secrets
  6. Get Secret Value
  7. Search Secret Usage
  8. Azure KeyVault (List Contents)
  9. Search KeyVault
 10. Monitor Namespace (All Resources)
 11. Thread Dump
 12. Heap Dump
  0. Exit

Select option (0-12):
```

### Command Line Mode

```bash
# Get all pods in production
./aks-agent.py -n production -a pods

# Troubleshoot a crashing pod
./aks-agent.py -n production -p xyz-123 -a troubleshoot

# Get logs from previous container
./aks-agent.py -n dev -p mypod -a logs

# List all secrets
./aks-agent.py -n production -a secrets

# Search where a secret is used
./aks-agent.py -n production -s "db-password" -a search-secret

# Generate thread dump
./aks-agent.py -n production -p web-app-123 -a thread-dump

# Generate heap dump
./aks-agent.py -n production -p web-app-123 -a heap-dump

# Check KeyVault
./aks-agent.py -kv mykeyvault -a keyvault

# Monitor entire namespace
./aks-agent.py -n production -a monitor
```

---

## Features Summary

| Feature | Command | Description |
|---------|---------|-------------|
| List Pods | `-n ns -a pods` | Show all pods with status |
| Pod Details | `-n ns -p pod -a details` | Full pod info |
| Pod Logs | `-n ns -p pod -a logs` | Current logs |
| Troubleshoot | `-n ns -p pod -a troubleshoot` | **Complete diagnosis** |
| Secrets | `-n ns -a secrets` | List all secrets |
| Search Secret | `-n ns -s string -a search-secret` | Find secret usage |
| KeyVault | `-kv vault -a keyvault` | List KeyVault items |
| Monitor | `-n ns -a monitor` | All resources |
| Thread Dump | `-n ns -p pod -a thread-dump` | Java thread dump |
| Heap Dump | `-n ns -p pod -a heap-dump` | Java heap dump |

---

## Download Files

### From This Computer

```
C:\Opencode-project-working\
├── aks-agent.py          ← Python application
├── aks-agent.sh          ← Bash script
└── AKS-AGENT-README.md   ← This file
```

### Copy to Ubuntu

**Windows to Linux:**
```powershell
# Using Windows Terminal/PowerShell
copy \\wsl$\Ubuntu\home\user\aks-agent.py C:\Users\You\Desktop\

# Or share via Python HTTP server
# On Windows:
cd C:\Opencode-project-working
python -m http.server 8000
# On Ubuntu:
wget http://windows-ip:8000/aks-agent.py
```

**Direct Path (WSL):**
```bash
# If using WSL
cp /mnt/c/Opencode-project-working/aks-agent.py ~/aks-agent.py
cp /mnt/c/Opencode-project-working/aks-agent.sh ~/aks-agent.sh
```

---

## Troubleshooting

### Error: kubectl not found
```bash
sudo apt install kubectl
```

### Error: az command not found
```bash
curl -sL https://aka.ms/InstallAzureCLIDeb | sudo bash
```

### Error: No Java process found
```bash
# Install JDK
sudo apt install openjdk-11-jdk
```

### Error: Permission denied
```bash
# Check kubectl context
kubectl config current-context

# Set correct context
kubectl config use-context <context-name>
```

---

## Auto-Complete Setup (Optional)

```bash
# Add to ~/.bashrc
echo 'source <(./aks-agent.py --completion)' >> ~/.bashrc
```

---

## Files Location Reference

| What | Where |
|------|-------|
| Python App | `C:\Opencode-project-working\aks-agent.py` |
| Bash Script | `C:\Opencode-project-working\aks-agent.sh` |
| Quick Guide | `C:\Opencode-project-working\AKS-AGENT-README.md` |
| Full Agent | `C:\Opencode-project-working\agents\aks-agent.md` |
| Skill JSON | `C:\Opencode-project-working\skills\aks-kubernetes-agent.json` |

---

## Support

For issues, check:
```bash
# Check cluster access
kubectl get nodes

# Check Azure login
az account show

# Check namespace exists
kubectl get namespaces
```
