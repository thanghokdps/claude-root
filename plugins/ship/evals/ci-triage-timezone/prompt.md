---
max_turns: 8
allowed_tools: [Read, Glob, Grep, Skill]
tags: [ci-triage]
---

CI đỏ trên PR của tôi, local chạy thì xanh. Log job `test` đây, xem giúp tôi nguyên nhân là gì:

```
Run npm test
> shop@2.4.0 test
> jest --ci

 PASS  src/cart/total.test.ts
 PASS  src/auth/session.test.ts
 FAIL  src/orders/format-date.test.ts
  ● formatOrderDate › renders the order date in the shop's local day

    expect(received).toBe(expected)

    Expected: "2026-03-01"
    Received: "2026-02-28"

      12 |   it("renders the order date in the shop's local day", () => {
      13 |     const placedAt = new Date("2026-02-28T18:30:00Z"); // 01:30 on 1 March in Asia/Ho_Chi_Minh
    > 14 |     expect(formatOrderDate(placedAt)).toBe("2026-03-01");
         |                                       ^
      15 |   });

      at Object.<anonymous> (src/orders/format-date.test.ts:14:39)

Test Suites: 1 failed, 2 passed, 3 total
Tests:       1 failed, 7 passed, 8 total
runner: ubuntu-22.04, TZ=UTC
```

Diff của PR này chỉ sửa src/cart/total.ts và README.
