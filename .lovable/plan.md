# 📚 Sipurim Sheli – Implementation Plan

## Guiding Principle
> "A product that lifts burden from a tired parent and creates a quiet moment of connection – evening after evening."

---

## Core Clarifications

### Browse / Catalog
- **Escape hatch only** – never exploration or discovery
- Home is always the primary entry
- Catalog exists for when suggestion doesn't fit, nothing more

### Reading History  
- **Shared memory, not usage log**
- No long lists, no timestamps, no progress tracking
- Feels like "what we've experienced together"

### Multi-child Home
- **Never parallel child journeys**
- Default: One family suggestion OR one selected child
- No side-by-side comparisons

### Technical Approach
- Stack decisions serve UX, not the reverse
- React/TypeScript/Tailwind as tools, not constraints

---

## 🌐 Part 1: Public Website

### 1.1 Landing Page
- Hero with emotional value proposition
- Visual preview (not full content)
- Trust indicators (educational approach, privacy)
- CTA: Start free trial → App onboarding

### 1.2 SEO Pages Structure
- **By Age**: Pages for ages 2-3, 4-5, 6-8
- **By Challenge**: Separation anxiety, new sibling, bedtime fears, kindergarten
- **By Theme**: Family, friendship, emotions, imagination
- Each: Series previews + educational context + CTA

### 1.3 Series Pages
- Description and theme
- Episode list (titles only)
- Age/situation tags
- Preview CTA → Trial

### 1.4 Book Preview Pages
- Cover illustration
- Brief description (2-3 sentences)
- Clear messaging: Full access in app

### 1.5 Trust Pages
- "Our Educational Approach"
- "How to Use" – Evening ritual guidance
- "For Parents" – FAQ, methodology

---

## 📱 Part 2: Closed App

### 2.1 Onboarding Flow
1. Welcome screen with emotional messaging
2. Create family profile (parent email only)
3. Add first child (name + age only)
4. Auto-generate first avatar
5. Immediate first suggestion → Evening flow

*No questionnaires. Learning happens gradually.*

### 2.2 Home Screen (Evening Entry)
**Primary state**: One clear suggestion
- "Continue with [Series Name]?" or "Tonight's story for [Child Name]"
- Large, single CTA: "Let's Begin"
- Subtle: "Or choose something else"

**Multi-child**: One family suggestion (never parallel journeys)
- Hidden toggle: Switch to individual child

**No clutter**: No carousels, no progress bars, no stats

### 2.3 Evening Flow (2 Clicks to Story)
1. Home → Accept suggestion
2. Parent Screen (optional, skippable)
3. Story Reader (full-screen, calm)
4. End Screen (quiet completion, soft "next time" suggestion)

### 2.4 The Infinite Journey
**Not visible as stages.** Manifests through:
- "What we've read together" – Shared memory, not list
- Gentle contextual labels
- Soft suggestions, never demands

### 2.5 Browse/Catalog (Escape Hatch Only)
- Accessible but not prominent
- Browse by: Age, Theme, Feelings
- Always returns to Home after selection
- **Not for exploration** – only when suggestion doesn't fit

### 2.6 Child Profiles
- Add/edit up to 4 children
- Name + Age (editable)
- Avatar display
- Advanced customization (unlocked gradually)

### 2.7 Family vs. Individual Mode
- Default: Family evening
- "Evening for [Child] only" – Hidden option

---

## ✨ Part 3: Story Creation (Premium)

### Visibility Rules
- Not shown: Day 1, Week 1, During active series
- Shown when: Series completion, No search results, Family events

### Creation Flow
1. "Create a special story?"
2. Select child
3. Select topic (predefined)
4. Select intensity
5. Select characters
6. Review → Generate

*No free text. Closed process.*

---

## 🌟 Part 4: Moments That Matter

### Grandparent Entry
- Contextual prompt, not feature showcase
- Supporting character role

### First Personal Story
- Presented as gift
- Quiet, personal moment

### Series Completion
- Calm completion
- No achievements or badges

---

## 👤 Part 5: Account & Settings

- Subscription management (Israeli provider hook)
- Family settings (children, extended family)
- Minimal preferences (notifications, reminder time)

---

## 📋 Screen Inventory

### Public (6 screens)
1. Landing Page
2. SEO Template (Age/Problem/Theme)
3. Series Page
4. Book Preview Page
5. About/Trust Pages
6. Login Entry

### App (11 screens)
1. Onboarding Flow
2. Home Screen
3. Parent Context Screen
4. Story Reader
5. End Screen
6. Browse/Catalog
7. Search Results
8. Child Profiles
9. Story Creation (5 steps)
10. Account Settings
11. Subscription

---

## 🚫 Explicitly Excluded

- Gamification (streaks, points, badges)
- Social sharing
- Character chat
- Real-time AI in UI
- Progress maps / numbered stages
- Multiple prominent suggestions
- Complex onboarding

---

## Implementation Order

### Phase 1: Foundation & Public
1. Design system (RTL, Hebrew typography, calm palette)
2. Layout components (Header, Navigation)
3. Landing Page
4. SEO page templates
5. Series/Book preview pages

### Phase 2: Core App Experience
1. Onboarding flow
2. Home Screen (evening entry)
3. Evening Flow (parent context → reader → end)
4. Child profile management

### Phase 3: Secondary Features
1. Browse/Catalog (escape hatch)
2. Reading history (shared memory view)
3. Account & settings

### Phase 4: Premium
1. Story creation flow
2. Moments that matter
