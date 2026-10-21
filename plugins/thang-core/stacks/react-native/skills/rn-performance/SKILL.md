---
name: rn-performance
description: React Native performance patterns and common perf issues for flash-mobile-app. Use when dealing with slow lists, janky animations, or re-render issues. Trigger phrases: "slow", "laggy", "performance", "re-render", "FlatList", "animation jank".
model: sonnet
effort: high
when_to_use: diagnosing performance issues, optimizing lists, fixing animation jank, reducing re-renders
---

# RN Performance Reference — flash-mobile-app

Diagnose → measure → fix. Never optimize without profiling first.

---

## Lists (most common perf issue)

**Use FlashList, not FlatList, for long lists:**

```typescript
import { FlashList } from '@shopify/flash-list';

<FlashList
  data={items}
  renderItem={({ item }) => <ItemCard item={item} />}
  estimatedItemSize={80}          // REQUIRED — measure your item height
  keyExtractor={item => item.id}
/>
```

**FlatList optimization (if you must use it):**
```typescript
<FlatList
  data={items}
  renderItem={renderItem}
  keyExtractor={item => item.id}
  getItemLayout={(_, index) => ({ length: ITEM_HEIGHT, offset: ITEM_HEIGHT * index, index })}
  removeClippedSubviews={true}
  maxToRenderPerBatch={10}
  windowSize={5}
/>
```

---

## Preventing unnecessary re-renders

```typescript
// Memoize expensive child components
const ItemCard = React.memo(({ item }: { item: FooItem }) => {
  // ...
});

// Stable callbacks with useCallback
const handlePress = useCallback((id: string) => {
  navigation.navigate(SCREENS.DETAIL, { id });
}, [navigation]);

// Stable references with useMemo
const sortedItems = useMemo(
  () => [...items].sort((a, b) => a.name.localeCompare(b.name)),
  [items]
);
```

**Rule**: Only memoize when you've confirmed a re-render problem via React DevTools Profiler. Premature memoization adds complexity for no gain.

---

## Animations (use Reanimated worklets)

```typescript
import Animated, { useSharedValue, useAnimatedStyle, withSpring } from 'react-native-reanimated';

// All animation logic on the UI thread (worklet)
const offset = useSharedValue(0);

const animatedStyle = useAnimatedStyle(() => ({
  transform: [{ translateX: offset.value }],
}));

// Run on UI thread — not JS thread
offset.value = withSpring(100);
```

Never use `Animated` from React Native for complex animations — use `react-native-reanimated`.

---

## Identifying the problem

1. **Open React Native DevTools** → Profiler tab
2. **Record** while reproducing the issue
3. **Look for**: components with gray bars (re-rendered), high render durations
4. **Check JS thread vs UI thread**: JS thread spikes = JS-side problem; UI thread spikes = native/animation issue

---

## ⚠ Gotchas

- **FlashList `estimatedItemSize`**: if wrong → layout thrash. Measure real item height.
- **Anonymous functions in JSX props**: `onPress={() => fn(item)}` creates new ref every render → use `useCallback`
- **Context re-renders**: if `AuthContext` or `ChatContext` value changes → all consumers re-render → memoize context value
- **Module Federation**: shared libraries like React are singletons — re-render issues can sometimes cross remote boundaries
- **Image loading**: always use `resizeMode` and specify `width`/`height` — auto-sizing causes layout recalculations
