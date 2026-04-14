#!/usr/bin/env python3
"""
AKS Kubernetes Agent - Multi-Context Support
Takes context and namespace upfront, auto-configures before running commands
Supports multiple config_*.yaml files
CRON-SAFE: Includes proper PATH setup for cron jobs
"""

import argparse
import json
import subprocess
import sys
import os
import glob
import shutil
from pathlib import Path

def setup_cron_environment():
    """Setup environment for cron jobs - find kubectl and az in common locations"""
    
    # Add common binary paths
    common_paths = [
        '/usr/local/bin',
        '/usr/bin',
        '/bin',
        '/snap/bin',
        os.path.expanduser('~/.local/bin'),
        os.path.expanduser('~/bin'),
        os.path.expanduser('~/.kube'),
        os.path.expanduser('~/.azure/bin'),
        '/opt/az-cli/bin',
        '/usr/local/az-cli/bin',
        '/opt/homebrew/bin',
    ]
    
    # Add krew plugin path
    common_paths.append(os.path.expanduser('~/.krew/bin'))
    
    # Find kubectl
    kubectl_path = shutil.which('kubectl')
    if not kubectl_path:
        for path in common_paths:
            test_path = os.path.join(path, 'kubectl')
            if os.path.exists(test_path):
                kubectl_path = test_path
                os.environ['PATH'] = path + ':' + os.environ.get('PATH', '')
                break
    
    # Find az CLI
    az_path = shutil.which('az')
    if not az_path:
        for path in common_paths:
            test_path = os.path.join(path, 'az')
            if os.path.exists(test_path):
                az_path = test_path
                os.environ['PATH'] = path + ':' + os.environ.get('PATH', '')
                break
    
    # Kubernetes config
    kubeconfig = os.environ.get('KUBECONFIG', os.path.expanduser('~/.kube/config'))
    if not os.path.exists(kubeconfig):
        # Check for config_*.yaml files
        kube_dir = os.path.expanduser('~/.kube')
        if os.path.exists(kube_dir):
            config_files = glob.glob(os.path.join(kube_dir, 'config_*.yaml'))
            if config_files:
                os.environ['KUBECONFIG'] = ':'.join(config_files)
    
    # Azure config dir
    os.environ.setdefault('AZURE_CONFIG_DIR', os.path.expanduser('~/.azure'))
    
    return kubectl_path, az_path

# Initialize cron-safe environment
KUBECTL_PATH, AZ_PATH = setup_cron_environment()

class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'

KUBECONFIG_DIR = os.path.expanduser("~/.kube")
CONFIG_PATTERNS = ["config_*.yaml", "config_*.yml", "kubeconfig_*.yaml", "*.kubeconfig"]

class KubeContext:
    def __init__(self, name, cluster, namespace, kubeconfig_path):
        self.name = name
        self.cluster = cluster
        self.namespace = namespace
        self.kubeconfig_path = kubeconfig_path
    
    def __str__(self):
        return f"{self.name} | cluster: {self.cluster} | namespace: {self.namespace}"

def find_config_files():
    """Find all config files in ~/.kube directory"""
    config_files = []
    if os.path.exists(KUBECONFIG_DIR):
        for pattern in CONFIG_PATTERNS:
            config_files.extend(glob.glob(os.path.join(KUBECONFIG_DIR, pattern)))
            config_files.extend(glob.glob(os.path.join(KUBECONFIG_DIR, "configs", pattern)))
    return list(set(config_files))

def get_current_context():
    """Get current kubectl context"""
    result = subprocess.run(
        "kubectl config current-context",
        shell=True, capture_output=True, text=True
    )
    return result.stdout.strip() if result.returncode == 0 else None

def list_contexts():
    """List all available contexts from config files"""
    print(f"\n{Colors.HEADER}{'='*70}{Colors.ENDC}")
    print(f"{Colors.BOLD}Available Kubernetes Contexts{Colors.ENDC}")
    print(f"{Colors.HEADER}{'='*70}{Colors.ENDC}")
    
    config_files = find_config_files()
    print(f"\n{Colors.CYAN}Config files found: {len(config_files)}{Colors.ENDC}")
    
    contexts = []
    for config_file in config_files:
        print(f"\n{Colors.YELLOW}From: {config_file}{Colors.ENDC}")
        result = subprocess.run(
            f"KUBECONFIG={config_file} kubectl config get-contexts -o name",
            shell=True, capture_output=True, text=True
        )
        if result.returncode == 0:
            for ctx_name in result.stdout.strip().split('\n'):
                if ctx_name:
                    contexts.append(ctx_name)
                    print(f"  - {ctx_name}")
    
    print(f"\n{Colors.GREEN}Total contexts found: {len(contexts)}{Colors.ENDC}")
    return contexts

def load_context_from_name(context_name):
    """Load a specific context and extract namespace"""
    result = subprocess.run(
        f"kubectl config view --context={context_name} -o json",
        shell=True, capture_output=True, text=True
    )
    
    if result.returncode == 0:
        try:
            config = json.loads(result.stdout)
            contexts = config.get('contexts', [])
            for ctx in contexts:
                if ctx.get('name') == context_name:
                    return {
                        'name': context_name,
                        'namespace': ctx.get('namespace', 'default'),
                        'cluster': ctx.get('cluster', 'unknown')
                    }
        except:
            pass
    
    return {'name': context_name, 'namespace': 'default', 'cluster': 'unknown'}

def switch_context(context_name, kubeconfig_path=None):
    """Switch to a specific context"""
    env = os.environ.copy()
    if kubeconfig_path and os.path.exists(kubeconfig_path):
        env['KUBECONFIG'] = kubeconfig_path
    
    cmd = f"kubectl config use-context {context_name}"
    if kubeconfig_path:
        cmd = f"KUBECONFIG={kubeconfig_path} kubectl config use-context {context_name}"
    
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True, env=env)
    if result.returncode == 0:
        print(f"{Colors.GREEN}✓ Switched to context: {context_name}{Colors.ENDC}")
        return True
    else:
        print(f"{Colors.RED}✗ Failed to switch context: {result.stderr}{Colors.ENDC}")
        return False

def check_prerequisites():
    """Check if kubectl is available"""
    result = subprocess.run("kubectl version --client", shell=True, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"{Colors.RED}✗ kubectl not found!{Colors.ENDC}")
        return False
    return True

class K8sAgent:
    def __init__(self, context=None, namespace=None, kubeconfig_path=None):
        self.context = context
        self.namespace = namespace
        self.kubeconfig_path = kubeconfig_path
        self.env = os.environ.copy()
        
        if kubeconfig_path and os.path.exists(kubeconfig_path):
            self.env['KUBECONFIG'] = kubeconfig_path
            print(f"{Colors.CYAN}Using kubeconfig: {kubeconfig_path}{Colors.ENDC}")
        
        if context:
            if not self.switch_context(context):
                raise Exception(f"Failed to switch to context: {context}")
            
            if not namespace:
                ctx_info = self.get_context_info(context)
                self.namespace = ctx_info.get('namespace', 'default')
                print(f"{Colors.CYAN}Using namespace: {self.namespace}{Colors.ENDC}")
    
    def run_cmd(self, cmd, capture=True, show_cmd=True):
        """Run command with KUBECONFIG set and PATH configured"""
        if show_cmd:
            print(f"\n{Colors.CYAN}>>> {cmd}{Colors.ENDC}")
        
        try:
            # Merge environment with PATH setup
            cmd_env = os.environ.copy()
            cmd_env.update(self.env)
            
            # Ensure kubectl/az are in PATH for this command
            cmd_env['PATH'] = f"/usr/local/bin:/usr/bin:/bin:{os.path.expanduser('~/.local/bin')}:{cmd_env.get('PATH', '')}"
            
            result = subprocess.run(
                cmd, shell=True, capture_output=capture, 
                text=True, timeout=120, env=cmd_env
            )
            return result.stdout, result.stderr, result.returncode
        except subprocess.TimeoutExpired:
            return "", "Command timed out", 1
        except Exception as e:
            return "", str(e), 1
    
    def switch_context(self, ctx):
        """Switch kubectl context"""
        if self.kubeconfig_path:
            cmd = f"KUBECONFIG={self.kubeconfig_path} kubectl config use-context {ctx}"
        else:
            cmd = f"kubectl config use-context {ctx}"
        
        stdout, stderr, rc = self.run_cmd(cmd, show_cmd=True)
        return rc == 0
    
    def get_context_info(self, context_name):
        """Get context details"""
        if self.kubeconfig_path:
            cmd = f"KUBECONFIG={self.kubeconfig_path} kubectl config view --context={context_name} -o json"
        else:
            cmd = f"kubectl config view --context={context_name} -o json"
        
        stdout, _, _ = self.run_cmd(cmd)
        try:
            config = json.loads(stdout)
            for ctx in config.get('contexts', []):
                if ctx.get('name') == context_name:
                    return {
                        'name': context_name,
                        'namespace': ctx.get('namespace', 'default'),
                        'cluster': ctx.get('cluster', 'unknown')
                    }
        except:
            pass
        return {'name': context_name, 'namespace': 'default', 'cluster': 'unknown'}
    
    def get_pods(self):
        """Get all pods"""
        print(f"\n{Colors.HEADER}{'='*70}{Colors.ENDC}")
        print(f"{Colors.BOLD}Pods in Namespace: {self.namespace}{Colors.ENDC}")
        stdout, _, rc = self.run_cmd(f"kubectl get pods -n {self.namespace} -o wide")
        if rc == 0:
            print(stdout)
        return stdout
    
    def get_all_resources(self):
        """Get all resources in namespace"""
        print(f"\n{Colors.HEADER}{'='*70}{Colors.ENDC}")
        print(f"{Colors.BOLD}All Resources in Namespace: {self.namespace}{Colors.ENDC}")
        stdout, _, rc = self.run_cmd(f"kubectl get all -n {self.namespace}")
        if rc == 0:
            print(stdout)
        return stdout
    
    def get_pod_details(self, pod_name):
        """Get pod details"""
        print(f"\n{Colors.HEADER}{'='*70}{Colors.ENDC}")
        print(f"{Colors.BOLD}Pod Details: {pod_name}{Colors.ENDC}")
        stdout, _, rc = self.run_cmd(f"kubectl describe pod {pod_name} -n {self.namespace}")
        if rc == 0:
            print(stdout)
        return stdout
    
    def get_pod_logs(self, pod_name, previous=False, container=""):
        """Get pod logs"""
        print(f"\n{Colors.HEADER}{'='*70}{Colors.ENDC}")
        print(f"{Colors.BOLD}Pod Logs: {pod_name}{Colors.ENDC}")
        
        cmd = f"kubectl logs {pod_name} -n {self.namespace}"
        if previous:
            cmd += " --previous"
        if container:
            cmd += f" -c {container}"
        
        stdout, stderr, rc = self.run_cmd(f"{cmd} | tail -100")
        if stdout:
            print(stdout)
        return stdout
    
    def troubleshoot_pod(self, pod_name):
        """Complete pod troubleshooting"""
        print(f"\n{Colors.HEADER}{'='*70}{Colors.ENDC}")
        print(f"{Colors.BOLD}Troubleshooting Pod: {pod_name}{Colors.ENDC}")
        print(f"{Colors.HEADER}{'='*70}{Colors.ENDC}")
        
        checks = [
            ("Status", f"kubectl get pod {pod_name} -n {self.namespace} -o jsonpath='{{.status.phase}}'"),
            ("Restart Count", f"kubectl get pod {pod_name} -n {self.namespace} -o jsonpath='{{.status.containerStatuses[*].restartCount}}'"),
            ("Exit Code", f"kubectl get pod {pod_name} -n {self.namespace} -o jsonpath='{{.status.containerStatuses[*].lastState.terminated.exitCode}}'"),
            ("Termination Message", f"kubectl get pod {pod_name} -n {self.namespace} -o jsonpath='{{.status.containerStatuses[*].lastState.terminated.message}}'"),
        ]
        
        for i, (name, cmd) in enumerate(checks, 1):
            stdout, _, _ = self.run_cmd(cmd)
            if stdout.strip():
                print(f"\n{Colors.YELLOW}[{i}] {name}:{Colors.ENDC} {stdout.strip()}")
        
        print(f"\n{Colors.YELLOW}[5] OOMKilled Check:{Colors.ENDC}")
        stdout, _, _ = self.run_cmd(f"kubectl get pod {pod_name} -n {self.namespace} -o jsonpath='{{.status.containerStatuses[*].lastState.terminated.reason}}'")
        if 'OOMKilled' in stdout:
            print(f"{Colors.RED}⚠ Pod was OOMKilled!{Colors.ENDC}")
        else:
            print("Not OOMKilled")
        
        print(f"\n{Colors.YELLOW}[6] Previous Logs:{Colors.ENDC}")
        self.run_cmd(f"kubectl logs {pod_name} -n {self.namespace} --previous 2>&1 | tail -50")
        
        print(f"\n{Colors.YELLOW}[7] Pod Events:{Colors.ENDC}")
        self.run_cmd(f"kubectl get events -n {self.namespace} --field-selector involvedObject.name={pod_name} --sort-by='.lastTimestamp'")
    
    def get_secrets(self):
        """List secrets"""
        print(f"\n{Colors.HEADER}{'='*70}{Colors.ENDC}")
        print(f"{Colors.BOLD}Secrets in Namespace: {self.namespace}{Colors.ENDC}")
        stdout, _, rc = self.run_cmd(f"kubectl get secrets -n {self.namespace}")
        if rc == 0:
            print(stdout)
        return stdout
    
    def search_secret_usage(self, search_string):
        """Search for secret string"""
        print(f"\n{Colors.HEADER}{'='*70}{Colors.ENDC}")
        print(f"{Colors.BOLD}Searching for: '{search_string}' in namespace: {self.namespace}{Colors.ENDC}")
        print(f"{Colors.HEADER}{'='*70}{Colors.ENDC}")
        
        searches = [
            ("Kubernetes Secrets", f"kubectl get secrets -n {self.namespace} -o json | jq -r --arg s '{search_string}' '.items[] | select(.data | tojson | @base64d | contains($s)) | .metadata.name' 2>/dev/null"),
            ("ConfigMaps", f"kubectl get configmap -n {self.namespace} -o json | jq -r --arg s '{search_string}' '.items[] | select(.data | tojson | contains($s)) | .metadata.name' 2>/dev/null"),
            ("Deployments/Pods", f"kubectl get deployment,statefulset,pod -n {self.namespace} -o json | jq -r --arg s '{search_string}' '.items[] | select(.spec | tojson | contains($s)) | \"\\(.kind): \\(.metadata.name)\"' 2>/dev/null"),
        ]
        
        for name, cmd in searches:
            print(f"\n{Colors.YELLOW}{name}:{Colors.ENDC}")
            self.run_cmd(cmd)
    
    def monitor_namespace(self):
        """Monitor all resources"""
        print(f"\n{Colors.HEADER}{'='*70}{Colors.ENDC}")
        print(f"{Colors.BOLD}Monitoring Namespace: {self.namespace}{Colors.ENDC}")
        print(f"{Colors.HEADER}{'='*70}{Colors.ENDC}")
        
        resources = ['pods', 'deployments', 'services', 'configmaps', 'secrets', 'ingresses', 'cronjobs', 'jobs']
        for res in resources:
            print(f"\n{Colors.YELLOW}{res.upper()}:{Colors.ENDC}")
            self.run_cmd(f"kubectl get {res} -n {self.namespace}")
        
        print(f"\n{Colors.YELLOW}EVENTS:{Colors.ENDC}")
        self.run_cmd(f"kubectl get events -n {self.namespace} --sort-by='.lastTimestamp'")
    
    def thread_dump(self, pod_name, container=""):
        """Generate thread dump"""
        print(f"\n{Colors.HEADER}{'='*70}{Colors.ENDC}")
        print(f"{Colors.BOLD}Thread Dump: {pod_name}{Colors.ENDC}")
        
        pid_cmd = f"kubectl exec {pod_name} -n {self.namespace}"
        if container:
            pid_cmd += f" -c {container}"
        pid_cmd += " -- jps -l 2>/dev/null | grep -v Jps | head -1 | awk '{print $1}'"
        
        stdout, _, _ = self.run_cmd(pid_cmd)
        java_pid = stdout.strip()
        
        if not java_pid:
            print(f"{Colors.RED}No Java process found!{Colors.ENDC}")
            return
        
        print(f"Java PID: {java_pid}")
        
        dump_cmd = f"kubectl exec {pod_name} -n {self.namespace}"
        if container:
            dump_cmd += f" -c {container}"
        dump_cmd += f" -- jstack -l {java_pid}"
        
        stdout, _, rc = self.run_cmd(dump_cmd)
        if rc == 0:
            print(stdout)
            print(f"\n{Colors.GREEN}✓ Thread dump complete{Colors.ENDC}")
    
    def heap_dump(self, pod_name, container=""):
        """Generate heap dump"""
        print(f"\n{Colors.HEADER}{'='*70}{Colors.ENDC}")
        print(f"{Colors.BOLD}Heap Dump: {pod_name}{Colors.ENDC}")
        
        pid_cmd = f"kubectl exec {pod_name} -n {self.namespace}"
        if container:
            pid_cmd += f" -c {container}"
        pid_cmd += " -- jps -l 2>/dev/null | grep -v Jps | head -1 | awk '{print $1}'"
        
        stdout, _, _ = self.run_cmd(pid_cmd)
        java_pid = stdout.strip()
        
        if not java_pid:
            print(f"{Colors.RED}No Java process found!{Colors.ENDC}")
            return
        
        print(f"Java PID: {java_pid}")
        
        from datetime import datetime
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        filename = f"/tmp/heapdump-{timestamp}.hprof"
        
        dump_cmd = f"kubectl exec {pod_name} -n {self.namespace}"
        if container:
            dump_cmd += f" -c {container}"
        dump_cmd += f" -- jmap -dump:format=b,file={filename} {java_pid}"
        
        stdout, _, rc = self.run_cmd(dump_cmd)
        if rc == 0:
            print(f"{Colors.GREEN}✓ Heap dump created: {filename}{Colors.ENDC}")
            self.run_cmd(f"kubectl cp {self.namespace}/{pod_name}:{filename} ./heapdump-{timestamp}.hprof")
            print(f"{Colors.GREEN}✓ Saved: heapdump-{timestamp}.hprof{Colors.ENDC}")

def show_help():
    print(f"""
{Colors.BOLD}AKS Kubernetes Agent - Multi-Context{Colors.ENDC}

Usage:
  {Colors.CYAN}python aks-agent-multi.py --context <context> --namespace <namespace> [options]{Colors.ENDC}

Required:
  -ctx, --context        Kubernetes context name
  -ns, --namespace       Kubernetes namespace

Optional:
  -kube, --kubeconfig    Path to kubeconfig file (default: auto-detect from ~/.kube)
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
  {Colors.GREEN}# List all available contexts{Colors.ENDC}
  python aks-agent-multi.py --list-contexts

  {Colors.GREEN}# Get all pods in production context{Colors.ENDC}
  python aks-agent-multi.py -ctx prod-cluster -ns production -a pods

  {Colors.GREEN}# Troubleshoot a crashing pod{Colors.ENDC}
  python aks-agent-multi.py -ctx dev-cluster -ns dev -p xyz-123 -a troubleshoot

  {Colors.GREEN}# Generate thread dump{Colors.ENDC}
  python aks-agent-multi.py -ctx prod-cluster -ns production -p web-app-1 -a thread-dump

  {Colors.GREEN}# Search for secret usage{Colors.ENDC}
  python aks-agent-multi.py -ctx staging -ns staging -s "db-password" -a search-secret
""")

def main():
    if len(sys.argv) == 1 or '--help' in sys.argv or '-h' in sys.argv:
        show_help()
        sys.exit(0)
    
    if '--list-contexts' in sys.argv or '-lc' in sys.argv:
        check_prerequisites()
        list_contexts()
        sys.exit(0)
    
    if not check_prerequisites():
        sys.exit(1)
    
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument('-ctx', '--context', required=True)
    parser.add_argument('-ns', '--namespace', default=None)
    parser.add_argument('-kube', '--kubeconfig', default=None)
    parser.add_argument('-p', '--pod', default=None)
    parser.add_argument('-c', '--container', default=None)
    parser.add_argument('-s', '--search', default=None)
    parser.add_argument('-kv', '--keyvault', default=None)
    parser.add_argument('-a', '--action', default='pods')
    
    args, _ = parser.parse_known_args()
    
    try:
        agent = K8sAgent(
            context=args.context,
            namespace=args.namespace,
            kubeconfig_path=args.kubeconfig
        )
    except Exception as e:
        print(f"{Colors.RED}Error: {e}{Colors.ENDC}")
        sys.exit(1)
    
    action = args.action
    
    if action == 'pods':
        agent.get_pods()
    elif action == 'all':
        agent.get_pods()
        agent.get_secrets()
        agent.monitor_namespace()
    elif action == 'details' and args.pod:
        agent.get_pod_details(args.pod)
    elif action == 'logs' and args.pod:
        agent.get_pod_logs(args.pod, False, args.container)
    elif action == 'troubleshoot' and args.pod:
        agent.troubleshoot_pod(args.pod)
    elif action == 'secrets':
        agent.get_secrets()
    elif action == 'search-secret' and args.search:
        agent.search_secret_usage(args.search)
    elif action == 'monitor':
        agent.monitor_namespace()
    elif action == 'thread-dump' and args.pod:
        agent.thread_dump(args.pod, args.container)
    elif action == 'heap-dump' and args.pod:
        agent.heap_dump(args.pod, args.container)
    elif action == 'get-all':
        agent.get_all_resources()
    else:
        print(f"{Colors.RED}Invalid action or missing required arguments{Colors.ENDC}")
        show_help()

if __name__ == "__main__":
    main()
