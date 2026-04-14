# GitHub Actions - AKS Kubernetes Agent

Automated Kubernetes operations using GitHub Actions.

## Workflows

| Workflow | Trigger | Purpose |
|----------|---------|---------|
| `aks-monitor.yml` | Schedule/Manual | Monitor pods, secrets, namespace |
| `aks-diagnostics.yml` | Manual | Thread dumps, heap dumps, troubleshoot |
| `aks-secret-scan.yml` | Schedule/Manual | Search secret usage |
| `aks-cluster-health.yml` | Schedule/Manual | Cluster/node health |
| `aks-deploy.yml` | Manual | Multi-context operations |

## Setup

### 1. Create Secrets

Go to `Settings > Secrets and variables > Actions`

| Secret | Description | Example |
|--------|-------------|---------|
| `AZURE_CREDENTIALS` | Azure service principal | See below |
| `KUBE_CONFIG` | kubeconfig (base64) | `cat ~/.kube/config \| base64` |
| `RESOURCE_GROUP` | Azure resource group | `my-rg` |
| `SLACK_WEBHOOK` | Slack webhook (optional) | `https://hooks.slack.com/...` |

### 2. Azure Credentials

```bash
# Create service principal
az ad sp create-for-rbac --name "aks-github-actions" \
  --role Contributor \
  --scopes /subscriptions/<sub-id>

# Output:
# {
#   "appId": "...",
#   "password": "...",
#   "tenant": "..."
# }

# Use this JSON as AZURE_CREDENTIALS secret
```

### 3. Kubeconfig Base64

```bash
# Encode kubeconfig
cat ~/.kube/config | base64 -w0

# Add as KUBE_CONFIG secret
```

## Usage

### Manual Trigger

```yaml
# .github/workflows/aks-monitor.yml
on:
  workflow_dispatch:
    inputs:
      context:
        default: 'prod-cluster'
      namespace:
        default: 'production'
      action:
        type: choice
        options:
          - pods
          - troubleshoot
          - secrets
```

Go to **Actions > AKS Monitor > Run workflow**

### Schedule

```yaml
on:
  schedule:
    - cron: '*/5 * * * *'  # Every 5 minutes
```

## Example: Cron with Multiple Clusters

```yaml
name: Monitor All Clusters

on:
  schedule:
    - cron: '*/5 * * * *'

jobs:
  prod:
    uses: ./.github/workflows/aks-monitor.yml
    with:
      context: prod-cluster
      namespace: production
    secrets:
      AZURE_CREDENTIALS: ${{ secrets.AZURE_CREDENTIALS }}
      KUBE_CONFIG: ${{ secrets.KUBE_CONFIG }}

  staging:
    uses: ./.github/workflows/aks-monitor.yml
    with:
      context: staging-cluster
      namespace: staging
    secrets:
      AZURE_CREDENTIALS: ${{ secrets.AZURE_CREDENTIALS }}
      KUBE_CONFIG: ${{ secrets.KUBE_CONFIG }}
```

## Example: Scheduled Diagnostics

```yaml
# .github/workflows/aks-scheduled-diagnostics.yml
name: Daily Heap Dump

on:
  schedule:
    - cron: '0 2 * * *'  # 2 AM daily

jobs:
  heap-dump:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Setup
        run: |
          curl -sL https://aka.ms/InstallAzureCLIDeb | sudo bash
          sudo apt-get install -y kubectl jq openjdk-17-jdk-headless
      
      - name: Azure Login
        uses: azure/login@v2
        with:
          creds: ${{ secrets.AZURE_CREDENTIALS }}
      
      - name: Setup kubeconfig
        run: echo "${{ secrets.KUBE_CONFIG }}" | base64 -d > kubeconfig
      
      - name: Generate Heap Dump
        run: |
          chmod +x aks-agent-multi.sh
          ./aks-agent-multi.sh -ctx prod -ns production -p critical-app -a heap-dump
      
      - name: Upload Dump
        uses: actions/upload-artifact@v4
        with:
          name: heapdump-$(date +%Y%m%d)
          path: heapdump-*.hprof
          retention-days: 30
```

## Common Issues

### kubectl not found
```yaml
- name: Setup kubectl
  run: |
    sudo apt-get update
    sudo apt-get install -y kubectl
```

### Authentication failed
```bash
# Refresh credentials
az login
az account set --subscription <sub-id>
```

### Permission denied
```bash
# Check RBAC
az role assignment list --assignee <app-id>
```

## Files

```
.github/workflows/
├── aks-monitor.yml        # Pod monitoring
├── aks-diagnostics.yml    # Dumps & troubleshooting
├── aks-secret-scan.yml   # Secret scanning
├── aks-cluster-health.yml # Cluster health
├── aks-deploy.yml        # Multi-context deploy
└── aks-pod-health.yml    # Pod health check
```
