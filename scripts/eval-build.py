#!/usr/bin/env python3
"""eval-build.py <plugin> — copy plugins/<plugin>/evals/ to plugins/<plugin>/evals-build/ and give every case the
`plugins:` list `claude plugin eval` needs: the plugin and its dependency closure from plugin.json. Cases never list
it by hand, so a new dependency touches no case. Run by scripts/eval-plugin.sh."""
import importlib.util
import json
import os
import shutil
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location("lint_kit", os.path.join(HERE, "lint-kit.py"))
lint_kit = importlib.util.module_from_spec(spec)
spec.loader.exec_module(lint_kit)


def dependency_graph():
    graph = {}
    for plugin in lint_kit.plugin_names():
        path = os.path.join(lint_kit.PLUGINS_DIR, plugin, ".claude-plugin", "plugin.json")
        graph[plugin] = json.load(open(path, encoding="utf-8")).get("dependencies", [])
    return graph


def case_plugins(plugin, graph):
    """Paths relative to a case dir (plugins/<plugin>/evals-build/<case>/)."""
    return ["../.."] + [f"../../../{dep}" for dep in sorted(lint_kit.closure(graph, plugin))]


def with_plugins(prompt, plugins):
    if not prompt.startswith("---\n"):
        raise ValueError("prompt.md has no frontmatter")
    return f"---\nplugins: {json.dumps(plugins)}\n" + prompt[4:]


def build(plugin):
    src = os.path.join(lint_kit.PLUGINS_DIR, plugin, "evals")
    out = os.path.join(lint_kit.PLUGINS_DIR, plugin, "evals-build")  # --eval-dir rejects a leading dot
    shutil.rmtree(out, ignore_errors=True)
    shutil.copytree(src, out, ignore=shutil.ignore_patterns("results"))
    plugins = case_plugins(plugin, dependency_graph())
    for case in os.listdir(out):
        prompt = os.path.join(out, case, "prompt.md")
        if os.path.isfile(prompt):
            text = open(prompt, encoding="utf-8").read()
            open(prompt, "w", encoding="utf-8").write(with_plugins(text, plugins))
    return out


if __name__ == "__main__":
    print(build(sys.argv[1]))
