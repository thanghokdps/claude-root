---
model: opus
effort: high
name: codebase-design
description: Shared vocabulary for designing deep modules — a lot of behaviour behind a small interface, placed at a clean seam. Use when designing or improving a module's interface, deciding where a seam goes, making code more testable, or when another skill needs the deep-module vocabulary.
when_to_use: during /brainstorming when shaping a module, during /code-review when an interface feels wrong, when /tdd finds a test that has to reach past the interface, or when a refactor needs a reason more precise than "cleaner"
---

# Codebase Design

Design **deep modules**: a lot of behaviour behind a small interface, placed at a clean seam, testable through that interface.

This is a reference skill — mostly vocabulary. Use these terms exactly. Consistent language is the whole point; "component", "service", and "boundary" each mean four things and so mean nothing.

---

## Glossary

**Module** — anything with an interface and an implementation. Deliberately scale-agnostic: a function, a class, a package, a tier-spanning slice. *Avoid:* unit, component, service.

**Interface** — everything a caller must know to use the module correctly. The type signature, yes, but also invariants, ordering constraints, error modes, required configuration, and performance characteristics. *Avoid:* API, signature — both are too narrow, covering only the type-level surface.

**Implementation** — what is inside a module.

**Depth** — leverage at the interface: how much behaviour a caller or a test can exercise per unit of interface they must learn. **Deep** = large behaviour behind a small interface. **Shallow** = the interface is nearly as complex as the implementation.

**Seam** *(Michael Feathers)* — a place where you can alter behaviour without editing in that place; the *location* where a module's interface lives. Where the seam goes is its own decision, distinct from what sits behind it. *Avoid:* boundary — overloaded with DDD's bounded context.

**Adapter** — a concrete thing satisfying an interface at a seam. Names a *role* (which slot it fills), not substance (what is inside it).

**Leverage** — what callers get from depth: more capability per unit of interface learned. One implementation pays back across N call sites and M tests.

**Locality** — what maintainers get from depth: change, bugs, and verification concentrate in one place instead of spreading across callers. Fix once, fixed everywhere.

---

## Deep vs shallow

```
   DEEP                          SHALLOW  (avoid)
┌──────────────┐          ┌────────────────────────────┐
│Small Interface│         │      Large Interface       │
├──────────────┤          ├────────────────────────────┤
│              │          │  Thin Implementation       │
│    Deep      │          └────────────────────────────┘
│Implementation│
│              │
└──────────────┘
```

When designing an interface, ask:

- Can I remove a method?
- Can I simplify the parameters?
- Can I hide more complexity inside?

---

## Principles

- **Depth is a property of the interface, not the implementation.** A deep module can be internally composed of small, swappable parts — they just are not part of its interface. A module can have **internal seams** (private, used by its own tests) as well as the **external seam** at its interface.
- **The deletion test.** Imagine deleting the module. If complexity vanishes, it was a pass-through. If complexity reappears across N callers, it was earning its keep.
- **The interface is the test surface.** Callers and tests cross the same seam. Wanting to test *past* the interface means the module is the wrong shape — that is the signal `/tdd` produces and this skill answers.
- **One adapter is a hypothetical seam. Two adapters is a real one.** Introduce a seam when something actually varies across it, not before.

---

## Designing for testability

**Accept dependencies, don't create them.**

```typescript
function processOrder(order, paymentGateway) {}          // testable
function processOrder(order) { new StripeGateway(); }    // not
```

**Return results, don't produce side effects.**

```typescript
function calculateDiscount(cart): Discount {}            // testable
function applyDiscount(cart): void { cart.total -= d; }  // not
```

**Small surface area.** Fewer methods, fewer tests. Fewer parameters, simpler setup.

---

## Rejected framings

- **Depth as a ratio of implementation lines to interface lines** (Ousterhout) — rewards padding the implementation. Use depth-as-leverage.
- **"Interface" as the TypeScript `interface` keyword** — far too narrow. Interface here is every fact a caller must know.
- **"Boundary"** — say **seam** or **interface**.

---

## Where this sits

Reference, not a stage. It supplies vocabulary to:

| Skill | What it borrows |
|-------|-----------------|
| `/brainstorming` | depth, seam placement when shaping the approach |
| `/tdd` | seams — the agreed test surface |
| `/code-review` | shallow-module and leaky-interface findings |
| `/simplify` | the deletion test, for whether an abstraction earns its keep |
| `/blast-radius` | seams as the boundary a change stops at |

`rules/code-quality.md` governs readability inside a module. This skill governs the shape of the module itself.
