---
id: 0017
title: Dashboard UI glassmorphism redesign
stage: green
date: 2026-07-10
surface: agent
model: claude-fable-5
feature: 001-agentreplay-v1
branch: 001-agentreplay-v1
user: anusbutt
command: none
labels: ["dashboard", "ui", "shadcn", "framer-motion", "glassmorphism"]
links:
  spec: specs/001-agentreplay-v1/spec.md
  ticket: null
  adr: null
  pr: null
files:
 - dashboard/src/app/globals.css
 - dashboard/src/app/layout.tsx
 - dashboard/src/app/page.tsx
 - dashboard/src/app/loading.tsx
 - dashboard/src/app/runs/[id]/page.tsx
 - dashboard/src/app/runs/[id]/loading.tsx
 - dashboard/src/components/RunsList.tsx
 - dashboard/src/components/TimelineStep.tsx
 - dashboard/src/components/RunActions.tsx
 - dashboard/src/components/ForkPanel.tsx
 - dashboard/src/components/CompareView.tsx
 - dashboard/src/components/VerdictBadge.tsx
 - dashboard/src/components/VerdictCards.tsx
 - dashboard/src/components/CopyButton.tsx
 - dashboard/src/components/ui/button.tsx
 - dashboard/src/components/ui/badge.tsx
 - dashboard/src/components/ui/card.tsx
 - dashboard/src/components/ui/input.tsx
 - dashboard/src/components/ui/textarea.tsx
 - dashboard/src/components/ui/skeleton.tsx
 - dashboard/src/lib/utils.ts
 - dashboard/src/lib/format.ts
 - dashboard/package.json
 - CLAUDE.md
 - .specify/memory/constitution.md
 - specs/001-agentreplay-v1/research.md
tests:
 - npm run build (passes: TypeScript + Turbopack clean)
 - live render check vs local backend: /, /runs/[flagged], /runs/[fork] all 200 with expected content
---

## Prompt

i dont like the dashboard UI. updte it and use framer-motion, shadcn and react icon. make it deliverable not just only for demo. it should minimalist and glassmorphism with better UX. nothing should by confusing. or a better way is to use claude design you'll give me prompt for claude design i'll generate UI then give it to you. now use rubric out of 10 decide what option is best. we can use more libraries if needed.

## Response snapshot

Rubric comparison (weighted for deadline): in-repo redesign 8.6/10 vs
Claude-design-then-port 5.8/10 — chose in-repo. Rebuilt the dashboard as a
dark glassmorphism UI: vendored shadcn/ui primitives (button/badge/card/
input/textarea/skeleton with cva), framer-motion for stagger/expand
animations, lucide-react icons. New layout shell (sticky glass topbar,
ambient radial glows), animated runs list with fork lineage badges,
redesigned run detail (header with copy-id, detection card with intent-vs-
action contradiction layout, root-cause card with suggested-fix highlight
linking to fork panel, glass fork form with collapsible advanced
temperature, emerald-glow compare view, icon-coded expandable timeline),
loading skeletons. Updated pinned-stack lines in CLAUDE.md/constitution/
research.md (Tailwind-only → Tailwind + shadcn/framer-motion/lucide).
Build passes; verified live against seeded backend data.

## Outcome

- ✅ Impact: dashboard is deliverable-quality, consistent visual system, clearer detect→analyze→fork workflow
- 🧪 Tests: npm run build clean; SSR render verified against live backend (3 routes, real data)
- 📁 Files: 26 files (6 new ui primitives, 3 new components, 2 loading states, theme, docs)
- 🔁 Next prompts: user visual review at localhost:3001; rebuild compose frontend; Vercel deploy
- 🧠 Reflection: rubric favored in-repo redesign chiefly because external design mockups lose all data wiring in the port

## Evaluation notes (flywheel)

- none
