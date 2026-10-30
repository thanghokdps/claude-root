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


def test_flag_values_are_not_read_as_the_subcommand():
    path = repo()
    assert gate(path, "kubectl -n production apply -f k8s/")[0] == "deny"
    assert gate(path, "kubectl --context prod delete deploy/api")[0] == "deny"
    assert gate(path, "helm -n production upgrade api charts/api")[0] == "deny"
    assert gate(path, "terraform -chdir=envs/prod apply")[0] == "deny"
    assert gate(path, "kubectl -n staging get pods")[0] == "allow"


def test_destroy_variants_and_kind_slash_name():
    path = repo()
    assert gate(path, "terraform apply -destroy -var-file=dev.tfvars")[0] == "deny"
    assert gate(path, "terraform plan -destroy -out=p")[0] == "ask"  # the saved plan's apply shows no -destroy
    assert gate(path, "kubectl delete ns/staging")[0] == "deny"
    assert gate(path, "kubectl delete -n dev namespace staging")[0] == "deny"


def test_background_subshell_and_substitution_are_segments():
    path = repo()
    for cmd in ("terraform plan & terraform apply -var-file=prod.tfvars", "(kubectl apply -f k8s/ -n production)",
                "echo $(helm upgrade api charts/api -n production)", "echo `terraform apply -var-file=prod.tfvars`",
                "{ kubectl delete node w1; }"):
        assert gate(path, cmd)[0] == "deny", cmd


def test_wrappers_are_peeled():
    path = repo()
    for cmd in ("sudo terraform apply -var-file=prod.tfvars", "timeout 300 kubectl apply -f k8s/ -n production",
                "command helm upgrade api charts/api -n production", "pnpm exec terraform apply -var-file=prod.tfvars",
                "npx -y terraform apply -var-file=prod.tfvars", "nohup terraform apply -var-file=prod.tfvars",
                "env TF_WORKSPACE=prod terraform apply"):
        assert gate(path, cmd)[0] == "deny", cmd
    assert gate(path, "sudo terraform plan")[0] == "allow"


def test_unknown_wrappers_and_scripts_fail_closed():
    path = repo()
    assert gate(path, "make deploy TOOL=terraform apply")[0] == "ask"
    assert gate(path, "bash scripts/deploy.sh terraform")[0] == "ask"
    assert gate(path, "cat cmd.txt | bash")[0] == "allow"  # nothing in the text names a tool
    assert gate(path, "echo 'kubectl apply -f k8s/ -n production' | bash")[0] == "ask"
    assert gate(path, "source ./apply-helm.sh")[0] == "ask"
    assert gate(path, "make build")[0] == "allow"


def test_unknown_flag_cannot_smuggle_a_read_only_subcommand():
    path = repo()
    assert gate(path, "kubectl --as admin apply -f k8s/ -n production")[0] == "deny"  # --as takes a value
    assert gate(path, "kubectl --odd-flag get apply -f k8s/ -n production")[0] == "ask"  # fail closed, never 'get'
    assert gate(path, "helm --kube-as-user me upgrade api charts/api -n production")[0] == "deny"
    assert gate(path, "helm diff upgrade api charts/api -n production")[0] == "allow"
    # `diff` behind an unknown flag may be that flag's value, with `upgrade` the real verb: never the read-only shortcut
    assert gate(path, "helm --kube-token diff upgrade api charts/api -n production")[0] != "allow"
    assert gate(path, "helm --odd diff upgrade api charts/api -n production")[0] != "allow"


def test_substitution_inside_double_quotes_is_a_segment():
    path = repo()
    assert gate(path, 'echo "$(terraform apply -var-file=prod.tfvars)"')[0] == "deny"
    assert gate(path, 'OUT="$(kubectl apply -f k8s/ -n production)"')[0] == "deny"
    assert gate(path, 'echo "`helm upgrade api charts/api -n production`"')[0] == "deny"
    assert gate(path, "echo '$(terraform apply -var-file=prod.tfvars)'")[0] == "allow"  # single quotes run nothing
    # operators inside the substitution split again: the apply is not hidden behind an inert `echo a;`
    assert gate(path, 'echo "$(echo a; terraform apply -var-file=prod.tfvars)"')[0] == "deny"
    assert gate(path, 'echo "`true && kubectl apply -f k8s/ -n production`"')[0] == "deny"


def test_programs_that_can_execute_are_not_inert():
    path = repo()
    assert gate(path, "find . -name '*.yaml' -exec kubectl apply -f {} -n production \\;")[0] == "ask"
    assert gate(path, "git -c alias.a='!terraform apply -var-file=prod.tfvars' a")[0] == "ask"
    assert gate(path, "awk 'BEGIN{system(\"terraform apply\")}'")[0] == "ask"
    assert gate(path, "git commit -m 'docs: terraform apply steps'")[0] == "allow"
    assert gate(path, "grep -rn 'kubectl apply' docs/")[0] == "allow"


def test_git_is_inert_only_for_safe_subcommands():
    path = repo()
    for cmd in ("git rebase -x 'terraform apply -var-file=prod.tfvars' HEAD~2", "git bisect run kubectl apply -f k8s/ -n production",
                "git submodule foreach 'helm upgrade api charts/api -n production'",
                "git difftool --extcmd='terraform apply -var-file=prod.tfvars'",
                "GIT_PAGER='terraform apply -var-file=prod.tfvars' git log", "GIT_SSH_COMMAND='kubectl apply -f k8s/ -n production' git fetch",
                "git fetch --upload-pack='terraform apply -var-file=prod.tfvars' origin", "git push -u origin x --receive-pack='kubectl apply -f k8s/ -n production'",
                "git --exec-path=/tmp/x log terraform apply", "git -C rebase log -x 'terraform apply -var-file=prod.tfvars'"):
        assert gate(path, cmd)[0] == "ask", cmd
    assert gate(path, "git -C /tmp/repo log --grep 'terraform apply'")[0] == "allow"  # -C takes a value, log is the verb


def test_quoted_substitution_restores_the_quote_and_unbalanced_quotes_ask():
    path = repo()
    # after `)` the text is back inside the double quote, so the `;` is literal and the apply is a real segment again
    assert gate(path, 'echo "a$(true)"; terraform apply -var-file=prod.tfvars')[0] == "deny"
    assert gate(path, 'echo "`true`; done"; kubectl apply -f k8s/ -n production')[0] == "deny"
    assert gate(path, 'echo "$(terraform plan -var-file=prod.tfvars) ok"')[0] == "allow"
    assert gate(path, "echo 'x; terraform apply -var-file=prod.tfvars")[0] == "ask"  # unterminated quote
    assert gate(path, "echo 'unterminated but harmless")[0] == "allow"
    assert gate(path, "git log --grep 'terraform apply'")[0] == "allow"
    assert gate(path, "git add docs/terraform-apply.md")[0] == "allow"


def test_inner_parens_cannot_close_the_substitution_early():
    path = repo()
    # the `)` of `(x)` must not restore the double quote and hide the apply behind inert `echo`
    assert gate(path, 'echo "$(f (x); terraform apply -var-file=prod.tfvars)"')[0] == "deny"
    assert gate(path, 'echo "$(echo $(true); kubectl apply -f k8s/ -n production)"')[0] == "deny"
    # literal text inside the quote: never denied; the split quote may leave an unbalanced segment, which asks
    assert gate(path, 'echo "$((1+2)); helm upgrade api charts/api -n production"')[0] != "deny"


def test_git_unknown_global_options_are_not_inert():
    path = repo()
    assert gate(path, "git --odd-opt log 'terraform apply'")[0] == "ask"
    assert gate(path, "git --attr-source=x log 'terraform apply'")[0] == "allow"  # known value option, inline form
    assert gate(path, "git --no-pager log --grep 'kubectl apply'")[0] == "allow"
    assert gate(path, "git --config=alias.a='!terraform apply' a")[0] == "ask"


def test_escaped_parens_and_unclosed_substitutions_fail_closed():
    path = repo()
    # `\)` is a literal paren, so the substitution stays open and the apply runs inside it
    assert gate(path, 'echo "$(true \\); terraform apply -var-file=prod.tfvars)"')[0] == "deny"
    assert gate(path, 'echo "$(true; kubectl apply -f k8s/ -n production"')[0] == "ask"  # never closed: do not trust the split
    assert gate(path, 'echo "a \\" b"; helm upgrade api charts/api -n production')[0] == "deny"  # escaped quote stays inside
    assert gate(path, 'echo "$(true)"')[0] == "allow"


def test_git_abbreviations_and_any_variable_are_not_inert():
    path = repo()
    assert gate(path, "git fetch --upload='terraform apply -var-file=prod.tfvars' origin")[0] == "ask"
    assert gate(path, "PAGER='kubectl apply -f k8s/ -n production' git log")[0] == "ask"
    assert gate(path, "EDITOR='helm upgrade api charts/api -n production' git commit")[0] == "ask"
    assert gate(path, "git log --oneline -- docs/terraform-apply.md")[0] == "allow"


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
