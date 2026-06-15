---
name: module-federation
description: Module Federation micro-frontend patterns — React.lazy, Suspense, ErrorBoundary, LazyLoad screen convention
paths:
  - "apps/*/src/screens/LazyLoad*/**/*.tsx"
  - "apps/*/src/screens/**/*.tsx"
---

# Module Federation Patterns

## LazyLoad screen convention

Each micro-frontend app (reallocation, mealReservation, roomBooking, timeOff, maintenance) is loaded lazily from the host app via a `LazyLoad<AppName>Screen` wrapper:

```tsx
// apps/host/src/screens/LazyLoadRoomBooking/index.tsx

const RoomBookingRemote = React.lazy(
  // @ts-ignore — module federation types not generated
  () => import('roomBooking/RoomBooking'),
);

export const LazyLoadRoomBookingScreen = ({ navigation }: LazyLoadRoomBookingScreenProps) => {
  // 1. Fetch all data needed by the remote module
  const { data, isLoading, isError } = useGetData();

  if (isError) return <Text>Something went wrong</Text>;

  return (
    <View style={styles.container}>
      {isLoading ? (
        <LoadingSlider />
      ) : (
        <ErrorBoundary
          FallbackComponent={FallbackError}
          onError={error => sentryService.captureException(error)}
        >
          <React.Suspense fallback={<FallbackLoadRemote />}>
            <RoomBookingRemote
              // Pass all required props from host
              data={data}
              onBack={() => navigation.goBack()}
              onSubmit={handleSubmit}
            />
          </React.Suspense>
        </ErrorBoundary>
      )}
    </View>
  );
};
```

## Required imports for LazyLoad screens

```tsx
import React, { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import ErrorBoundary from 'react-native-error-boundary';
import Toast from 'react-native-toast-message';
import { StyleSheet, View } from 'react-native';

import { FallbackError } from '@/components/FallbackError';
import { FallbackLoadRemote } from '@/components/FallbackLoadRemote';
import { LoadingSlider } from '@/components/LoadingSlider';
import { sentryService } from '@/services/sentryService';
```

## Screen navigation type

```tsx
import { SCREENS } from '@repo/constants/screens';
import type { AppStackScreenProps } from '@/types/navigation';

type LazyLoadMyScreenProps = AppStackScreenProps<typeof SCREENS.MY_SCREEN>;

export const LazyLoadMyScreen = ({ navigation }: LazyLoadMyScreenProps) => {
```

## WebSocket real-time updates

When the remote module needs real-time data:

```tsx
const { lastMessage } = useWebSocketListener();

useEffect(() => {
  if (!lastMessage) return;
  if (lastMessage.type !== WsType.BROADCAST) return;
  if (lastMessage.channel !== WsChanel.ROOM_BOOKING) return;

  // Process message and update local state
}, [lastMessage]);
```

## Close modals on screen blur

```tsx
const closeModalsRef = useRef<(() => void) | null>(null);

useFocusEffect(
  useCallback(() => {
    return () => closeModalsRef.current?.();  // cleanup on blur
  }, []),
);

// Pass to remote component:
onScreenBlur={(closeModals: () => void) => {
  closeModalsRef.current = closeModals;
}}
```

## FAB offset — required when screens have floating buttons

```tsx
const setFabOffset = useChatActionsSelector(a => a.setFabOffset);

useEffect(() => {
  setFabOffset(20);
}, [setFabOffset]);
```

## Module names (federation remotes)

| Screen | Remote import |
|--------|--------------|
| Room Booking | `import('roomBooking/RoomBooking')` |
| Meal Reservation | `import('mealReservation/MealReservation')` |
| Time Off | `import('timeOff/TimeOff')` |
| Reallocation | `import('reallocation/Reallocation')` |
| Maintenance | `import('maintenance/Maintenance')` |

## Rules

- Always add `// @ts-ignore` above the `import()` — MF types are not generated
- Always wrap with `<ErrorBoundary>` + `<React.Suspense>` — never bare `React.lazy`
- Data fetching lives in the host (LazyLoad screen) — remote modules are pure presentational
- Show `<LoadingSlider />` while initial data loads; show `<FallbackLoadRemote />` while module loads
