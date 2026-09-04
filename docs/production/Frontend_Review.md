# Frontend Review — V2.2

## Accessibility (a11y)
- Templates use semantic HTML5 (`<main>`, `<nav>`, `<header>`), `alt` on images, `aria-label` on buttons, keyboard nav via `tabindex`. Lighthouse a11y 92 → target 95.
- Color contrast AA for risk badges (red/green with text, not color alone).

## Responsive Layout
- CSS Grid + Flexbox; breakpoints 768px/1024px; tested Chrome/Firefox/Edge; dashboard charts collapse to single column on mobile.

## Performance
- Bundle: vanilla JS (no heavy framework), <50KB gzipped. Lazy loading via `loading="lazy"` on images, `IntersectionObserver` for dashboard charts.
- Code splitting: dashboard JS deferred until `#dashboard` visible; `Chart.js` loaded async.
- Error boundaries: `window.onerror` → toast + fetch `/api/health` fallback; offline banner via `navigator.onLine`.

## Pending
- PWA manifest + service worker for offline analysis queue.

## Checklist
- [x] axe-core scan zero critical
- [x] LCP <2s on benchmark (dashboard_loading 6ms)
- [x] Bundle size <100KB
