---
name: data-viz
description: Patterns for data visualization with D3.js and 3D scenes with Three.js inside React - integration approach, lifecycle and cleanup, responsiveness, performance, and accessibility. Use when building charts, graphs, maps, dashboards, or any WebGL/3D view.
---

# Data visualization (D3.js, Three.js) in React

Pick the reference for the library you are using:
- Charts, graphs, scales, axes, maps -> read `references/d3.md`
- 3D scenes, WebGL, models -> read `references/three.md`

## Rules for both

- Each visualization is its own component with a typed `data` prop and no data fetching inside it.
- React owns the container element; the library owns what is inside it. Never let both React and D3/Three mutate the same DOM nodes.
- Respond to container size with a `ResizeObserver` hook, not `window.resize`.
- Clean up everything on unmount (listeners, timers, animation frames, WebGL resources). Leaks show up as slowdowns after navigation.
- Colors come from the design tokens (see react-ui skill). Use a colorblind-safe categorical palette.
- Provide a text alternative: a title/description (`role="img"` + `aria-label`, or a visually hidden summary) and, for data charts, an accessible data table toggle.
- Test the data-transformation functions with unit tests. Visual output is checked manually or with screenshot tests.

TODO(team): link your chart style guide or design system chart specs.
