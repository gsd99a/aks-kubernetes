# AKS Agent - Cron Job Setup Guide

## The Problem

Cron jobs run with minimal environment - PATH doesn't include kubectl, az, etc.

```
PATH=/usr/bin:/bin
# kubectl NOT found!
```

## The Solution

### Option 1: Use Environment Setup Script (RECOMMENDED)

```bash
# Create cron entry like this:
* * * * * source /path/to/aks-cron-env.sh && /path/to/aks-agent-multi.sh -ctx prod -ns production -a pods >> /var/log/aks-pods.log 2>&1
```

### Option 2: Inline PATH Setup

```bash
# Add PATH inline in crontab
* * * * * export PATH="/usr/local/bin:/usr/bin:/bin:$HOME/.local/bin:$HOME/.azure/bin" && /path/to/aks-agent-multi.sh -ctx prod -ns production -a pods
```

### Option 3: Use Python Version (Auto-handles PATH)

```bash
# Python script auto-detects kubectl location
* * * * * /usr/bin/python3 /path/to/aks-agent-multi.py -ctx prod -ns production -a pods
```

---

## Complete Cron Setup

### 1. Setup Environment File

```bash
# Copy env file to home directory
cp aks-cron-env.sh ~/.aks-cron-env.sh
chmod +x ~/.aks-cron-env.sh
```

### 2. Test Environment Setup

```bash
# Source the environment
source ~/.aks-cron-env.sh

# Check if kubectl is found
check_kubectl
# Output: ✓ kubectl found: /usr/local/bin/kubectl
```

### 3. Create Cron Jobs

```bash
# Edit crontab
crontab -e

# Add entries:
```

### Example Cron Entries

```bash
# ===========================================
# AKS Agent Cron Jobs
# ===========================================

# Every 5 minutes: Check pods in production
*/5 * * * * source ~/.aks-cron-env.sh && /home/user/scripts/aks-agent-multi.sh -ctx prod-cluster -ns production -a pods >> /var/log/aks/production-pods.log 2>&1

# Every 10 minutes: Check pods in staging
*/10 * * * * source ~/.aks-cron-env.sh && /home/user/scripts/aks-agent-multi.sh -ctx staging-cluster -ns staging -a pods >> /var/log/aks/staging-pods.log 2>&1

# Hourly: Full namespace overview
0 * * * * source ~/.aks-cron-env.sh && /home/user/scripts/aks-agent-multi.sh -ctx prod-cluster -ns production -a all >> /var/log/aks/production-full.log 2>&1

# Daily: Thread dump for monitoring
0 2 * * * source ~/.aks-cron-env.sh && /home/user/scripts/aks-agent-multi.sh -ctx prod-cluster -ns production -p critical-app-1 -a thread-dump >> /var/log/aks/threaddump.log 2>&1

# On failure: Search for issues
*/15 * * * * source ~/.aks-cron-env.sh && /home/user/scripts/aks-agent-multi.sh -ctx prod-cluster -ns production -s "OOMKilled" -a search-secret >> /var/log/aks/errors.log 2>&1
```

---

## Cron-Safe Scripts

### Bash Script (`aks-agent-multi.sh`)
```bash
# Already includes PATH setup at the top!
#!/bin/bash
setup_cron_environment() {
    export PATH="/usr/local/bin:/usr/bin:/bin:$HOME/.local/bin:$HOME/.azure/bin:..."
    # ... finds kubectl, az, etc.
}
```

### Python Script (`aks-agent-multi.py`)
```python
# Already auto-detects kubectl location!
def setup_cron_environment():
    # Uses shutil.which() and searches common paths
    kubectl_path = shutil.which('kubectl')
    # ...
```

---

## Troubleshooting Cron Issues

### 1. Check Cron Log
```bash
# Ubuntu/Debian
grep CRON /var/log/syslog

# CentOS/RHEL
grep CRON /var/log/cron
```

### 2. Test Script Manually
```bash
# Run exactly as cron would
/bin/bash -c 'source ~/.aks-cron-env.sh && ./aks-agent-multi.sh -ctx prod -ns production -a pods'
```

### 3. Debug PATH Issues
```bash
# Add to your script
echo "PATH=$PATH" >> /tmp/debug.log
which kubectl >> /tmp/debug.log
```

### 4. Check Environment
```bash
# Source and check status
source ~/.aks-cron-env.sh
print_status
```

---

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `PATH` | Binary locations | Auto-set by env script |
| `KUBECONFIG` | kubeconfig file | `~/.kube/config` |
| `AZURE_CONFIG_DIR` | Azure config | `~/.azure` |

---

## Cron Job Examples

### Monitor Multiple Clusters

```bash
# crontab -e

# Production cluster - every 5 min
*/5 * * * * source ~/.aks-cron-env.sh && /scripts/aks-agent.sh -ctx prod-aks -ns production -a pods

# Development cluster - every 10 min
*/10 * * * * source ~/.aks-cron-env.sh && /scripts/aks-agent.sh -ctx dev-aks -ns dev -a pods

# Staging cluster - every 15 min
*/15 * * * * source ~/.aks-cron-env.sh && /scripts/aks-agent.sh -ctx staging-aks -ns staging -a pods
```

### Scheduled Diagnostics

```bash
# crontab -e

# Daily heap dump at 2 AM
0 2 * * * source ~/.aks-cron-env.sh && /scripts/aks-agent.sh -ctx prod -ns production -p myapp-0 -a heap-dump

# Weekly thread dump analysis on Monday
0 9 * * 1 source ~/.aks-cron-env.sh && /scripts/aks-agent.sh -ctx prod -ns production -p myapp-0 -a thread-dump

# Monthly secret audit
0 0 1 * * source ~/.aks-cron-env.sh && /scripts/aks-agent.sh -ctx prod -ns production -a secrets
```

### Alert on Issues

```bash
# crontab -e

# Check for CrashLoopBackOff every 5 min
*/5 * * * * source ~/.aks-cron-env.sh && /scripts/check-crashing-pods.sh -ctx prod -ns production

# Check for OOMKilled pods every 5 min
*/5 * * * * source ~/.aks-cron-env.sh && /scripts/check-oom.sh -ctx prod -ns production
```

---

## Files Reference

| File | Purpose |
|------|---------|
| `aks-agent-multi.sh` | Main script (cron-safe) |
| `aks-agent-multi.py` | Python alternative (auto PATH) |
| `aks-cron-env.sh` | Environment setup for cron |

---

## Quick Test

```bash
# Test cron environment
source ~/.aks-cron-env.sh

# Should show:
# ✓ kubectl found
# ✓ az CLI found
# ✓ kubectl access OK

# Then test your command
./aks-agent-multi.sh -ctx prod -ns production -a pods
```
