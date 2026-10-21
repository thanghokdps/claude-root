# Next.js rules

## App Router conventions

- Route handlers in `app/api/<path>/route.ts` — export named HTTP methods (`GET`, `POST`, etc.)
- Server Components by default — add `"use client"` only when needed (event handlers, hooks, browser APIs)
- Never mix server and client state in the same component

## Data fetching

- Fetch in Server Components → pass as props to Client Components
- Never `useEffect` + `fetch` when a Server Component can fetch directly
- Use `next/cache` `revalidatePath` / `revalidateTag` for ISR — never manual cache busting hacks

## Environment variables

- Server-only vars: no `NEXT_PUBLIC_` prefix — never expose to client
- Client vars: `NEXT_PUBLIC_` prefix required
- Access in Server Components: `process.env.VAR`
- Access in Client Components: `process.env.NEXT_PUBLIC_VAR` only

## Image and font

- Always use `next/image` for images — never `<img>` tag
- Always use `next/font` for fonts — never `<link>` to Google Fonts

## API route size limits

Tool/API results must stay under 2k chars. Truncate list results to max 10 records before returning.

## TypeScript strict

- All route handlers fully typed: `NextRequest`, `NextResponse`
- Validate all user input at API boundaries with Zod before using

## No useChat from Vercel AI SDK

If this project uses CopilotKit / AG-UI:
```typescript
// FORBIDDEN
import { useChat } from "@ai-sdk/react";
// CORRECT
import { useCoAgent } from "@copilotkit/react-core";
```
