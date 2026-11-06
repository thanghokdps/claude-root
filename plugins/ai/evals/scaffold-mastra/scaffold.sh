#!/usr/bin/env bash
# Same offline pnpm and git identity as scaffold-langchain; this case's own warm/ adds the Mastra packages to the store.
exec bash "$(dirname "${BASH_SOURCE[0]}")/../scaffold-langchain/scaffold.sh"
