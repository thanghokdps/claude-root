---
paths:
  - "apps/*/src/screens/**/*.tsx"
---

# Screen Conventions

## Named export, typed navigation props

```tsx
import { SCREENS } from '@repo/constants/screens';
import type { AppStackScreenProps } from '@/types/navigation';

type MyScreenProps = AppStackScreenProps<typeof SCREENS.MY_SCREEN>;

export const MyScreen = ({ navigation, route }: MyScreenProps) => {
```

Never use `default export` for screens.

## Data loading pattern

```tsx
const { data, isLoading, isError } = useGetData();

if (isError) return <Text>Something went wrong</Text>;
if (isLoading) return <LoadingSlider />;

return <View>{/* render data */}</View>;
```

## Submission pattern (mutations)

```tsx
const { mutate, isPending: isSubmitting } = useCreateRequest(
  () => {
    Toast.show({ type: 'success', text1: 'Created successfully' });
    navigation.navigate(SCREENS.HOME);
  },
  (error: unknown) => {
    const apiMessage = getErrorMessage(error);
    Toast.show({ type: 'error', text1: 'Failed', ...(apiMessage && { text2: apiMessage }) });
  },
);

useBlockBackNavigation(isSubmitting, { navigation });
```

## Focus-dependent cleanup

```tsx
useFocusEffect(
  useCallback(() => {
    return () => {
      // cleanup on screen blur (close modals, reset state)
    };
  }, []),
);
```

## Module Federation screens (LazyLoad pattern)

```tsx
const RemoteModule = React.lazy(
  () => import('moduleName/ComponentName'), // @ts-ignore above if needed
);

return (
  <ErrorBoundary FallbackComponent={FallbackError} onError={e => sentryService.captureException(e)}>
    <React.Suspense fallback={<FallbackLoadRemote />}>
      <RemoteModule {...props} />
    </React.Suspense>
  </ErrorBoundary>
);
```

## Styles

Use `StyleSheet.create` at the bottom of the file for screen-level layout. Theme-dependent styles go in `makeStyles`.

```tsx
const styles = StyleSheet.create({
  container: { flex: 1 },
});
```
