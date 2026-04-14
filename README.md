# AKS Kubernetes Agent

Multi-context, cron-safe CLI tool for Azure AKS operations. Supports pods, debugging, secrets, thread/heap dumps, and GitHub Actions.

## Features

- **Multi-context support** - Switch contexts upfront, applies to all commands
- **Cron-safe** - Works in cron jobs with proper PATH setup
- **Azure KeyVault** - Integrated secrets/certs/keys search
- **Thread/Heap Dumps** - Java diagnostics
- **GitHub Actions** - Ready-to-use workflows

## Quick Start

```bash
# Download scripts
git clone https://github.com/YOUR_USER/aks-agent.git
cd aks-agent

# Make executable
chmod +x aks-agent-multi.sh

# List contexts
./aks-agent-multi.sh --list-contexts

# Get pods
./aks-agent-multi.sh -ctx prod-cluster -ns production -a pods
```

## Usage

```bash
./aks-agent-multi.sh -ctx <context> -ns <namespace> -a <action>
```

### Actions

| Action | Description |
|--------|-------------|
| `pods` | List all pods |
| `details -p <pod>` | Pod describe |
| `logs -p <pod>` | Pod logs |
| `troubleshoot -p <pod>` | Complete diagnosis |
| `secrets` | List secrets |
| `search-secret -s <string>` | Search secret usage |
| `monitor` | All resources |
| `thread-dump -p <pod>` | Java thread dump |
| `heap-dump -p <pod>` | Java heap dump |
| `all` | Full namespace overview |

### Examples

```bash
# Monitor production
./aks-agent-multi.sh -ctx prod-cluster -ns production -a pods

# Troubleshoot crashing pod
./aks-agent-multi.sh -ctx dev -ns dev -p xyz-123 -a troubleshoot

# Generate heap dump
./aks-agent-multi.sh -ctx prod -ns production -p web-app -a heap-dump

# Search secret usage
./aks-agent-multi.sh -ctx prod -ns production -s "db-password" -a search-secret
```

## Cron Jobs

```bash
# Setup environment
source aks-cron-env.sh

# Add to crontab
*/5 * * * * source ~/.aks-cron-env.sh && /path/to/aks-agent-multi.sh -ctx prod -ns production -a pods
```

## GitHub Actions

See `.github/workflows/` for ready-to-use workflows:

- `aks-monitor.yml` - Scheduled pod monitoring
- `aks-diagnostics.yml` - Thread/heap dumps
- `aks-cluster-health.yml` - Cluster health
- `aks-secret-scan.yml` - Secret scanning

### Setup Secrets

```
Settings > Secrets > Actions:

AZURE_CREDENTIALS = Azure service principal JSON
KUBE_CONFIG = base64 encoded kubeconfig
```

## Files

| File | Description |
|------|-------------|
| `aks-agent-multi.sh` | Main Bash script (cron-safe) |
| `aks-agent-multi.py` | Python alternative |
| `aks-cron-env.sh` | Cron environment setup |

## Prerequisites

- kubectl
- Azure CLI (`az`)
- jq

## License

MIT
