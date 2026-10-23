# Heketon Frontend

Next.js 16 App Router frontend for **Heketon** (HR & Office Ops AI Orchestrator), built for the Tencent Cloud Hackathon Indonesia 2026. The interface is developed using a customized TailAdmin Pro architecture, providing an accessible dashboard for HR operators to manage candidate interview escalations, review AI triage recommendations, approve outbound WhatsApp/Email communications with a 60-second undo window, and audit immutable system logs.

---

## Architecture & Directory Structure

The frontend is built on **Next.js 16 (App Router)** and **React 19** with strict localization boundaries:

```
frontend/
├── public/                 # Static assets (images, logos, favicons)
├── src/
│   ├── app/
│   │   ├── [locale]/       # Localized application shell (via next-intl)
│   │   │   ├── (admin)/    # Authenticated dashboard layouts (with Sidebar & Header)
│   │   │   └── (full-width-pages)/ # Unauthenticated / standalone views (Auth, Error)
│   │   └── globals.css     # Tailwind v4 configuration, theme tokens & custom styles
│   ├── components/         # Reusable UI components (Buttons, Modals, Tables, Forms)
│   ├── context/            # Global React Contexts (ThemeContext, SidebarContext)
│   ├── hooks/              # Custom React hooks (useModal, useTheme)
│   ├── i18n/               # next-intl routing, navigation wrappers & config
│   ├── icons/              # SVG icons compiled into React components via SVGR
│   ├── layout/             # Layout wrappers (Sidebar, AppHeader, Backdrop)
│   ├── lib/                # Shared utilities & API client (apiFetch, ApiError)
│   ├── messages/           # Localization dictionaries (en.json)
│   ├── proxy.ts            # Next.js 16 middleware (internationalization router)
│   └── services/           # Typed API service functions calling backend endpoints
├── package.json            # Dependencies & scripts
└── tsconfig.json           # TypeScript configuration
```

> [!IMPORTANT]
> All pages must reside inside `src/app/[locale]/`. Never create pages directly at `src/app/`. Navigation must be imported from `@/i18n/navigation`, not `next/navigation`.

---

## Tech Stack & Component Responsibilities

The frontend combines modern React 19 capabilities, low-runtime CSS with Tailwind v4, rich data visualization, interactive scheduling widgets, and direct AI streaming.

### 1. Core Framework & Language

| Technology | Version | Purpose & Functionality in Heketon |
| :--- | :--- | :--- |
| **Next.js 16 (App Router)** | `^16.3.4` | Modern React web framework with React Server Components (RSC), Client Components (`"use client"`), Turbopack dev engine, and localized routing. |
| **React 19** | `^19.2.8` | Core UI library utilizing modern concurrent rendering, Action hooks, and optimistic UI updates for smooth user interactions. |
| **TypeScript** | `^5.9.3` | Type-safe development with strict type inference across component props, DTOs, and API responses. |

### 2. Styling, Design System & Theming

| Technology | Version | Purpose & Functionality in Heketon |
| :--- | :--- | :--- |
| **Tailwind CSS v4** | `^4.1.17` | Zero-configuration utility CSS framework. Uses CSS-native `@theme` declarations inside `src/app/globals.css` rather than legacy `tailwind.config.js`. |
| **CSS Logical Properties** | *Native* | Direction-agnostic styling (`ms-*`, `pe-*`, `start-*`, `text-start`) guaranteeing full compatibility for both LTR and RTL layouts. |
| **clsx & tailwind-merge** | `^2.1.1` / `^2.6.0` | Helper utilities for safely joining conditional class names and eliminating conflicting Tailwind utility classes. |

### 3. Internationalization (i18n)

| Technology | Version | Purpose & Functionality in Heketon |
| :--- | :--- | :--- |
| **next-intl** | `^4.14.2` | Enterprise internationalization framework managing localized path routing (`src/i18n/routing.ts`), typed translation lookups (`src/messages/`), and localized navigation helpers (`Link`, `useRouter`, `usePathname`). |
| **proxy.ts** | *Custom* | Next.js 16 middleware file handling locale redirection and path matching. |

### 4. Interactive Scheduling & Rich Data Visualization

| Technology | Version | Purpose & Functionality in Heketon |
| :--- | :--- | :--- |
| **FullCalendar (`@fullcalendar/react`)** | `^7.1.0` | Calendar scheduling component. Visualizes Interviewer availability, candidate time slots across WIB/WITA/WIT, and automatic blackout periods (such as Friday Prayer 11:30–13:00). Dynamically imported (`ssr: false`). |
| **ApexCharts (`react-apexcharts`)** | `^2.1.1` | Analytics charts displaying recruitment KPIs, negotiation round distributions, triage success rates, and response latencies. Dynamically imported (`ssr: false`). |
| **Flatpickr** | `^4.6.13` | Lightweight date-time picker for precise manual slot overrides and operational rule setting. |
| **Swiper** | `^14.2.0` | Touch-enabled carousel component used for guided onboarding walkthroughs and multi-step action plan confirmation cards. |
| **SimpleBar React** | `^3.3.2` | Performance-optimized cross-browser scrollbar for dense data tables and chat logs. |
| **@react-jvectormap** | `^1.0.4` | Interactive SVG vector maps displaying candidate geographical distributions across Indonesian provinces and timezones. |

### 5. Drag-and-Drop & Document Handling

| Technology | Version | Purpose & Functionality in Heketon |
| :--- | :--- | :--- |
| **react-dnd & HTML5 Backend** | `^16.0.1` | Flexible drag-and-drop primitives powering the interactive candidate pipeline Kanban board (Application → Screening → Escalated → Scheduled). |
| **react-dropzone** | `^20.1.1` | Drag-and-drop file upload zone for CVs, job description documents, and company operational rule policies. |

### 6. Client-Side AI & Streaming

| Technology | Version | Purpose & Functionality in Heketon |
| :--- | :--- | :--- |
| **Vercel AI SDK (`ai`, `@ai-sdk/react`)** | `^7.0.148` / `^4.0.152` | Reactive hooks (`useChat`, `useCompletion`) and UI state utilities for streaming AI responses directly to the browser. |
| **AI Provider Adapters** | `@ai-sdk/google`, `@ai-sdk/openai`, `@ai-sdk/anthropic` | Client/server adapters for direct LLM connection when bypassing backend orchestration for simple client prompts. |

### 7. Icons & Assets

| Technology | Version | Purpose & Functionality in Heketon |
| :--- | :--- | :--- |
| **@svgr/webpack** | `^8.1.0` | Webpack loader that transforms raw SVG vector files into first-class, theme-aware React components inside `@/icons`. |

### 8. API Communication & State Management

| Technology | Version | Purpose & Functionality in Heketon |
| :--- | :--- | :--- |
| **apiFetch (`src/lib/api.ts`)** | *Internal* | Custom HTTP client wrapping the Fetch API. Automatically attaches `NEXT_PUBLIC_API_URL`, parses JSON payloads, handles bearer tokens, and unwraps FastAPI `ApiResponse[T]` responses. |
| **React Context** | *Native* | Lightweight state management for application-wide concerns (`ThemeContext` for Dark Mode toggle, `SidebarContext` for collapsible drawer state). |

---

## Shared Environment

The frontend reads configuration from the **root monorepo `.env`** loaded in `next.config.ts`:

```ini
# Exposed to the browser (prefixed with NEXT_PUBLIC_)
NEXT_PUBLIC_APP_NAME="Heketon"
NEXT_PUBLIC_API_URL="http://localhost:8000/api/v1"
NEXT_PUBLIC_SUPABASE_URL=""
NEXT_PUBLIC_SUPABASE_ANON_KEY=""
```

> [!CAUTION]
> Never prefix private credentials (database passwords, private API keys) with `NEXT_PUBLIC_`, as those will be bundled into client-side JavaScript.

---

## Developer Commands

Run from the `frontend/` directory:

```bash
# Install dependencies
pnpm install

# Start Turbopack development server on http://localhost:3000
pnpm dev

# Build production bundle
pnpm build

# Run linter
pnpm lint
```
