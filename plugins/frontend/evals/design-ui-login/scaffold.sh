#!/usr/bin/env bash
# Seeds a Next.js skeleton plus a design folder (login.png 360x640 + login.md) to match.
set -euo pipefail
git init -q -b main
git config user.email eval@example.com && git config user.name eval
mkdir -p app components/ui design
cat > package.json <<'J'
{ "name": "shop-web", "private": true, "scripts": { "dev": "next dev" },
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
  --space-6: 24px;
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
cat > design/login.md <<'J'
# Login frame (design/login.png, 360x640)

- Centered card, 320px wide, background #151922, radius 12px, padding 24px.
- Title "Sign in" 24px/700, colour #e8eaf0, 16px below to the fields.
- Fields: Email, Password. Height 44px, gap 16px, radius 8px, background #0b0d12, border 1px #2a3142.
- Primary button "Sign in", full width, 44px high, background #5b8cff, radius 8px.
- Link "Forgot password?" 14px, colour #7da2ff, 12px below the button.
- Frame shown: default only. No error, loading or disabled frame was drawn.
J
python3 -I - <<'P'
# The frame as blocks: an 8x8 placeholder made runs stop and ask for the real mockup.
import zlib, struct
def chunk(t, d):
    c = struct.pack(">I", len(d)) + t + d
    return c + struct.pack(">I", zlib.crc32(t + d) & 0xffffffff)
W, H = 360, 640
blocks = [  # x0, y0, x1, y1, colour; later blocks paint over earlier ones
    (20, 150, 340, 420, b"\x15\x19\x22"),  # card
    (44, 174, 140, 198, b"\xe8\xea\xf0"),  # title
    (44, 214, 316, 258, b"\x0b\x0d\x12"),  # email
    (44, 274, 316, 318, b"\x0b\x0d\x12"),  # password
    (44, 334, 316, 378, b"\x5b\x8c\xff"),  # button
    (130, 390, 230, 404, b"\x7d\xa2\xff"),  # link
]
def row(y):
    pixels = bytearray(b"\x0b\x0d\x12" * W)
    for x0, y0, x1, y1, colour in blocks:
        if y0 <= y < y1:
            pixels[x0 * 3:x1 * 3] = colour * (x1 - x0)
    return b"\x00" + bytes(pixels)
raw = b"".join(row(y) for y in range(H))
png = b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", W, H, 8, 2, 0, 0, 0)) + chunk(b"IDAT", zlib.compress(raw)) + chunk(b"IEND", b"")
open("design/login.png", "wb").write(png)
P
git add -A && git commit -qm "init: next app skeleton with login design"
