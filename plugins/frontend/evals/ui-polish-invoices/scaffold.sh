#!/usr/bin/env bash
# Seeds a Vite + React page that works but drifts: raw hex, one-off spacing, two competing primary buttons.
set -euo pipefail
git init -q -b main
git config user.email eval@example.com && git config user.name eval
mkdir -p src/pages src/components/ui src/styles
cat > package.json <<'J'
{ "name": "billing", "private": true, "dependencies": { "react": "19.0.0", "react-dom": "19.0.0", "vite": "6.0.0" } }
J
cat > src/styles/tokens.css <<'C'
:root { --color-fg: #18181b; --color-bg: #ffffff; --color-primary: #1d4ed8; --space-2: 8px; --space-4: 16px; }
C
cat > src/components/ui/button.tsx <<'T'
export function Button(props: React.ButtonHTMLAttributes<HTMLButtonElement>) {
  return <button {...props} style={{ background: "var(--color-primary)", color: "#fff", padding: "var(--space-2)" }} />;
}
T
cat > src/pages/Invoices.tsx <<'T'
import { Button } from "../components/ui/button";

const invoices = [{ id: "INV-1", total: "1,200.00" }];

export function Invoices({ onExport, onCreate }: { onExport: () => void; onCreate: () => void }) {
  return (
    <div style={{ padding: 13 }}>
      <div style={{ fontSize: 15, color: "#aaaaaa" }}>INVOICES</div>
      <Button onClick={onExport}>Submit</Button>
      <Button onClick={onCreate}>Process</Button>
      {invoices.map((i) => (
        <div key={i.id} style={{ boxShadow: "0 4px 20px #0003", borderRadius: 24, padding: 27, color: "#bbbbbb" }}>
          {i.id} {i.total}
        </div>
      ))}
      {invoices.length === 0 && <div>No data</div>}
    </div>
  );
}
T
git add -A && git commit -qm "init: invoices page"
