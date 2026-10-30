---
name: react-ui
description: React + TypeScript + SASS frontend conventions - project structure, component patterns, typed API clients generated from OpenAPI, data fetching and state, forms, styling with SASS tokens, accessibility, and testing. Use when creating or changing React components, pages, hooks, styles, or frontend API code.
---

# React + TypeScript UI conventions

TODO(team): confirm build tool (Vite/Next.js/CRA), router, data-fetching library, form library, and component library. Defaults below: Vite, React Router, TanStack Query, React Hook Form + Zod, SASS modules.

## Structure (feature folders)

```
src/
├── app/                 routes, providers, layout
├── features/<feature>/
│   ├── components/
│   ├── hooks/           useOrders(), useCreateOrder()
│   ├── api.ts           calls into the generated client
│   └── <Feature>Page.tsx
├── shared/              reusable components, hooks, utils
├── api/generated/       generated from openapi.yaml - never hand-edit
└── styles/              _tokens.scss, _mixins.scss, global.scss
```

## API layer

- Generate types (and optionally the client) from `docs/specs/<feature>/openapi.yaml` or the service's published spec. TODO(team): generator choice, e.g. `openapi-typescript` + `openapi-fetch`, or `orval`.
- Components never call `fetch` directly. They use feature hooks, which wrap the API layer with TanStack Query.
- Query keys: `[feature, resource, params]`. Invalidate on mutation success.

## Components

- Function components, named exports, props typed with an explicit `type <Name>Props`.
- Keep components small; extract hooks for logic. Presentational components receive data via props.
- Every data view handles **loading, empty, error, and success** states.
- No `useEffect` for derived state; compute it. `useEffect` is for syncing with external systems.
- Lists use stable keys from data IDs, never array indexes.

## Forms

- React Hook Form + Zod schema. Server validation errors (Problem Details `errors[]`) are mapped back onto fields.
- Disable submit while submitting; show success/error feedback.

## Styling (SASS)

- SASS modules per component (`Button.module.scss`).
- All colors, spacing, typography, radii, and breakpoints come from `styles/_tokens.scss`. No hard-coded hex values or pixel spacing in components.
- Use `@use`, not `@import`.
- Mobile-first media queries via a `respond-to($breakpoint)` mixin.

## Accessibility

- Semantic HTML first (`button`, `nav`, `main`, `label`). ARIA only to fill gaps.
- Every input has a label; every icon-only button has `aria-label`.
- Visible focus styles. Full keyboard operation. Color contrast at least WCAG AA.

## Testing

- Vitest/Jest + React Testing Library. Query by role and label, not test IDs, where possible.
- Mock the network at the boundary (MSW), not the hooks.
- E2E flows belong to the integration-testing skill (Playwright).

## Checklist

- [ ] Types come from the generated API, not hand-written duplicates
- [ ] Loading/empty/error states
- [ ] Styles use tokens only
- [ ] Keyboard and screen-reader usable
- [ ] `tsc --noEmit`, lint, and tests pass
