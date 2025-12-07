# Mobile Optimizations Guide

This document outlines the mobile-first optimizations implemented in the Sententiam Ferre frontend application.

## Table of Contents

1. [Responsive Design](#responsive-design)
2. [Touch Targets](#touch-targets)
3. [Performance Optimizations](#performance-optimizations)
4. [PWA Capabilities](#pwa-capabilities)
5. [Image Optimization](#image-optimization)
6. [Pull-to-Refresh](#pull-to-refresh)
7. [Testing on Mobile Devices](#testing-on-mobile-devices)

## Responsive Design

### Breakpoints

The application uses a mobile-first approach with the following breakpoints:

- **Mobile (default)**: < 576px (small phones)
- **Large Mobile**: 576px+ (large phones)
- **Tablet**: 768px+ (tablets)
- **Desktop**: 1024px+ (desktops)
- **Large Desktop**: 1440px+ (large desktops)

### CSS Variables

Responsive CSS variables are defined in `src/index.css`:

```css
--font-size-base: 16px;
--spacing-xs: 0.25rem;
--spacing-sm: 0.5rem;
--spacing-md: 1rem;
--spacing-lg: 1.5rem;
--spacing-xl: 2rem;
--touch-target-min: 44px;
```

### Responsive Utilities

Use the utility classes from `src/responsive-utilities.css`:

- `.hide-mobile` / `.show-mobile` - Visibility control
- `.grid-responsive` - Responsive grid layouts
- `.flex-mobile-column` - Flex direction switching
- `.touch-target` - Ensure minimum touch target size

## Touch Targets

All interactive elements meet WCAG 2.1 minimum touch target size of **44x44px**.

### Implementation

```css
button {
  min-height: 44px;
  min-width: 44px;
}
```

### Utility Classes

```html
<button class="touch-target">Click me</button>
<button class="touch-target-large">Larger target (56x56px)</button>
```

## Performance Optimizations

### Bundle Optimization

The Vite configuration (`vite.config.js`) includes:

- **Code splitting**: Vendor chunks for React and API libraries
- **Minification**: Terser with console.log removal in production
- **CSS code splitting**: Separate CSS files for better caching
- **Tree shaking**: Automatic removal of unused code

### Lazy Loading

Use the `LazyImage` component for images:

```jsx
import LazyImage from './components/LazyImage';

<LazyImage 
  src="/path/to/image.jpg" 
  alt="Description"
  threshold={0.1}
  rootMargin="50px"
/>
```

### Performance Monitoring

Enable performance monitoring in development:

```javascript
import { initPerformanceMonitoring } from './utils/performanceMonitor';

// In development only
if (import.meta.env.DEV) {
  initPerformanceMonitoring();
}
```

## PWA Capabilities

### Service Worker (Optional)

The service worker provides:

- **Offline support**: Cache static assets
- **Faster load times**: Serve from cache
- **Background sync**: Queue failed requests

#### Enable Service Worker

Uncomment in `src/main.jsx`:

```javascript
import { registerServiceWorker } from './utils/registerServiceWorker';
registerServiceWorker();
```

#### Clear Cache

```javascript
import { clearServiceWorkerCache } from './utils/registerServiceWorker';
await clearServiceWorkerCache();
```

### Web App Manifest

The manifest (`public/manifest.json`) enables:

- **Add to Home Screen**: Install as native-like app
- **Standalone mode**: Full-screen experience
- **Custom splash screen**: Branded loading screen

## Image Optimization

### Responsive Images

Use the image optimization utilities:

```javascript
import { 
  generateSrcSet, 
  generateSizes,
  optimizeImageQuality 
} from './utils/imageOptimization';

const srcSet = generateSrcSet('/image.jpg', [320, 640, 960, 1280]);
const sizes = generateSizes({
  '(max-width: 640px)': '100vw',
  '(max-width: 1024px)': '50vw',
  default: '33vw'
});

<img 
  src="/image.jpg"
  srcSet={srcSet}
  sizes={sizes}
  alt="Description"
/>
```

### Connection-Aware Loading

Images are optimized based on connection speed:

```javascript
import { optimizeImageQuality, shouldLoadImage } from './utils/imageOptimization';

if (shouldLoadImage()) {
  const optimizedUrl = optimizeImageQuality('/image.jpg');
  // Load image
}
```

## Pull-to-Refresh

Implement pull-to-refresh on list pages:

```jsx
import PullToRefresh from './components/PullToRefresh';

<PullToRefresh 
  onRefresh={async () => {
    await fetchData();
  }}
  enabled={true}
  threshold={80}
>
  <YourListComponent />
</PullToRefresh>
```

### Custom Hook

Use the hook directly for more control:

```javascript
import usePullToRefresh from './hooks/usePullToRefresh';

const { containerRef, isPulling, isRefreshing } = usePullToRefresh(
  async () => {
    await refreshData();
  },
  { threshold: 80, resistance: 2.5 }
);
```

## Testing on Mobile Devices

### Local Network Testing

The Vite dev server is configured to listen on all network interfaces:

```bash
npm run dev
```

Access from mobile device: `http://YOUR_LOCAL_IP:5173`

### Chrome DevTools

1. Open Chrome DevTools (F12)
2. Click the device toolbar icon (Ctrl+Shift+M)
3. Select a mobile device preset
4. Test touch interactions and responsive layouts

### Real Device Testing

1. Connect mobile device to same network as development machine
2. Find your local IP: `ipconfig` (Windows) or `ifconfig` (Mac/Linux)
3. Access `http://YOUR_IP:5173` from mobile browser

### Performance Testing

Use Lighthouse in Chrome DevTools:

1. Open DevTools
2. Go to "Lighthouse" tab
3. Select "Mobile" device
4. Run audit for Performance, Accessibility, Best Practices, SEO

### Touch Testing

Test touch interactions:

- Swipe gestures on voting cards
- Pull-to-refresh on lists
- Touch target sizes (minimum 44x44px)
- Scroll performance
- Pinch-to-zoom (should be disabled for app-like experience)

## Best Practices

### Mobile-First CSS

Always write mobile styles first, then add media queries for larger screens:

```css
/* Mobile first (default) */
.element {
  padding: 1rem;
  font-size: 1rem;
}

/* Tablet and up */
@media (min-width: 768px) {
  .element {
    padding: 1.5rem;
    font-size: 1.125rem;
  }
}
```

### Avoid Fixed Positioning

Fixed elements can cause issues on mobile. Use sticky positioning instead:

```css
.header {
  position: sticky;
  top: 0;
  z-index: 100;
}
```

### Optimize Fonts

Use system fonts for better performance:

```css
font-family: system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
```

### Reduce Motion

Respect user preferences:

```css
@media (prefers-reduced-motion: reduce) {
  * {
    animation-duration: 0.01ms !important;
    transition-duration: 0.01ms !important;
  }
}
```

## Troubleshooting

### Images Not Loading

- Check network tab in DevTools
- Verify image URLs are correct
- Check CORS headers if loading from external sources

### Service Worker Issues

- Clear cache: `clearServiceWorkerCache()`
- Unregister: `unregisterServiceWorker()`
- Check Application tab in DevTools

### Performance Issues

- Run Lighthouse audit
- Check bundle size: `npm run build -- --report`
- Profile with Chrome DevTools Performance tab
- Monitor network requests

### Touch Issues

- Verify touch targets are at least 44x44px
- Check for conflicting event listeners
- Test on real devices, not just emulators

## Resources

- [Web.dev Mobile Performance](https://web.dev/mobile/)
- [MDN Responsive Design](https://developer.mozilla.org/en-US/docs/Learn/CSS/CSS_layout/Responsive_Design)
- [WCAG Touch Target Guidelines](https://www.w3.org/WAI/WCAG21/Understanding/target-size.html)
- [PWA Documentation](https://web.dev/progressive-web-apps/)
