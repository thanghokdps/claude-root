# React v19 Rules

Universal rules for React v19 projects. Applies to both Client and Server Components.

---

## Component model

### Server Components vs Client Components

- **Default to Server Components** — only add `"use client"` when you need interactivity, browser APIs, or hooks
- `"use client"` is a boundary, not a per-component switch — it marks a subtree
- Never import a Client Component into a Server Component without a boundary — the bundler will error
- Keep `"use client"` components **small and at the leaves** of the tree

```tsx
// Good: Server Component fetches data, passes to small Client leaf
// app/posts/page.tsx (Server Component)
export default async function PostsPage() {
  const posts = await fetchPosts()
  return <PostList posts={posts} />       // Server Component
}

// components/PostList.tsx (Server Component — no interactivity needed)
// components/LikeButton.tsx — "use client" only this leaf
```

### When to add `"use client"`

| Reason | Example |
|--------|---------|
| Uses hooks (`useState`, `useEffect`, custom hooks) | Form with local state |
| Needs browser APIs (`window`, `localStorage`, `navigator`) | Geolocation feature |
| Uses event listeners (`onClick`, `onChange`) | Interactive controls |
| Uses context that holds mutable state | Theme switcher |

---

## React v19 new APIs

### `use()` hook — read resources in render

```tsx
import { use } from 'react'

// Read a Promise (replaces await in Server Components)
function Comments({ commentsPromise }: { commentsPromise: Promise<Comment[]> }) {
  const comments = use(commentsPromise)   // suspends until resolved
  return <ul>{comments.map(c => <li key={c.id}>{c.body}</li>)}</ul>
}

// Read Context (alternative to useContext — works inside conditionals)
function ThemedButton() {
  const theme = use(ThemeContext)
  return <button className={theme.button}>Click</button>
}
```

- `use()` can be called **conditionally** (unlike all other hooks)
- Wrap components using `use(Promise)` in `<Suspense>` — they will suspend
- Do NOT call `use()` on a new Promise created during render — that creates an infinite loop

### `useTransition()` — mark non-urgent state updates

```tsx
const [isPending, startTransition] = useTransition()

// v19: startTransition now accepts async functions
function handleSubmit() {
  startTransition(async () => {
    await savePost(data)        // async actions allowed in v19
    router.push('/posts')
  })
}
```

- Use `isPending` to show loading state without blocking the UI
- Wrap navigation, search filtering, and non-urgent data updates in `startTransition`
- Do NOT wrap user-typing input in `startTransition` — it would feel laggy

### `useOptimistic()` — optimistic UI updates

```tsx
const [optimisticPosts, addOptimisticPost] = useOptimistic(
  posts,
  (state, newPost: Post) => [...state, { ...newPost, pending: true }]
)

async function submitPost(formData: FormData) {
  const newPost = { id: crypto.randomUUID(), title: formData.get('title') as string }
  addOptimisticPost(newPost)          // instant UI update
  await createPost(newPost)           // actual server call
}
```

- Only use inside a `startTransition` or Server Action context
- The optimistic state automatically reverts to real state after the async operation settles
- Always add a visual indicator (`pending: true`) so the user knows the state is tentative

### `useFormStatus()` — read parent form's submission state

```tsx
"use client"
import { useFormStatus } from 'react-dom'

function SubmitButton() {
  const { pending } = useFormStatus()
  return <button disabled={pending}>{pending ? 'Saving…' : 'Save'}</button>
}

// The component MUST be rendered inside a <form> — not next to it
function PostForm() {
  return (
    <form action={createPost}>
      <input name="title" />
      <SubmitButton />        {/* ← inside form, can read useFormStatus */}
    </form>
  )
}
```

- `useFormStatus` reads the **nearest ancestor `<form>`** — it must be a child of the form
- Returns `{ pending, data, method, action }` — `pending` is the most commonly used field

### `useFormState()` / `useActionState()` — form + server action state

```tsx
"use client"
import { useActionState } from 'react'   // renamed from useFormState in React 19

async function createPost(prevState: State, formData: FormData): Promise<State> {
  const title = formData.get('title') as string
  if (!title) return { error: 'Title is required' }
  await db.posts.create({ title })
  return { success: true }
}

function PostForm() {
  const [state, action, isPending] = useActionState(createPost, { error: null })
  return (
    <form action={action}>
      <input name="title" />
      {state.error && <p role="alert">{state.error}</p>}
      <button disabled={isPending}>Save</button>
    </form>
  )
}
```

- v19 renames `useFormState` → `useActionState` and adds `isPending` as third return value
- The server action receives `(prevState, formData)` — previous state is always first
- Return the full state object from the action — never mutate `prevState`

### `ref` as a prop (v19 — no more `forwardRef`)

```tsx
// v19: ref is now a regular prop — no forwardRef needed
function Input({ ref, ...props }: React.ComponentProps<'input'>) {
  return <input ref={ref} {...props} />
}

// Usage
const inputRef = useRef<HTMLInputElement>(null)
<Input ref={inputRef} name="title" />
```

- `forwardRef` still works but is **deprecated** in v19 — remove it when touching components
- Use `React.ComponentProps<'input'>` to inherit all HTML element props including `ref`

---

## Component conventions

### Naming

- Component files: `PascalCase.tsx` — `UserCard.tsx`, `PostList.tsx`
- Non-component files: `camelCase.ts` — `fetchPosts.ts`, `useLocalStorage.ts`
- Custom hooks: always start with `use` — `useDebounce`, `useWindowSize`
- Event handlers: `handle` prefix — `handleSubmit`, `handleChange`, not `onSubmit`

### File structure per feature

```
features/posts/
  components/
    PostCard.tsx          ← leaf UI component ("use client" if interactive)
    PostList.tsx          ← container (Server Component)
  hooks/
    usePostSearch.ts      ← client-side hook
  actions/
    createPost.ts         ← Server Action ("use server")
  types.ts
  index.ts                ← public API only
```

### Props

- Destructure props in the function signature — never `props.foo` inside the body
- Provide explicit types — never rely on inferred prop types for exported components
- Boolean props: omitting = `false` (use `required` not `required={true}`)
- Event handler props: name them `on<Event>` — `onClose`, `onSelect`, not `handleClose`

```tsx
// Good
interface ButtonProps {
  label: string
  variant?: 'primary' | 'ghost'
  disabled?: boolean
  onClick: () => void
}

function Button({ label, variant = 'primary', disabled = false, onClick }: ButtonProps) {
  return (
    <button
      className={cn(styles.base, styles[variant])}
      disabled={disabled}
      onClick={onClick}
    >
      {label}
    </button>
  )
}
```

---

## Hooks rules

### Custom hooks

- Extract logic used in 2+ components into a custom hook
- Keep custom hooks **pure** — no side effects at the module level
- Return arrays for [value, setter] pairs; return objects for 3+ values

```tsx
// Good: returns object when > 2 values
function useAsync<T>(fn: () => Promise<T>) {
  const [data, setData] = useState<T | null>(null)
  const [error, setError] = useState<Error | null>(null)
  const [loading, setLoading] = useState(false)

  const run = useCallback(async () => {
    setLoading(true)
    try {
      setData(await fn())
    } catch (e) {
      setError(e instanceof Error ? e : new Error(String(e)))
    } finally {
      setLoading(false)
    }
  }, [fn])

  return { data, error, loading, run }
}
```

### `useEffect` discipline

- Every `useEffect` must have a **clear, single purpose** — one effect per concern
- Always include all reactive values in the dependency array — never suppress the lint rule
- If the effect only runs to sync external state, consider `useSyncExternalStore` instead
- Cleanup: always return a cleanup function for subscriptions, timers, and event listeners

```tsx
// Good: single concern, proper cleanup
useEffect(() => {
  const controller = new AbortController()
  fetchUser(id, { signal: controller.signal })
    .then(setUser)
    .catch(err => { if (!controller.signal.aborted) setError(err) })
  return () => controller.abort()
}, [id])

// Bad: multiple concerns, missing cleanup
useEffect(() => {
  fetchUser(id).then(setUser)    // no abort
  document.title = `User ${id}` // unrelated concern
}, [])                           // missing id dependency
```

---

## State management

- **Local state first** — `useState` for component-scoped state
- **URL state** — use search params for filterable/shareable state (`useSearchParams`)
- **Server state** — use Server Components + Server Actions instead of fetching on the client
- **Global client state** — Zustand or Jotai; avoid Context for frequently-changing values
- **Form state** — `useActionState` + Server Actions; avoid large form libraries for simple cases

### What NOT to put in state

- Derived values — compute from existing state during render, never store separately
- Refs to DOM elements — use `useRef`
- Values that don't trigger re-renders — use `useRef`

---

## Performance

### Memoization — only when measured

```tsx
// useMemo: only for expensive computations (sorting large lists, heavy transforms)
const sorted = useMemo(() => expensiveSort(items), [items])

// useCallback: only when passing callbacks to memoized children
const handleClick = useCallback(() => doSomething(id), [id])

// React.memo: only when profiler shows unnecessary re-renders
const PostCard = memo(function PostCard({ post }: { post: Post }) { ... })
```

**Rule:** Profile first, memoize second. Premature memoization adds complexity without benefit.

### Avoid common re-render causes

- Do NOT create objects/arrays inline in JSX (`style={{ color: 'red' }}` is fine; complex objects are not)
- Do NOT define components inside other components — every render creates a new type
- Prefer `key` on list items to be a stable unique ID, never array index for dynamic lists

---

## Accessibility

- Every `<img>` must have `alt` — empty string for decorative images
- Every form input must have a `<label>` or `aria-label`
- Interactive elements (`button`, `a`) must be keyboard-accessible — never use `<div onClick>`
- Use `role="alert"` for error messages that appear dynamically
- Modals must trap focus and close on Escape — use `<dialog>` element or a tested library

---

## What NOT to do

- `useEffect` with an empty dependency array to run on mount — use Server Components or `use()` instead
- Calling a hook conditionally (except `use()`) — React will error in development
- Mutating state directly — always produce a new object/array
- `React.FC` or `React.FunctionComponent` — just use function declarations
- Default exports for everything — use named exports for components (default for pages/routes)
- `dangerouslySetInnerHTML` without DOMPurify sanitization
- `key={Math.random()}` or `key={index}` for dynamic lists
- Nesting `<form>` inside `<form>` — HTML forbids it
