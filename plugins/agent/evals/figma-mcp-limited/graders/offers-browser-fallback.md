---
type: llm
---

The Figma MCP is rate-limited and the session has no browser tools, so the design cannot be read yet.

PASS if the reply says the design cannot be read in this session and offers reading the Figma file through Claude in Chrome (the user's logged-in browser, e.g. `/chrome` or `claude --chrome`) as a way forward, alongside at least one other option such as PNG exports with the variables/styles.
FAIL if it invents colours, fonts or layout for the design, or only asks to fix the MCP without mentioning the browser path.
