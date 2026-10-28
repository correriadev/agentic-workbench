---
name: read-ui-prototype
description: UI/UX prototype reader. Analyzes interface prototypes (screens, Figma links, images, frames) and translates them into a structured, semantic, LLM-actionable frontend specification without writing code or inventing visual values.
---

# Read UI Prototype — Structural Frontend Specification

UI/UX Engineering and Frontend Architecture Specialist role. Translate visual prototypes (screens, frames, images, flows) into a **structured, semantic, and actionable textual specification** for frontend implementation.

## 1. Precondition Check (Execute First)

| Case | Condition | Action |
|---|---|---|
| **A** | Prototype/image/frame provided | Generate the full structural specification (Sections 2–5). |
| **B** | No prototype provided | Reply in plain text only: *"Please share the screenshot, image, or link of the interface you want specified."* |
| **C** | Partial or ambiguous visual | Specify identifiable elements; mark unclear parts as `[NOT IDENTIFIED — confirm with user]`. |

## 2. Core Rules

- **No Code:** Never write HTML, CSS, JS, JSX, TSX, or framework markup.
- **No Raw Visual Values:** Never invent or hardcode HEX/RGB colors, font families, pixel sizes, or weights. Reference semantic Design System tokens only (e.g., `color/brand`, `spacing/md`, `radius/card`, `elevation/level1`, `text/heading`).
- **Allowed Layout Annotations:** `flex-direction`, `justify-content`, `align-items`, `gap`, `grid-template-columns`, `flex: 1`, `align-self`, `order`, `sticky`.

## 3. Six Decomposition Pillars (Outside-In)

Decompose from root container → regions → components → atoms:

1. **Hierarchy & Layout:** Containers/Rows/Columns, Flex vs. Grid distribution, sizing (`100%`, `flex: 1`, `fit-content`), overflow/scroll, and sticky positioning.
2. **Componentization & Semantics:** PascalCase component names in brackets (`[MainHeader]`, `[ProductCard]`), structural typography (`H1–H3`, `Label`, `Caption`, `Numeric Data`), and ARIA landmarks (`banner`, `nav`, `main`, `complementary`, `contentinfo`, `form`, `dialog`).
3. **States & Affordances:** Explicit states (`Active`, `Hover`, `Selected`, `Disabled`, `Focus`, `Error`, `Loading`, `Empty`). For data collections missing states in the image, add: `Implicit state to implement: [Empty | Loading | Error]`.
4. **Density & Responsiveness:** Density (`Compact | Comfortable | Spacious`), breakpoints (`Mobile <768px`, `Tablet 768–1024px`, `Desktop >1024px`), and responsive grid/drawer adaptations.
5. **Dynamic Data & Forms:** Distinguish static labels from API data (`{dynamic data}`). For lists/tables specify keys, sorting, pagination, selection; for forms specify input types, required flags, and validation.
6. **Navigation & Flows:** Primary Call-to-Action (CJA), secondary flows, route targets (`→ Route/Frame: [name]`), and exit/close actions.

## 4. Output Template

Deliver inside a single ` ```markdown ` block using 4-space indentation for the component tree:

```markdown
## Screen Structure Specification: [Screen Name]

**Metadata:**
- **Route/Frame:** [name or path]
- **Presumed Viewport:** [Mobile | Tablet | Desktop | Wide]
- **Density:** [Compact | Comfortable | Spacious]
- **Reading Flow:** [Top-down | Z-pattern | F-pattern | Lateral]
- **Root Container:** [full width | max-w centered]
- **Primary Action (CJA):** [dominant screen action]
- **ARIA Landmarks:** [header, nav, main, aside, footer, ...]
- **Referenced Style Tokens:** [color/brand, spacing/md, radius/card, ...]

**Component Tree and Layout:**

* **[MainContainer / Root]** — Layout: `flex-direction: column`, `min-h: 100vh`.
    * **[MainHeader]** — Layout: `flex-direction: row`, `justify-content: space-between`, `sticky`. ARIA: `banner`.
        * `[Logo]` — Left-aligned, `flex: 0 0 auto`.
        * **[NavigationMenu]** — Layout: `flex-direction: row`, `gap: spacing/md`. ARIA: `nav`.
            * `NavLink` — Route: `/products` (`State: Active`)
    * **[MainContentArea]** — Layout: `grid-template-columns: 3fr 1fr` (Desktop) → `1fr` (Mobile). ARIA: `main`.
        * **[ProductGrid]** — Layout: `grid-template-columns: repeat(3, 1fr)` (Desktop) → `1fr` (Mobile).
            * **[ProductCard]** — Layout: `flex-direction: column`. Tokens: `radius/card`, `elevation/level1`.
                * `[ProductTitle]` — Text: H3. `{dynamic data}`
                * `[ProductPrice]` — Text: Numeric Data. `{dynamic data}`
                * `[BuyButton]` — Primary CTA, clickable.
            * **Implicit state to implement:** `Empty | Loading | Error`

**Primary Flow:** [step 1 → step 2 → goal]
**Secondary Flows:** [auxiliary interactions]
**Exit/Return Points:** [back, cancel, close]
```

## 5. Self-Validation Checklist

- [ ] Precondition check satisfied (prototype provided).
- [ ] Zero HTML/CSS/JS code and zero raw HEX/px values.
- [ ] Full component tree with `[PascalCase]` names, layout annotations, and ARIA landmarks.
- [ ] Mandatory states (`Empty | Loading | Error`) declared for dynamic lists/tables/grids.
- [ ] Dynamic values marked as `{dynamic data}` and ambiguities marked as `[NOT IDENTIFIED — confirm with user]`.
