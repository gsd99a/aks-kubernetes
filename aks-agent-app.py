#!/usr/bin/env python3
"""
AKS Kubernetes Agent - Interactive CLI Tool
Run this on your Ubuntu box to manage AKS operations
"""

import argparse
import json
import subprocess
import sys
import os
from datetime import datetime

class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'

def run_cmd(cmd, capture=True, show_cmd=True):
    """Run kubectl/az command and return output"""
    if show_cmd:
        print(f"\n{Colors.CYAN}>>> {cmd}{Colors.ENDC}")
    
    try:
        result = subprocess.run(
            cmd, shell=True, capture_output=capture, 
            text=True, timeout=60
        )
        return result.stdout, result.stderr, result.returncode
    except subprocess.TimeoutExpired:
        return "", "Command timed out", 1
    except Exception as e:
        return "", str(e), 1

def check_prerequisites():
    """Check if kubectl and az are available"""
    print(f"\n{Colors.HEADER}{'='*60}{Colors.ENDC}")
    print(f"{Colors.BOLD}Checking Prerequisites...{Colors.ENDC}")
    
    _, kubectl_err, kubectl_rc = run_cmd("kubectl version --client", show_cmd=False)
    _, az_err, az_rc = run_cmd("az version", show_cmd=False)
    
    if kubectl_rc != 0:
        print(f"{Colors.RED}✗ kubectl not found!{Colors.ENDC}")
        print(f"  Install: curl -LO \"https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl\"")
        return False
    
    _, kubectl_server, _ = run_cmd("kubectl version --short 2>/dev/null | head -1", show_cmd=False)
    if kubectl_server:
        print(f"{Colors.GREEN}✓ kubectl installed{Colors.ENDC}")
    
    if az_rc == 0:
        print(f"{Colors.GREEN}✓ Azure CLI installed{Colors.ENDC}")
    
    return True

def get_namespaces():
    """List all namespaces"""
    print(f"\n{Colors.HEADER}{'='*60}{Colors.ENDC}")
    print(f"{Colors.BOLD}Fetching Namespaces...{Colors.ENDC}")
    
    stdout, _, rc = run_cmd("kubectl get namespaces -o name")
    if rc == 0:
        namespaces = [ns.strip().replace('namespace/', '') for ns in stdout.strip().split('\n') if ns.strip()]
        for ns in namespaces:
            print(f"  - {ns}")
        return namespaces
    return []

def get_pods(namespace):
    """Get all pods in namespace"""
    print(f"\n{Colors.HEADER}{'='*60}{Colors.ENDC}")
    print(f"{Colors.BOLD}Pods in Namespace: {namespace}{Colors.ENDC}")
    
    stdout, _, rc = run_cmd(f"kubectl get pods -n {namespace} -o wide")
    if rc == 0:
        print(stdout)
    return stdout

def get_pod_details(pod_name, namespace):
    """Get detailed pod information"""
    print(f"\n{Colors.HEADER}{'='*60}{Colors.ENDC}")
    print(f"{Colors.BOLD}Pod Details: {pod_name}{Colors.ENDC}")
    
    stdout, _, rc = run_cmd(f"kubectl describe pod {pod_name} -n {namespace}")
    if rc == 0:
        print(stdout)
    return stdout

def get_pod_logs(pod_name, namespace, previous=False, container=""):
    """Get pod logs"""
    print(f"\n{Colors.HEADER}{'='*60}{Colors.ENDC}")
    print(f"{Colors.BOLD}Pod Logs: {pod_name}{Colors.ENDC}")
    
    cmd = f"kubectl logs {pod_name} -n {namespace}"
    if previous:
        cmd += " --previous"
    if container:
        cmd += f" -c {container}"
    
    stdout, stderr, rc = run_cmd(cmd)
    if stdout:
        print(stdout)
    if stderr:
        print(f"{Colors.YELLOW}{stderr}{Colors.ENDC}")
    return stdout

def troubleshoot_pod(pod_name, namespace):
    """Complete pod troubleshooting"""
    print(f"\n{Colors.HEADER}{'='*60}{Colors.ENDC}")
    print(f"{Colors.BOLD}Troubleshooting Pod: {pod_name}{Colors.ENDC}")
    print(f"{Colors.HEADER}{'='*60}{Colors.ENDC}")
    
    print(f"\n{Colors.YELLOW}[1/6] Pod Status{Colors.ENDC}")
    stdout, _, _ = run_cmd(f"kubectl get pod {pod_name} -n {namespace} -o jsonpath='{{.status.phase}}'")
    print(f"Status: {stdout}")
    
    print(f"\n{Colors.YELLOW}[2/6] Restart Count{Colors.ENDC}")
    stdout, _, _ = run_cmd(f"kubectl get pod {pod_name} -n {namespace} -o jsonpath='{{.status.containerStatuses[*].restartCount}}'")
    print(f"Restarts: {stdout}")
    
    print(f"\n{Colors.YELLOW}[3/6] Container Status{Colors.ENDC}")
    stdout, _, _ = run_cmd(f"kubectl get pod {pod_name} -n {namespace} -o jsonpath='{{range .status.containerStatuses[*]}}{{.name}}:{{.state}};{{end}}'")
    print(stdout)
    
    print(f"\n{Colors.YELLOW}[4/6] Last Termination Message{Colors.ENDC}")
    stdout, _, _ = run_cmd(f"kubectl get pod {pod_name} -n {namespace} -o jsonpath='{{.status.containerStatuses[*].lastState.terminated.message}}'")
    if stdout.strip():
        print(stdout)
    else:
        print("(No previous termination)")
    
    print(f"\n{Colors.YELLOW}[5/6] Exit Code{Colors.ENDC}")
    stdout, _, _ = run_cmd(f"kubectl get pod {pod_name} -n {namespace} -o jsonpath='{{.status.containerStatuses[*].lastState.terminated.exitCode}}'")
    if stdout.strip():
        print(f"Exit Code: {stdout}")
    
    print(f"\n{Colors.YELLOW}[6/6] OOMKilled Check{Colors.ENDC}")
    stdout, _, _ = run_cmd(f"kubectl get pod {pod_name} -n {namespace} -o jsonpath='{{.status.containerStatuses[*].lastState.terminated.reason}}'")
    if 'OOMKilled' in stdout:
        print(f"{Colors.RED}⚠ Pod was OOMKilled!{Colors.ENDC}")
    else:
        print("Not OOMKilled")
    
    print(f"\n{Colors.YELLOW}Previous Container Logs:{Colors.ENDC}")
    run_cmd(f"kubectl logs {pod_name} -n {namespace} --previous 2>&1 | tail -50")
    
    print(f"\n{Colors.YELLOW}Pod Events:{Colors.ENDC}")
    run_cmd(f"kubectl get events -n {namespace} --field-selector involvedObject.name={pod_name} --sort-by='.lastTimestamp'")

def get_secrets(namespace):
    """List secrets in namespace"""
    print(f"\n{Colors.HEADER}{'='*60}{Colors.ENDC}")
    print(f"{Colors.BOLD}Secrets in Namespace: {namespace}{Colors.ENDC}")
    
    stdout, _, rc = run_cmd(f"kubectl get secrets -n {namespace}")
    if rc == 0:
        print(stdout)
    return stdout

def get_secret_value(secret_name, namespace):
    """Get decoded secret value"""
    print(f"\n{Colors.HEADER}{'='*60}{Colors.ENDC}")
    print(f"{Colors.BOLD}Secret Value: {secret_name}{Colors.ENDC}")
    
    stdout, _, rc = run_cmd(f"kubectl get secret {secret_name} -n {namespace} -o jsonpath='{{{{.data}}}}' | base64 -d")
    if rc == 0:
        print(stdout)

def search_secret_usage(search_string, namespace):
    """Search for secret string across all resources"""
    print(f"\n{Colors.HEADER}{'='*60}{Colors.ENDC}")
    print(f"{Colors.BOLD}Searching for: '{search_string}' in namespace: {namespace}{Colors.ENDC}")
    print(f"{Colors.HEADER}{'='*60}{Colors.ENDC}")
    
    print(f"\n{Colors.YELLOW}[1/4] Kubernetes Secrets{Colors.ENDC}")
    run_cmd(f"kubectl get secrets -n {namespace} -o json | jq -r --arg s '{search_string}' '.items[] | select(.data | tojson | @base64d | contains($s)) | .metadata.name' 2>/dev/null")
    
    print(f"\n{Colors.YELLOW}[2/4] ConfigMaps{Colors.ENDC}")
    run_cmd(f"kubectl get configmap -n {namespace} -o json | jq -r --arg s '{search_string}' '.items[] | select(.data | tojson | contains($s)) | .metadata.name' 2>/dev/null")
    
    print(f"\n{Colors.YELLOW}[3/4] Deployments/Pods{Colors.ENDC}")
    run_cmd(f"kubectl get deployment,statefulset,daemonset,pod -n {namespace} -o json | jq -r --arg s '{search_string}' '.items[] | select(.spec | tojson | contains($s)) | \"\\(.kind): \\(.metadata.name)\"' 2>/dev/null")
    
    print(f"\n{Colors.YELLOW}[4/4] Events{Colors.ENDC}")
    run_cmd(f"kubectl get events -n {namespace} | grep -i '{search_string}'")

def keyvault_list(keyvault_name):
    """List KeyVault contents"""
    print(f"\n{Colors.HEADER}{'='*60}{Colors.ENDC}")
    print(f"{Colors.BOLD}Azure KeyVault: {keyvault_name}{Colors.ENDC}")
    print(f"{Colors.HEADER}{'='*60}{Colors.ENDC}")
    
    print(f"\n{Colors.YELLOW}Secrets:{Colors.ENDC}")
    run_cmd(f"az keyvault secret list --vault-name {keyvault_name} --output table 2>/dev/null || echo 'az CLI error or no access'")
    
    print(f"\n{Colors.YELLOW}Certificates:{Colors.ENDC}")
    run_cmd(f"az keyvault certificate list --vault-name {keyvault_name} --output table 2>/dev/null || echo 'az CLI error or no access'")
    
    print(f"\n{Colors.YELLOW}Keys:{Colors.ENDC}")
    run_cmd(f"az keyvault key list --vault-name {keyvault_name} --output table 2>/dev/null || echo 'az CLI error or no access'")

def search_keyvault(search_string, keyvault_name):
    """Search in Azure KeyVault"""
    print(f"\n{Colors.HEADER}{'='*60}{Colors.ENDC}")
    print(f"{Colors.BOLD}Searching KeyVault '{keyvault_name}' for: '{search_string}'{Colors.ENDC}")
    print(f"{Colors.HEADER}{'='*60}{Colors.ENDC}")
    
    print(f"\n{Colors.YELLOW}Matching Secrets:{Colors.ENDC}")
    run_cmd(f"az keyvault secret list --vault-name {keyvault_name} --output json 2>/dev/null | jq -r --arg s '{search_string}' '.[] | select(.id | test($s; \"i\")) | .id'")
    
    print(f"\n{Colors.YELLOW}Matching Certificates:{Colors.ENDC}")
    run_cmd(f"az keyvault certificate list --vault-name {keyvault_name} --output json 2>/dev/null | jq -r --arg s '{search_string}' '.[] | select(.id | test($s; \"i\")) | .id'")
    
    print(f"\n{Colors.YELLOW}Matching Keys:{Colors.ENDC}")
    run_cmd(f"az keyvault key list --vault-name {keyvault_name} --output json 2>/dev/null | jq -r --arg s '{search_string}' '.[] | select(.kid | test($s; \"i\")) | .kid'")

def thread_dump(pod_name, namespace, container=""):
    """Generate thread dump"""
    print(f"\n{Colors.HEADER}{'='*60}{Colors.ENDC}")
    print(f"{Colors.BOLD}Generating Thread Dump: {pod_name}{Colors.ENDC}")
    
    print(f"\n{Colors.YELLOW}Step 1: Finding Java PID{Colors.ENDC}")
    pid_cmd = f"kubectl exec {pod_name} -n {namespace}"
    if container:
        pid_cmd += f" -c {container}"
    pid_cmd += " -- jps -l 2>/dev/null | grep -v Jps | head -1 | awk '{print $1}'"
    
    stdout, _, _ = run_cmd(pid_cmd)
    java_pid = stdout.strip()
    
    if not java_pid:
        print(f"{Colors.RED}No Java process found!{Colors.ENDC}")
        print("Trying generic thread dump...")
        kill_cmd = f"kubectl exec {pod_name} -n {namespace}"
        if container:
            kill_cmd += f" -c {container}"
        kill_cmd += " -- kill -3 1"
        run_cmd(kill_cmd)
        return
    
    print(f"Java PID: {java_pid}")
    
    print(f"\n{Colors.YELLOW}Step 2: Thread Dump{Colors.ENDC}")
    dump_cmd = f"kubectl exec {pod_name} -n {namespace}"
    if container:
        dump_cmd += f" -c {container}"
    dump_cmd += f" -- jstack -l {java_pid}"
    
    stdout, stderr, rc = run_cmd(dump_cmd)
    if rc == 0:
        print(stdout)
        print(f"\n{Colors.GREEN}✓ Thread dump generated successfully{Colors.ENDC}")
    else:
        print(f"{Colors.RED}Thread dump failed: {stderr}{Colors.ENDC}")

def heap_dump(pod_name, namespace, container=""):
    """Generate heap dump"""
    print(f"\n{Colors.HEADER}{'='*60}{Colors.ENDC}")
    print(f"{Colors.BOLD}Generating Heap Dump: {pod_name}{Colors.ENDC}")
    
    print(f"\n{Colors.YELLOW}Step 1: Finding Java PID{Colors.ENDC}")
    pid_cmd = f"kubectl exec {pod_name} -n {namespace}"
    if container:
        pid_cmd += f" -c {container}"
    pid_cmd += " -- jps -l 2>/dev/null | grep -v Jps | head -1 | awk '{print $1}'"
    
    stdout, _, _ = run_cmd(pid_cmd)
    java_pid = stdout.strip()
    
    if not java_pid:
        print(f"{Colors.RED}No Java process found!{Colors.ENDC}")
        return
    
    print(f"Java PID: {java_pid}")
    
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    filename = f"/tmp/heapdump-{timestamp}.hprof"
    
    print(f"\n{Colors.YELLOW}Step 2: Heap Dump to {filename}{Colors.ENDC}")
    dump_cmd = f"kubectl exec {pod_name} -n {namespace}"
    if container:
        dump_cmd += f" -c {container}"
    dump_cmd += f" -- jmap -dump:format=b,file={filename} {java_pid}"
    
    stdout, stderr, rc = run_cmd(dump_cmd)
    if rc == 0:
        print(f"{Colors.GREEN}✓ Heap dump created: {filename}{Colors.ENDC}")
        
        print(f"\n{Colors.YELLOW}Step 3: Copying to local machine{Colors.ENDC}")
        run_cmd(f"kubectl cp {namespace}/{pod_name}:{filename} ./heapdump-{timestamp}.hprof")
        print(f"{Colors.GREEN}✓ Saved as: heapdump-{timestamp}.hprof{Colors.ENDC}")
    else:
        print(f"{Colors.RED}Heap dump failed: {stderr}{Colors.ENDC}")

def monitor_namespace(namespace):
    """Monitor all resources in namespace"""
    print(f"\n{Colors.HEADER}{'='*60}{Colors.ENDC}")
    print(f"{Colors.BOLD}Monitoring Namespace: {namespace}{Colors.ENDC}")
    print(f"{Colors.HEADER}{'='*60}{Colors.ENDC}")
    
    print(f"\n{Colors.YELLOW}[1] Pods{Colors.ENDC}")
    run_cmd(f"kubectl get pods -n {namespace}")
    
    print(f"\n{Colors.YELLOW}[2] Deployments{Colors.ENDC}")
    run_cmd(f"kubectl get deployments -n {namespace}")
    
    print(f"\n{Colors.YELLOW}[3] Services{Colors.ENDC}")
    run_cmd(f"kubectl get svc -n {namespace}")
    
    print(f"\n{Colors.YELLOW}[4] ConfigMaps{Colors.ENDC}")
    run_cmd(f"kubectl get configmap -n {namespace}")
    
    print(f"\n{Colors.YELLOW}[5] Secrets{Colors.ENDC}")
    run_cmd(f"kubectl get secrets -n {namespace}")
    
    print(f"\n{Colors.YELLOW}[6] Events{Colors.ENDC}")
    run_cmd(f"kubectl get events -n {namespace} --sort-by='.lastTimestamp'")

def interactive_mode():
    """Interactive menu mode"""
    while True:
        print(f"\n{Colors.HEADER}{'='*60}{Colors.ENDC}")
        print(f"{Colors.BOLD}AKS Kubernetes Agent - Interactive Mode{Colors.ENDC}")
        print(f"{Colors.HEADER}{'='*60}{Colors.ENDC}")
        print("""
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
        """)
        
        choice = input(f"{Colors.CYAN}Select option (0-12): {Colors.ENDC}").strip()
        
        if choice == '0':
            print("Goodbye!")
            break
        
        namespace = input("Namespace: ").strip()
        if not namespace:
            print("Namespace required!")
            continue
        
        if choice == '1':
            get_pods(namespace)
        
        elif choice == '2':
            pod = input("Pod name: ").strip()
            if pod:
                get_pod_details(pod, namespace)
        
        elif choice == '3':
            pod = input("Pod name: ").strip()
            prev = input("Previous logs? (y/n): ").strip().lower() == 'y'
            cont = input("Container (optional): ").strip()
            if pod:
                get_pod_logs(pod, namespace, prev, cont)
        
        elif choice == '4':
            pod = input("Pod name: ").strip()
            if pod:
                troubleshoot_pod(pod, namespace)
        
        elif choice == '5':
            get_secrets(namespace)
        
        elif choice == '6':
            secret = input("Secret name: ").strip()
            if secret:
                get_secret_value(secret, namespace)
        
        elif choice == '7':
            search = input("Search string: ").strip()
            if search:
                search_secret_usage(search, namespace)
        
        elif choice == '8':
            keyvault = input("KeyVault name: ").strip()
            if keyvault:
                keyvault_list(keyvault)
        
        elif choice == '9':
            keyvault = input("KeyVault name: ").strip()
            search = input("Search string: ").strip()
            if keyvault and search:
                search_keyvault(search, keyvault)
        
        elif choice == '10':
            monitor_namespace(namespace)
        
        elif choice == '11':
            pod = input("Pod name: ").strip()
            cont = input("Container (optional): ").strip()
            if pod:
                thread_dump(pod, namespace, cont)
        
        elif choice == '12':
            pod = input("Pod name: ").strip()
            cont = input("Container (optional): ").strip()
            if pod:
                heap_dump(pod, namespace, cont)

def main():
    parser = argparse.ArgumentParser(description="AKS Kubernetes Agent - CLI Tool")
    parser.add_argument("--interactive", "-i", action="store_true", help="Interactive mode")
    parser.add_argument("--namespace", "-n", help="Kubernetes namespace")
    parser.add_argument("--pod", "-p", help="Pod name")
    parser.add_argument("--container", "-c", help="Container name")
    parser.add_argument("--keyvault", "-kv", help="Azure KeyVault name")
    parser.add_argument("--search", "-s", help="Search string")
    parser.add_argument("--action", "-a", choices=[
        'pods', 'details', 'logs', 'troubleshoot', 'secrets', 'secret-value',
        'search-secret', 'keyvault', 'search-keyvault', 'monitor',
        'thread-dump', 'heap-dump', 'namespaces', 'check'
    ], help="Action to perform")
    
    args = parser.parse_args()
    
    if args.interactive or len(sys.argv) == 1:
        if not check_prerequisites():
            sys.exit(1)
        interactive_mode()
        return
    
    if not check_prerequisites():
        sys.exit(1)
    
    namespace = args.namespace
    pod = args.pod
    container = args.container
    keyvault = args.keyvault
    search = args.search
    action = args.action
    
    if action == 'check':
        print("Prerequisites OK")
        sys.exit(0)
    
    if action == 'namespaces':
        get_namespaces()
        sys.exit(0)
    
    if not namespace:
        print("Namespace required! Use -n <namespace>")
        sys.exit(1)
    
    if action == 'pods':
        get_pods(namespace)
    elif action == 'details' and pod:
        get_pod_details(pod, namespace)
    elif action == 'logs' and pod:
        get_pod_logs(pod, namespace, False, container)
    elif action == 'troubleshoot' and pod:
        troubleshoot_pod(pod, namespace)
    elif action == 'secrets':
        get_secrets(namespace)
    elif action == 'secret-value' and pod:
        get_secret_value(pod, namespace)
    elif action == 'search-secret' and search:
        search_secret_usage(search, namespace)
    elif action == 'keyvault' and keyvault:
        keyvault_list(keyvault)
    elif action == 'search-keyvault' and keyvault and search:
        search_keyvault(search, keyvault)
    elif action == 'monitor':
        monitor_namespace(namespace)
    elif action == 'thread-dump' and pod:
        thread_dump(pod, namespace, container)
    elif action == 'heap-dump' and pod:
        heap_dump(pod, namespace, container)

if __name__ == "__main__":
    main()
