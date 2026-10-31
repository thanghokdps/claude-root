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


def shared_settings(cwd):
    p = os.path.join(cwd, ".claude", "settings.json")
    return json.load(open(p)) if os.path.exists(p) else None


def shared_packs(cwd):
    """Packs the hook put in the team file, without the dev@harness every set-up repo gets."""
    return {k.split("@")[0] for k in (shared_settings(cwd) or {}).get("enabledPlugins", {})} - {"dev"}


KIT_MARKETPLACE = {"source": {"source": "github", "repo": "thanghokdps/claude-root"}}


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
    assert "settings" not in out["additionalContext"]
    assert local_settings(cwd) is None and shared_settings(cwd) is None


def test_ai_web_repo_gets_the_kit_in_its_team_settings():
    cwd = repo({"package.json": AI_PKG, "prisma/schema.prisma": "", ".claude/docs/index.md": "# x"})
    ctx = run(cwd, config_dir({"ai@harness": False}))
    for want in ["Next.js", "AI assistant", "Prisma", "Roles: frontend, backend, ai", "/feature", "/agent-tool",
                 "/db-change", ".claude/docs/index.md", "/docs-sync", "ai@harness", ".claude/settings.json",
                 "uncommitted", "/reload-plugins"]:
        assert want in ctx, (want, ctx)
    s = shared_settings(cwd)
    assert s["extraKnownMarketplaces"] == {"harness": KIT_MARKETPLACE}, s
    assert s["enabledPlugins"] == {"dev@harness": True, "frontend@harness": True, "backend@harness": True,
                                   "ai@harness": True}, s
    assert local_settings(cwd) is None


def test_existing_team_settings_are_merged_not_replaced():
    cwd = repo({"package.json": AI_PKG, ".claude/settings.json": {
        "permissions": {"allow": ["Bash(ls)"]}, "enabledPlugins": {"other@team": True},
        "extraKnownMarketplaces": {"team": {"source": {"source": "github", "repo": "acme/kit"}}}}})
    run(cwd)
    s = shared_settings(cwd)
    assert s["permissions"] == {"allow": ["Bash(ls)"]}
    assert s["enabledPlugins"]["other@team"] is True and s["enabledPlugins"]["ai@harness"] is True
    assert set(s["extraKnownMarketplaces"]) == {"team", "harness"}


def test_second_session_writes_nothing():
    cwd = repo({"package.json": AI_PKG})
    run(cwd)
    before = open(os.path.join(cwd, ".claude", "settings.json")).read()
    ctx = run(cwd)
    assert open(os.path.join(cwd, ".claude", "settings.json")).read() == before
    assert "Wrote" not in ctx, ctx


def test_written_source_is_never_this_machines_alias():
    cfg = config_dir()
    os.makedirs(os.path.join(cfg, "plugins"))
    with open(os.path.join(cfg, "plugins", "known_marketplaces.json"), "w") as f:
        json.dump({"harness": {"source": {"source": "git", "url": "git@github-me:me/kit.git"}}}, f)
    cwd = repo({"package.json": AI_PKG})
    run(cwd, cfg)
    assert shared_settings(cwd)["extraKnownMarketplaces"]["harness"] == KIT_MARKETPLACE


def test_odd_team_settings_are_left_alone():
    for content in ("{not json", "[1, 2]", {"enabledPlugins": ["x"]}, {"extraKnownMarketplaces": "x"}):
        cwd = repo({"package.json": {"dependencies": {"express": "4"}}, ".claude/settings.json": content})
        before = open(os.path.join(cwd, ".claude", "settings.json")).read()
        run(cwd)
        assert open(os.path.join(cwd, ".claude", "settings.json")).read() == before, content
        assert local_settings(cwd)["enabledPlugins"] == {"backend@harness": True}, content


def test_home_folder_and_non_git_folder_get_no_team_settings():
    cwd = repo({"package.json": AI_PKG})
    run(cwd, env={"HOME": cwd})
    assert shared_settings(cwd) is None
    plain = tempfile.mkdtemp(prefix="repo-profile-nogit-")
    with open(os.path.join(plain, "package.json"), "w") as f:
        json.dump(AI_PKG, f)
    run(plain)
    assert shared_settings(plain) is None


def test_the_kit_repo_itself_gets_no_team_settings():
    cwd = repo({".claude-plugin/marketplace.json": {"name": "harness", "plugins": []}})
    run(cwd)
    assert shared_settings(cwd) is None
    assert not os.path.exists(os.path.join(cwd, ".claude", "rules"))


def test_plain_backend_repo_without_docs():
    cwd = repo({"package.json": {"dependencies": {"express": "4"}}})
    ctx = run(cwd)
    assert "Express" in ctx and "/api-endpoint" in ctx and "/project-init" in ctx, ctx
    assert "AI assistant" not in ctx and "Roles: backend." in ctx, ctx
    assert shared_settings(cwd)["enabledPlugins"] == {"dev@harness": True, "backend@harness": True}


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
        assert shared_packs(cwd) == want, (files, shared_packs(cwd))


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


def test_explicit_opt_out_keeps_the_repo_out_of_team_settings():
    cwd = repo({"package.json": AI_PKG, ".claude/settings.json": {"enabledPlugins": {"ai@harness": False}}})
    ctx = run(cwd)
    assert "AI assistant" in ctx
    assert shared_settings(cwd) == {"enabledPlugins": {"ai@harness": False}}
    assert local_settings(cwd)["enabledPlugins"] == {"frontend@harness": True, "backend@harness": True}
    assert ".claude/settings.local.json" in open(os.path.join(cwd, ".git", "info", "exclude")).read()


def test_a_false_in_local_settings_also_opts_out():
    cwd = repo({"package.json": {"dependencies": {"express": "4"}},
                ".claude/settings.local.json": {"enabledPlugins": {"harness@harness": False}}})
    run(cwd)
    assert shared_settings(cwd) is None
    assert local_settings(cwd)["enabledPlugins"]["backend@harness"] is True


def test_legacy_agent_pack_is_renamed_to_ai():
    cwd = repo({"package.json": AI_PKG, ".claude/settings.local.json": {"enabledPlugins": {"agent@harness": True}}})
    run(cwd, config_dir({"frontend@harness": True, "backend@harness": True}))
    assert local_settings(cwd)["enabledPlugins"] == {"ai@harness": True}


def test_user_scope_packs_still_reach_the_team_file():
    cwd = repo({"package.json": AI_PKG})
    ctx = run(cwd, config_dir({"ai@harness": True, "frontend@harness": True, "backend@harness": True}))
    assert "AI assistant" in ctx and "settings.local.json" not in ctx
    assert local_settings(cwd) is None
    assert shared_packs(cwd) == {"frontend", "backend", "ai"}


def test_malformed_local_settings_is_left_alone():
    cwd = repo({"package.json": AI_PKG, ".claude/settings.local.json": "{not json"})
    run(cwd)
    assert open(os.path.join(cwd, ".claude", "settings.local.json")).read() == "{not json"


def test_new_repo_gets_the_kit_and_names_the_packs_that_are_off():
    cwd = repo()
    ctx = run(cwd, config_dir({"frontend@harness": True}))
    assert "no manifest" in ctx and "ai@harness" in ctx and "/reload-plugins" in ctx, ctx
    assert "claude plugin enable <pack> --scope project" in ctx and "frontend@harness," not in ctx, ctx
    assert "enabledPlugins in .claude/settings.json" not in ctx, ctx  # a guarded path: the model must not edit it
    s = shared_settings(cwd)
    assert s == {"extraKnownMarketplaces": {"harness": KIT_MARKETPLACE}, "enabledPlugins": {"dev@harness": True}}, s
    assert local_settings(cwd) is None
    assert "/agent-architect" not in ctx, ctx


def test_new_repo_with_ai_on_routes_a_chatbot_init_to_agent_architect():
    ctx = run(repo(), config_dir({"ai@harness": True}))
    assert "ai@harness is on" in ctx and "/agent-architect first" in ctx, ctx
    assert "ai@harness for LangChain" not in ctx, ctx


def test_new_repo_with_ai_on_routes_layer_requests_to_their_skill():
    ctx = run(repo(), config_dir({"ai@harness": True}))
    for skill in ("/agent-feature", "/agent-hitl", "/agent-rag", "/agent-tool", "/agent-graph"):
        assert skill in ctx, (skill, ctx)
    assert "even with no code yet" in ctx, ctx


def test_new_opted_out_repo_enables_packs_locally():
    cwd = repo({".claude/settings.local.json": {"enabledPlugins": {"ai@harness": False}}})
    ctx = run(cwd)
    assert "claude plugin enable <pack> --scope local" in ctx, ctx
    assert shared_settings(cwd) is None


RULES = os.path.join(ROOT, "plugins", "core", "rules")
CORE_RULES = sorted(f for f in os.listdir(RULES) if f.endswith(".md"))


def repo_rules(cwd):
    p = os.path.join(cwd, ".claude", "rules")
    return sorted(os.listdir(p)) if os.path.isdir(p) else []


def test_set_up_repo_gets_the_core_rules():
    cwd = repo({"package.json": AI_PKG})
    ctx = run(cwd)
    assert repo_rules(cwd) == CORE_RULES, repo_rules(cwd)
    assert open(os.path.join(cwd, ".claude", "rules", "git.md")).read() == open(os.path.join(RULES, "git.md")).read()
    assert ".claude/rules" in ctx and "uncommitted" in ctx, ctx
    assert "stacks" not in repo_rules(cwd)


def test_new_repo_gets_the_core_rules_too():
    cwd = repo()
    assert ".claude/rules" in run(cwd)
    assert repo_rules(cwd) == CORE_RULES


def test_a_team_rule_with_the_same_name_is_kept():
    cwd = repo({"package.json": AI_PKG, ".claude/rules/git.md": "# team git rule\n"})
    run(cwd)
    assert open(os.path.join(cwd, ".claude", "rules", "git.md")).read() == "# team git rule\n"
    assert repo_rules(cwd) == CORE_RULES


def test_rules_the_user_config_already_loads_are_not_copied():
    cfg = config_dir()
    os.makedirs(os.path.join(cfg, "rules"))
    for name in CORE_RULES:
        open(os.path.join(cfg, "rules", name), "w").close()
    cwd = repo({"package.json": AI_PKG})
    ctx = run(cwd, cfg)
    assert repo_rules(cwd) == [] and ".claude/rules" not in ctx, ctx


def test_opted_out_repo_gets_no_rules():
    cwd = repo({"package.json": AI_PKG, ".claude/settings.json": {"enabledPlugins": {"ai@harness": False}}})
    run(cwd)
    assert repo_rules(cwd) == []


def test_second_session_copies_no_rules():
    cwd = repo({"package.json": AI_PKG})
    run(cwd)
    os.remove(os.path.join(cwd, ".claude", "rules", "testing.md"))
    ctx = run(cwd)
    assert "testing.md" in repo_rules(cwd) and "1 core rule" in ctx, ctx
    assert "Wrote" not in run(cwd)


def test_symlinked_rules_folder_is_never_written_through():
    outside = tempfile.mkdtemp(prefix="repo-profile-outside-")
    cwd = repo({"package.json": AI_PKG})
    os.makedirs(os.path.join(cwd, ".claude"))
    os.symlink(outside, os.path.join(cwd, ".claude", "rules"))
    run(cwd)
    assert os.listdir(outside) == []


def test_off_switch_prints_nothing():
    assert run(repo(), env={"CLAUDE_REPO_PROFILE": "0"}) == ""
    cwd = repo({"package.json": AI_PKG})
    assert run(cwd, env={"CLAUDE_REPO_PROFILE": "0"}) == ""
    assert local_settings(cwd) is None and shared_settings(cwd) is None


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
    os.makedirs(os.path.join(cwd, ".claude"))
    os.symlink(target, os.path.join(cwd, ".claude", "settings.json"))
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
    assert shared_packs(cwd) == {"mobile", "workplace"}


def test_domain_marker_line_enables_the_workplace_pack():
    cwd = repo({"package.json": {"dependencies": {"express": "4"}},
                "docs/requirements.md": "# Req\n\nDomain: workplace\n"})
    assert "Domain: workplace" in run(cwd)
    assert "workplace" in shared_packs(cwd)


def test_backend_modules_one_level_down_count():
    cwd = repo({"package.json": {"private": True}, "apps/api/package.json": {"dependencies": {"hono": "4"}},
                "apps/api/src/api/meal-reservations/index.ts": "", "apps/api/src/api/meeting-rooms/index.ts": "",
                "apps/api/src/modules/lunch-plans/index.ts": ""})
    assert "Domain: workplace" in run(cwd)


def test_one_matching_module_is_not_a_domain():
    cwd = repo({"package.json": {"private": True}, "src/modules/booking/index.ts": "",
                "src/modules/users/index.ts": ""})
    assert "Domain:" not in run(cwd)
    assert shared_packs(cwd) == set() and local_settings(cwd) is None


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
