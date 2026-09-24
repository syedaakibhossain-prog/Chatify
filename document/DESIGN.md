# Chatify — Design System

A minimalist, professional chat interface. The goal is calm and clarity — no decorative flourishes, no gradients, no shadows-for-the-sake-of-shadows. Every element earns its place.

Think: Linear, Things, Apple Messages, Stripe Dashboard. Restrained, functional, confident.

---

## 1. Design Principles

1. **Content first.** Message text is the focus. UI chrome recedes.
2. **Two colors, not twenty.** Neutral grays + one accent. That's it.
3. **No decoration.** No gradients, no glassmorphism, no animated backgrounds.
4. **Whitespace is a feature.** When in doubt, add more space, not more borders.
5. **Instant feedback.** Optimistic UI, subtle transitions (150–200ms max), never more.
6. **Dark mode is first-class.** Not an afterthought. Both modes ship.

---

## 2. Color Palette

A **neutral-first** palette with one accent color. We use **slate** for grays (cooler than zinc/gray — feels more "software") and a restrained **indigo** as the accent.

### Light Mode

| Token | Hex | Usage |
|---|---|---|
| `bg-canvas` | `#FFFFFF` | App background |
| `bg-subtle` | `#F8FAFC` | Sidebar, message thread background |
| `bg-muted` | `#F1F5F9` | Hover states, own message bubble |
| `bg-elevated` | `#FFFFFF` | Cards, modals (with border) |
| `border` | `#E2E8F0` | All borders, dividers |
| `border-strong` | `#CBD5E1` | Focus rings, emphasized borders |
| `text-primary` | `#0F172A` | Headings, message text |
| `text-secondary` | `#475569` | Labels, timestamps |
| `text-muted` | `#94A3B8` | Placeholders, disabled |
| `text-inverse` | `#FFFFFF` | Text on accent |
| `accent` | `#4F46E5` | Primary actions, active state, sent bubbles |
| `accent-hover` | `#4338CA` | Accent hover |
| `accent-subtle` | `#EEF2FF` | Accent tint background (selected row) |
| `success` | `#10B981` | Online dot, delivery confirmation |
| `warning` | `#F59E0B` | Reconnecting banner |
| `danger` | `#EF4444` | Failed message, delete |
| `danger-subtle` | `#FEF2F2` | Danger tint background |

### Dark Mode

| Token | Hex | Usage |
|---|---|---|
| `bg-canvas` | `#0B1120` | App background |
| `bg-subtle` | `#111827` | Sidebar, thread background |
| `bg-muted` | `#1E293B` | Hover states, own message bubble |
| `bg-elevated` | `#1E293B` | Cards, modals |
| `border` | `#1F2937` | Borders, dividers |
| `border-strong` | `#334155` | Focus rings |
| `text-primary` | `#F1F5F9` | Headings, message text |
| `text-secondary` | `#94A3B8` | Labels, timestamps |
| `text-muted` | `#64748B` | Placeholders, disabled |
| `text-inverse` | `#FFFFFF` | Text on accent |
| `accent` | `#6366F1` | Primary actions |
| `accent-hover` | `#818CF8` | Accent hover |
| `accent-subtle` | `#1E1B4B` | Accent tint background |
| `success` | `#34D399` | Online dot |
| `warning` | `#FBBF24` | Reconnecting banner |
| `danger` | `#F87171` | Failed message |
| `danger-subtle` | `#451A1A` | Danger tint |

### Why These Colors

- **Slate over gray/zinc** — cooler, more modern, less office-paper feel
- **Indigo over blue** — blue reads as "default link," indigo reads as "product accent"
- **White canvas in light mode** — pure white feels official; off-white feels like a template
- **Not-quite-black in dark mode** — `#0B1120` avoids the harsh contrast of pure black, easier on eyes
- **Own message bubble uses accent** — that's the single place color is loud; everything else is quiet

---

## 3. Typography

**Font family:**