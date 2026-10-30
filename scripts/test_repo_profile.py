#!/usr/bin/env python3
"""Tests for plugins/core/hooks/repo-profile.sh.
Run: python3 scripts/test_repo_profile.py"""
import json
import os
import subprocess
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HOOK = os.path.join(ROOT, "plugins", "core", "hooks", "repo-profile.sh")


def repo(files=None):
    path = tempfile.mkdtemp(prefix="repo-profile-")
    subprocess.run(["git", "-C", path, "init", "-q"], check=True)
    for rel, content in (files or {}).items():
        full = os.path.join(path, rel)
        os.makedirs(os.path.dirname(full), exist_ok=True)
        with open(full, "w") as f:
            f.write(content if isinstance(content, str) else json.dumps(content))
    return path


def config_dir(enabled=None):
    path = tempfile.mkdtemp(prefix="repo-profile-cfg-")
    if enabled is not None:
        with open(os.path.join(path, "settings.json"), "w") as f:
            json.dump({"enabledPlugins": enabled}, f)
    return path


def run(cwd, cfg=None, env=None, event="SessionStart"):
    payload = json.dumps({"hook_event_name": event, "source": "startup", "cwd": cwd})
    # A machine-wide gitignore would hide whether the hook excludes settings.local.json itself.
    e = {**os.environ, "CLAUDE_CONFIG_DIR": cfg or config_dir(), "GIT_CONFIG_GLOBAL": os.devnull,
         "XDG_CONFIG_HOME": tempfile.mkdtemp(prefix="repo-profile-xdg-"), **(env or {})}
    r = subprocess.run([HOOK], input=payload, capture_output=True, text=True, env=e)
    assert r.returncode == 0, r.stderr
    if not r.stdout.strip():
        return ""
    return json.loads(r.stdout)["hookSpecificOutput"]["additionalContext"]


def local_settings(cwd):
    p = os.path.join(cwd, ".claude", "settings.local.json")
    return json.load(open(p)) if os.path.exists(p) else None


AI_PKG = {"dependencies": {"next": "15", "@langchain/langgraph": "1", "@copilotkit/react-core": "1",
                           "@prisma/client": "6"}, "devDependencies": {"typescript": "5"}}


def test_hono_on_cloudflare_workers_monorepo():
    cwd = repo({"package.json": {"private": True},
                "apps/space/package.json": {"dependencies": {"hono": "4", "@langchain/core": "1"},
                                            "devDependencies": {"wrangler": "4", "typescript": "5"}}})
    ctx = run(cwd)
    for want in ["Hono", "Cloudflare Workers", "AI assistant"]:
        assert want in ctx, (want, ctx)


def test_vue_and_svelte_count_as_web_ui():
    for deps, label in (({"nuxt": "3"}, "Nuxt"), ({"vue": "3"}, "Vue"), ({"@sveltejs/kit": "2"}, "SvelteKit")):
        ctx = run(repo({"package.json": {"dependencies": deps}}))
        assert label in ctx and "/ui-feature" in ctx, (label, ctx)


def test_koa_and_elysia_are_backends():
    for dep, label in (("koa", "Koa"), ("elysia", "Elysia"), ("hono", "Hono")):
        ctx = run(repo({"package.json": {"dependencies": {dep: "1"}}}))
        assert label in ctx and "/api-endpoint" in ctx, (label, ctx)


def subagent_output(cwd, cfg=None):
    payload = json.dumps({"hook_event_name": "SubagentStart", "agent_type": "Explore", "cwd": cwd})
    e = {**os.environ, "CLAUDE_CONFIG_DIR": cfg or config_dir()}
    r = subprocess.run([HOOK], input=payload, capture_output=True, text=True, env=e)
    assert r.returncode == 0, r.stderr
    return json.loads(r.stdout)["hookSpecificOutput"]


def test_subagents_get_the_profile_but_never_write_settings():
    cwd = repo({"package.json": AI_PKG})
    out = subagent_output(cwd, config_dir({"ai@harness": False}))
    assert out["hookEventName"] == "SubagentStart"
    assert "AI assistant" in out["additionalContext"]
    assert "settings.local.json" not in out["additionalContext"]
    assert local_settings(cwd) is None


def test_ai_web_repo_gets_profile_and_agent_enabled_locally():
    cwd = repo({"package.json": AI_PKG, "prisma/schema.prisma": "", ".claude/docs/index.md": "# x"})
    ctx = run(cwd, config_dir({"ai@harness": False}))
    for want in ["Next.js", "AI assistant", "Prisma", "Roles: frontend, backend, ai", "/feature", "/agent-tool",
                 "/db-change", ".claude/docs/index.md", "/docs-sync", "ai@harness"]:
        assert want in ctx, (want, ctx)
    enabled = local_settings(cwd)["enabledPlugins"]
    assert enabled == {"frontend@harness": True, "backend@harness": True, "ai@harness": True}, enabled
    exclude = open(os.path.join(cwd, ".git", "info", "exclude")).read()
    assert ".claude/settings.local.json" in exclude


def test_existing_local_settings_are_merged_not_replaced():
    cwd = repo({"package.json": AI_PKG, ".claude/settings.local.json": {"permissions": {"allow": ["Bash(ls)"]}}})
    run(cwd)
    s = local_settings(cwd)
    assert s["permissions"] == {"allow": ["Bash(ls)"]}
    assert s["enabledPlugins"]["ai@harness"] is True


def test_plain_backend_repo_without_docs():
    cwd = repo({"package.json": {"dependencies": {"express": "4"}}})
    ctx = run(cwd)
    assert "Express" in ctx and "/api-endpoint" in ctx and "/project-init" in ctx, ctx
    assert "AI assistant" not in ctx and "Roles: backend." in ctx, ctx
    assert local_settings(cwd)["enabledPlugins"] == {"backend@harness": True}


def test_role_packs_follow_the_stack():
    cases = (({"package.json": {"dependencies": {"next": "15"}}}, {"frontend", "backend"}),
             ({"package.json": {"dependencies": {"react": "19", "vite": "6"}}}, {"frontend"}),
             ({"pyproject.toml": '[project]\ndependencies = ["fastapi"]\n'}, {"backend"}),
             ({"go.mod": "module x\n"}, {"backend"}),
             ({"package.json": {"private": True}, ".github/workflows/ci.yml": "on: push\n", "infra/main.tf": ""}, {"devops"}),
             ({"package.json": {"dependencies": {"express": "4"}}, "Dockerfile": "FROM node\n"}, {"backend", "devops"}),
             ({"package.json": {"dependencies": {"expo": "52", "react-native": "0.76", "react": "19"}}}, {"mobile"}),
             ({"package.json": {"dependencies": {"typescript": "5"}}}, set()))
    for files, want in cases:
        cwd = repo(files)
        run(cwd)
        got = {k.split("@")[0] for k in (local_settings(cwd) or {}).get("enabledPlugins", {})}
        assert got == want, (files, got)


def test_devops_repo_prefers_its_skills():
    cwd = repo({"package.json": {"private": True}, "k8s/deploy.yaml": "", "charts/api/Chart.yaml": ""})
    ctx = run(cwd)
    assert "Roles: devops." in ctx and "/infra-change" in ctx and "/pipeline" in ctx, ctx


def test_rn_alone_is_mobile_not_frontend():
    cwd = repo({"package.json": {"dependencies": {"expo": "52", "react-native": "0.76", "react": "19"}}})
    ctx = run(cwd)
    assert "Roles: mobile." in ctx and "/mobile-feature" in ctx and "/ui-feature" not in ctx, ctx


def test_python_ai_repo_with_alembic():
    cwd = repo({"pyproject.toml": '[project]\ndependencies = ["fastapi", "langgraph", "sqlalchemy"]\n',
                "alembic/env.py": ""})
    ctx = run(cwd)
    for want in ["Python", "FastAPI", "AI assistant", "Alembic", "/db-change"]:
        assert want in ctx, (want, ctx)


def test_monorepo_workspace_manifests_are_read():
    cwd = repo({"package.json": {"private": True}, "apps/web/package.json": {"dependencies": {"next": "15"}},
                "apps/agent/package.json": {"dependencies": {"@mastra/core": "1"}}})
    ctx = run(cwd)
    assert "Next.js" in ctx and "AI assistant" in ctx, ctx


def test_mobile_repo():
    cwd = repo({"package.json": {"dependencies": {"expo": "52", "react-native": "0.76"}}, "eas.json": {}})
    ctx = run(cwd)
    assert "React Native" in ctx and "/release-checklist" in ctx, ctx


def test_explicit_opt_out_is_respected():
    cwd = repo({"package.json": AI_PKG, ".claude/settings.json": {"enabledPlugins": {"ai@harness": False}}})
    ctx = run(cwd)
    assert "AI assistant" in ctx
    assert "ai@harness" not in local_settings(cwd)["enabledPlugins"]


def test_legacy_agent_pack_is_renamed_to_ai():
    cwd = repo({"package.json": AI_PKG, ".claude/settings.local.json": {"enabledPlugins": {"agent@harness": True}}})
    run(cwd, config_dir({"frontend@harness": True, "backend@harness": True}))
    assert local_settings(cwd)["enabledPlugins"] == {"ai@harness": True}


def test_already_enabled_at_user_scope_writes_nothing():
    cwd = repo({"package.json": AI_PKG})
    ctx = run(cwd, config_dir({"ai@harness": True, "frontend@harness": True, "backend@harness": True}))
    assert "AI assistant" in ctx and "settings.local.json" not in ctx
    assert local_settings(cwd) is None


def test_malformed_local_settings_is_left_alone():
    cwd = repo({"package.json": AI_PKG, ".claude/settings.local.json": "{not json"})
    run(cwd)
    assert open(os.path.join(cwd, ".claude", "settings.local.json")).read() == "{not json"


def test_new_repo_names_the_packs_that_are_off_before_a_stack_is_scaffolded():
    cwd = repo()
    ctx = run(cwd, config_dir({"frontend@harness": True}))
    assert "no manifest" in ctx and "ai@harness" in ctx and "new session" in ctx, ctx
    assert "frontend@harness" not in ctx, ctx
    assert local_settings(cwd) is None


def test_off_switch_prints_nothing():
    assert run(repo(), env={"CLAUDE_REPO_PROFILE": "0"}) == ""
    cwd = repo({"package.json": AI_PKG})
    assert run(cwd, env={"CLAUDE_REPO_PROFILE": "0"}) == ""
    assert local_settings(cwd) is None


def test_repo_modules_cannot_shadow_the_hooks_imports():
    cwd = repo({"package.json": AI_PKG, "json.py": "open(__file__ + '.ran', 'w').write('x')\n"})
    subprocess.run([HOOK], input=json.dumps({"cwd": cwd}), capture_output=True, text=True, cwd=cwd,
                   env={**os.environ, "CLAUDE_CONFIG_DIR": config_dir()})
    assert not os.path.exists(os.path.join(cwd, "json.py.ran"))


def test_symlinked_local_settings_or_claude_dir_is_never_written_through():
    outside = tempfile.mkdtemp(prefix="repo-profile-outside-")
    target = os.path.join(outside, "settings.json")
    with open(target, "w") as f:
        json.dump({"keep": 1}, f)
    cwd = repo({"package.json": AI_PKG})
    os.makedirs(os.path.join(cwd, ".claude"))
    os.symlink(target, os.path.join(cwd, ".claude", "settings.local.json"))
    run(cwd)
    assert json.load(open(target)) == {"keep": 1}

    cwd = repo({"package.json": AI_PKG})
    os.symlink(outside, os.path.join(cwd, ".claude"))
    os.remove(target)
    run(cwd)
    assert os.listdir(outside) == []


def test_symlinked_git_exclude_is_not_appended_to():
    outside = os.path.join(tempfile.mkdtemp(prefix="repo-profile-outside-"), "exclude")
    open(outside, "w").close()
    cwd = repo({"package.json": AI_PKG})
    ex = os.path.join(cwd, ".git", "info", "exclude")
    os.makedirs(os.path.dirname(ex), exist_ok=True)
    if os.path.exists(ex):
        os.remove(ex)
    os.symlink(outside, ex)
    run(cwd)
    assert open(outside).read() == ""


WORKPLACE_APPS = {"package.json": {"private": True},
                  "apps/timeOff/package.json": {"dependencies": {"react-native": "0.76"}},
                  "apps/roomBooking/package.json": {"dependencies": {"react-native": "0.76"}}}


def test_two_workplace_modules_enable_the_workplace_pack():
    cwd = repo(WORKPLACE_APPS)
    ctx = run(cwd)
    assert "Domain: workplace" in ctx and "/workplace-review" in ctx and "workplace@harness" in ctx, ctx
    assert local_settings(cwd)["enabledPlugins"] == {"mobile@harness": True, "workplace@harness": True}


def test_domain_marker_line_enables_the_workplace_pack():
    cwd = repo({"package.json": {"dependencies": {"express": "4"}},
                "docs/requirements.md": "# Req\n\nDomain: workplace\n"})
    assert "Domain: workplace" in run(cwd)
    assert local_settings(cwd)["enabledPlugins"]["workplace@harness"] is True


def test_backend_modules_one_level_down_count():
    cwd = repo({"package.json": {"private": True}, "apps/api/package.json": {"dependencies": {"hono": "4"}},
                "apps/api/src/api/meal-reservations/index.ts": "", "apps/api/src/api/meeting-rooms/index.ts": "",
                "apps/api/src/modules/lunch-plans/index.ts": ""})
    assert "Domain: workplace" in run(cwd)


def test_one_matching_module_is_not_a_domain():
    cwd = repo({"package.json": {"private": True}, "src/modules/booking/index.ts": "",
                "src/modules/users/index.ts": ""})
    assert "Domain:" not in run(cwd)
    assert local_settings(cwd) is None


def test_workplace_opt_out_is_respected_and_agent_still_enabled():
    files = {**WORKPLACE_APPS, "apps/chatbot/package.json": {"dependencies": {"@copilotkit/react-core": "1"}},
             ".claude/settings.json": {"enabledPlugins": {"workplace@harness": False}}}
    cwd = repo(files)
    ctx = run(cwd)
    assert "Domain: workplace" in ctx and "AI assistant" in ctx, ctx
    assert local_settings(cwd)["enabledPlugins"] == {"mobile@harness": True, "ai@harness": True}  # RN apps: mobile, not frontend


def test_ticket_folder_is_mentioned():
    cwd = repo({"package.json": {"dependencies": {"react": "19"}}, "docs/tickets/412/intent.md": ""})
    assert "/ticket" in run(cwd)


if __name__ == "__main__":
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    for t in tests:
        t()
    print(f"test_repo_profile: {len(tests)} passed")
