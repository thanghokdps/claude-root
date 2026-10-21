# Module Federation Rules — flash-mobile-app

Rules specific to the host + remote micro-frontend architecture.

## Shared singletons (never duplicate)

These packages are declared as `shared` singletons — only one instance runs across all apps:
- `react`, `react-native`
- `nativewind`
- `@tanstack/react-query`
- All `@repo/*` packages

**Rule**: never bundle these differently in remotes vs host. Never import two versions of the same singleton.

## Remote loading

- Each remote app must export a well-defined entry module (screen or component)
- The host loads remotes lazily — always wrap with `LazyLoadXxx` screen pattern (see `apps/host/src/screens/LazyLoadMaintenance/`)
- Every remote screen in the host must have a `FallbackLoadRemote` fallback

## Cross-app imports (forbidden)

- Remotes must NOT import from `apps/host/`
- Host imports from remotes only via Module Federation at runtime — not static imports
- Share code via `packages/*` only

## When a package/* changes

- Changes to shared packages affect ALL apps (host + all remotes)
- Must rebuild packages before testing: `pnpm build`
- Must run checks for all affected apps, not just the one you edited

## Dev federation setup

```bash
# Start host only (no Zephyr cloud)
NO_ZC=1 pnpm start:host

# Start a specific remote alongside host
NO_ZC=1 pnpm start:timeOff   # in a separate terminal
```

Without `NO_ZC=1`, the app tries to connect to Zephyr cloud for remote manifests.

## Adding a new remote app

1. Create `apps/<name>/` following existing remote app structure
2. Configure federation in `apps/<name>/rspack.config.js`
3. Add `LazyLoad<Name>Screen` in `apps/host/src/screens/`
4. Register in `apps/host/src/navigation/Navigation.tsx`
5. Add to root `package.json` scripts
6. Add to `pnpm-workspace.yaml`
