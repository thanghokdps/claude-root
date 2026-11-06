#!/usr/bin/env bash
# Same offline pnpm and git identity as scaffold-langchain, whose warm/ already holds shape B's packages.
exec bash "$(dirname "${BASH_SOURCE[0]}")/../scaffold-langchain/scaffold.sh"
