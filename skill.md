# Frontend Skill — One Piece Bot

## Tech Stack

- **Framework**: Next.js 14.2 (App Router) + React 18
- **Language**: TypeScript (strict mode, path alias `@/*` → `./src/*`)
- **Styling**: Tailwind CSS 3.4 with custom theme
- **Backend**: FastAPI at `localhost:8000`, proxied via Next.js rewrites (`/api/*`, `/static/*`)
- **Alt UI**: `ui.py` (Streamlit) — legacy/demo interface, not the primary frontend

## Project Structure

```
frontend/
├── src/
│   ├── app/                  # App Router pages
│   │   ├── layout.tsx        # Root layout (bg image + gradient + Navbar)
│   │   ├── page.tsx          # Landing page (hero + feature cards)
│   │   ├── globals.css       # Tailwind base + custom classes
│   │   ├── chat/page.tsx     # Chat interface
│   │   └── theory/page.tsx   # Theory scorer
│   ├── components/           # Shared components
│   │   └── Navbar.tsx        # Sticky nav with active-path highlighting
│   └── lib/
│       ├── api.ts            # Typed fetch wrappers (sendChat, evaluateTheory)
│       └── types.ts          # Shared interfaces (ChatMessage, Passage, TheoryResult, etc.)
├── public/                   # Static assets (Logo.png)
├── tailwind.config.ts
├── next.config.js
└── tsconfig.json
```

## Design System

### Color Palette

| Token          | Value                    | Usage                      |
|----------------|--------------------------|----------------------------|
| `navy-900`     | `#020617`                | Page background            |
| `navy-800`     | `#0b1220`                | Elevated surfaces          |
| `navy-700`     | `#0f172a`                | Cards, panels              |
| `navy-600`     | `#1e293b`                | Borders, dividers          |
| `pirate-red`   | `#E63946`                | Destructive / accent       |
| `pirate-gold`  | `#eab308`                | Highlight / tagline accent |
| `indigo-600`   | `#4f46e5`                | Primary action (buttons, user bubbles) |
| `indigo-500`   | `#6366f1`                | Primary hover              |
| Text primary   | `#e2e8f0` (gray-200)     | Body text                  |
| Text secondary | `text-gray-400`          | Descriptions, muted        |
| Text tertiary  | `text-gray-500/600`      | Hints, metadata            |

### Surface & Border Convention

- **Borders**: Use `border-white/[0.06]` or `border-white/[0.08]` — never solid gray borders.
- **Subtle backgrounds**: `bg-white/[0.03]` to `bg-white/[0.05]` — translucent white over dark.
- **Hover states**: `hover:bg-white/[0.05]` or `hover:bg-white/[0.06]`.
- **Glass effect**: Use the `.glass` class for card surfaces (translucent navy + 16px blur + subtle border).

### Typography

- Font: system-ui stack (no custom fonts)
- Body text: `text-sm` (14px), `leading-relaxed`
- Small UI text: `text-[13px]` or `text-xs`
- Headings: `font-semibold` or `font-bold`, `text-white`
- Tracking: default for body, `tracking-tight` for headings, `tracking-[0.2em]` for uppercase labels

### Animations

- `.animate-in` — fadeInUp (0.35s ease-out) for entering elements
- `.typing-dot` — bounce animation for typing indicator (staggered delays)
- Use `transition-colors` on interactive elements, `transition-all duration-150` for nav items
- `transition-transform` for scale effects (e.g., logo hover)

### Layout Patterns

- **Max width**: `max-w-6xl` for nav, `max-w-2xl` for chat, `max-w-3xl` for card grids
- **Full-height pages**: `h-[calc(100vh-3.5rem)]` (subtract navbar 3.5rem)
- **Centering**: `mx-auto` with horizontal padding `px-4` or `px-6`
- **Spacing**: `space-y-5` between messages, `gap-2` to `gap-4` for flex/grid
- **Responsive**: mobile-first, `sm:` and `md:` breakpoints (e.g., `flex-col sm:flex-row`, `grid-cols-1 md:grid-cols-3`)

### Component Patterns

- All page components use `"use client"` directive
- State via React hooks (`useState`, `useRef`, `useEffect`)
- No external state management libraries
- Inline components for simple, page-specific UI (e.g., `FeatureCard` defined in `page.tsx`)
- Shared/reusable components go in `src/components/`

## Coding Conventions

1. **Tailwind-first**: All styling via Tailwind utility classes. Custom CSS only for animations and effects that can't be expressed as utilities (defined in `globals.css`).
2. **Minimal abstractions**: Small inline components are preferred over premature extraction. Only extract to `components/` when genuinely reused across pages.
3. **Type safety**: All API responses and component props are typed via `src/lib/types.ts`. Add new interfaces there, not inline.
4. **API layer**: All fetch calls go through `src/lib/api.ts` with typed return values. Never call `fetch()` directly from components.
5. **No external UI libraries**: No component library (shadcn, MUI, etc.) — all UI is hand-rolled with Tailwind.
6. **Image sources**: Character images come from the API (`/static/assets/`). Logo is in `/public/`.

## When Building New UI

- Match the existing dark theme — always use the navy/indigo/gray palette, never light backgrounds.
- Use `.glass` for card containers. Use translucent white borders (`border-white/[0.06]`).
- Add `.animate-in` to elements that enter the viewport.
- Keep text sizes small (`text-sm`, `text-[13px]`). This is a dense, modern UI — not a marketing page.
- Buttons: primary = `bg-indigo-600 hover:bg-indigo-500`, secondary/ghost = `border border-white/[0.12] hover:bg-white/[0.06]`.
- Disabled states: `disabled:opacity-30`.
- Inputs: `bg-white/[0.04] border border-white/[0.08] ... focus:border-white/[0.15]` — dark, subtle, no ring.
- Scrollbars are custom-styled (thin, translucent) — this is handled globally.
- The root layout already provides the background image + gradient overlay + Navbar. Pages just render content.
