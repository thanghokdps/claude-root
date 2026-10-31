#!/usr/bin/env bash
# Seeds a minimal Next.js App Router skeleton with components/ui primitives and a CSS-variable token file.
set -euo pipefail
git init -q -b main
git config user.email eval@example.com && git config user.name eval
mkdir -p app components/ui
cat > package.json <<'J'
{ "name": "shop-web", "private": true, "scripts": { "dev": "next dev", "test": "vitest run" },
  "dependencies": { "next": "15.0.0", "react": "19.0.0", "react-dom": "19.0.0" } }
J
cat > app/globals.css <<'J'
:root {
  --color-bg: #0b0d12;
  --color-surface: #151922;
  --color-text: #e8eaf0;
  --color-primary: #4f7cff;
  --color-danger: #ff5c5c;
  --radius-md: 8px;
  --space-2: 8px;
  --space-4: 16px;
}
body { background: var(--color-bg); color: var(--color-text); }
J
cat > app/layout.tsx <<'J'
import "./globals.css";
export default function RootLayout({ children }: { children: React.ReactNode }) {
  return <html lang="en"><body>{children}</body></html>;
}
J
cat > app/page.tsx <<'J'
export default function Home() { return <main>Home</main>; }
J
cat > components/ui/button.tsx <<'J'
import type { ButtonHTMLAttributes } from "react";
export function Button(props: ButtonHTMLAttributes<HTMLButtonElement>) {
  return <button {...props} style={{ background: "var(--color-primary)", borderRadius: "var(--radius-md)", padding: "var(--space-2) var(--space-4)" }} />;
}
J
cat > components/ui/input.tsx <<'J'
import type { InputHTMLAttributes } from "react";
export function Input(props: InputHTMLAttributes<HTMLInputElement>) {
  return <input {...props} style={{ background: "var(--color-surface)", borderRadius: "var(--radius-md)", padding: "var(--space-2)" }} />;
}
J
git add -A && git commit -qm "init: next app skeleton"
