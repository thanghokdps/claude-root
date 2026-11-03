#!/usr/bin/env bash
# Seeds the multi-tenant Mastra support assistant (tenantId in requestContext), with no documents or vector store yet.
# Without an agent, agent-rag stops at its precondition (correctly) and never reaches the tenant filter.
set -euo pipefail
cp -R "$(dirname "${BASH_SOURCE[0]}")/../graph-workflow/repo/." .
