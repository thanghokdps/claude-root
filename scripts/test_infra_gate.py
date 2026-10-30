#!/usr/bin/env python3
"""Tests for plugins/ship/hooks/infra-gate.sh. Run: python3 scripts/test_infra_gate.py"""
import json
import os
import subprocess
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HOOK = os.path.join(ROOT, "plugins", "ship", "hooks", "infra-gate.sh")


def repo(files=("main.tf",), config=None):
    path = tempfile.mkdtemp(prefix="infra-gate-")
    subprocess.run(["git", "-C", path, "init", "-q"], check=True)
    for rel in files:
        full = os.path.join(path, rel)
        os.makedirs(os.path.dirname(full), exist_ok=True)
        with open(full, "w") as f:
            f.write("")
    if config is not None:
        os.makedirs(os.path.join(path, ".claude"), exist_ok=True)
        with open(os.path.join(path, ".claude", "infra-gate.json"), "w") as f:
            json.dump(config, f)
    return path


def gate(path, command):
    payload = {"cwd": path, "session_id": "s", "hook_event_name": "PreToolUse", "tool_name": "Bash",
               "tool_input": {"command": command}}
    r = subprocess.run([HOOK], input=json.dumps(payload), capture_output=True, text=True)
    assert r.returncode == 0, r.stderr
    if not r.stdout.strip():
        return "allow", ""
    out = json.loads(r.stdout)["hookSpecificOutput"]
    return out["permissionDecision"], out["permissionDecisionReason"]


def test_inactive_without_infra_files():
    path = repo(files=("package.json",))
    assert gate(path, "terraform apply -var-file=prod.tfvars")[0] == "allow"
    assert gate(tempfile.mkdtemp(), "kubectl delete ns prod")[0] == "allow"  # not a git repo


def test_read_only_commands_pass():
    path = repo(files=("envs/prod/main.tf", "k8s/deploy.yaml", "charts/api/Chart.yaml"))
    for cmd in ("terraform plan -var-file=envs/prod/prod.tfvars -out=plan.out", "terraform validate", "terraform fmt -check",
                "kubectl get pods -n production", "kubectl diff -f k8s/", "kubectl describe deploy api --context prod",
                "helm template api charts/api -f values-prod.yaml", "helm diff upgrade api charts/api -n production",
                "helm lint charts/api", "echo 'terraform apply'"):
        assert gate(path, cmd)[0] == "allow", cmd


def test_production_apply_is_denied():
    path = repo()
    for cmd in ("terraform apply -var-file=prod.tfvars", "terraform apply plan.out -var-file envs/production/vars.tfvars",
                "TF_WORKSPACE=prod terraform apply -auto-approve", "tofu apply -var-file=live.tfvars",
                "kubectl apply -f k8s/ -n production", "kubectl apply -f k8s/ --context=gke-prod",
                "kubectl rollout restart deploy/api -n prod", "kubectl scale deploy/api --replicas=0 --namespace production",
                "helm upgrade --install api charts/api -n production", "helm rollback api 3 --kube-context prod",
                "npx terraform apply -var-file=prod.tfvars"):
        d, why = gate(path, cmd)
        assert d == "deny" and "person" in why, (cmd, d, why)


def test_destroy_and_cluster_scope_deletes_are_always_denied():
    path = repo()
    assert gate(path, "terraform destroy -var-file=dev.tfvars")[0] == "deny"
    assert gate(path, "kubectl delete namespace staging")[0] == "deny"
    assert gate(path, "kubectl delete node worker-1")[0] == "deny"


def test_non_production_and_unnamed_targets_ask():
    path = repo()
    for cmd in ("terraform apply plan.out -var-file=staging.tfvars", "terraform apply", "kubectl apply -f k8s/ -n staging",
                "kubectl delete pod api-1 -n dev", "helm upgrade --install api charts/api -n staging", "helm install api charts/api"):
        d, why = gate(path, cmd)
        assert d == "ask", (cmd, d, why)


def test_switching_onto_production_asks():
    path = repo()
    assert gate(path, "terraform workspace select prod")[0] == "ask"
    assert gate(path, "kubectl config use-context gke-production")[0] == "ask"
    assert gate(path, "terraform workspace select dev")[0] == "allow"


def test_wrappers_are_denied():
    path = repo()
    for cmd in ("bash -c 'terraform apply -var-file=prod.tfvars'", "eval terraform apply", "echo prod | xargs -I{} kubectl apply -n {} -f k8s/",
                "sh -c \"helm upgrade api charts/api -n production\""):
        assert gate(path, cmd)[0] == "deny", cmd


def test_chained_segments_are_each_checked():
    path = repo()
    d, why = gate(path, "terraform plan -out=p && terraform apply p -var-file=prod.tfvars")
    assert d == "deny", why
    assert gate(path, "cd envs/dev; terraform init; terraform plan")[0] == "allow"


def test_config_defines_production_names():
    path = repo(config={"production": ["eu-live"]})
    assert gate(path, "kubectl apply -f k8s/ -n eu-live")[0] == "deny"
    assert gate(path, "kubectl apply -f k8s/ -n production")[0] == "ask"  # not in the configured list


def test_config_alone_activates_the_gate():
    path = repo(files=("README.md",), config={})
    assert gate(path, "helm upgrade api charts/api -n production")[0] == "deny"


if __name__ == "__main__":
    tests = [v for k, v in dict(globals()).items() if k.startswith("test_")]
    for t in tests:
        t()
    print(f"test_infra_gate: {len(tests)} passed")
