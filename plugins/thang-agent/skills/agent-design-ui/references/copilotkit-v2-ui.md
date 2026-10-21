# CopilotKit v2 chat UI — tokens and slots

From docs.copilotkit.ai (`custom-look-and-feel/css`, `/slots`, read 2026-10). Before relying on a name, check it in the installed package: the full token set is in `@copilotkit/react-core/v2/styles.css`; slots are props of the exported components.

## Theme tokens (L0)

v2 components are Tailwind + shadcn based. Tokens are CSS custom properties on the `[data-copilotkit]` root, as `oklch()` values. The `--copilot-kit-*` variables belong to v1 (`@copilotkit/react-ui`) and do nothing here.

| Group | Tokens |
|-------|--------|
| Surfaces, text | `--background` `--foreground` · `--card` `--card-foreground` · `--popover` `--popover-foreground` · `--secondary` · `--muted` · `--accent` (each with `-foreground`) |
| Actions, feedback | `--primary` `--primary-foreground` · `--destructive` `--destructive-foreground` · `--ring` |
| Borders | `--border` · `--input` |
| Sidebar | `--sidebar-*` |
| Corners | `--radius` (`--radius-sm/md/lg/xl` derive from it) |

```css
/* scoped: a wrapper class keeps overrides out of the rest of the app */
.assistant-chat [data-copilotkit] {
  --primary: oklch(0.55 0.2 264);
  --radius: 0.75rem;
}
.dark .assistant-chat [data-copilotkit] { --background: oklch(0.16 0 0); }   /* only if the design has dark */
```

Hex → oklch: convert with a tool (`culori`, or `oklch.com`), never by eye.

## Slots (L1, L2)

Import from `@copilotkit/react-core/v2`. Each slot takes one of: a **class string** (merged with the defaults), a **props object** (override `className`, handlers, data attributes), or **your component** (receives the default's props). Slots nest.

| Component | Slots |
|-----------|-------|
| `CopilotChat`, `CopilotSidebar`, `CopilotPopup` | `messageView` · `scrollView` · `input` · `suggestionView` · `welcomeScreen` |
| `CopilotSidebar`, `CopilotPopup` only | `header` (`titleContent`, `closeButton`) · `toggleButton` (`openIcon`, `closeIcon`) |
| `messageView` | `assistantMessage` · `userMessage` · `reasoningMessage` · `cursor` |
| `assistantMessage` | `markdownRenderer` · `toolbar` · `copyButton` · `thumbsUpButton` · `thumbsDownButton` · `readAloudButton` · `regenerateButton` · `toolCallsView` |
| `userMessage` | `messageRenderer` · `toolbar` · `copyButton` · `editButton` · `branchNavigation` |
| `reasoningMessage` | `header` · `contentView` · `toggle` |
| `input` | `textArea` · `sendButton` · `addMenuButton` · `startTranscribeButton` · `cancelTranscribeButton` · `finishTranscribeButton` · `audioRecorder` · `disclaimer` |
| `scrollView` | `feather` · `scrollToBottomButton` |
| `suggestionView` | `suggestion` · `container` |
| `welcomeScreen` | `welcomeMessage` |

```tsx
<div className="assistant-chat">
  <CopilotChat
    messageView={{ assistantMessage: AssistantBubble, userMessage: "rounded-2xl bg-primary text-primary-foreground" }}
    input="rounded-xl border-2"
  />
</div>
```

A `children` render function on the chat components exposes `messageView`, `input`, `scrollView` and `suggestionView` as built elements — rearrange them before reaching for headless (L3).

## Headless (L3)

`useAgent` with your own message list and input, for layouts no slot arrangement reaches. Tool UI still goes through `useRenderTool`; nothing about auth or the confirm contract changes.
