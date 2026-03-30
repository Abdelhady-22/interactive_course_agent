# Interactive Course Platform — Complete Project Overview

---

## 📖 The Story Behind the Project

### The Problem

Creating high-quality educational video courses is an enormous undertaking. An instructor records hours of video, speaking directly to a camera, explaining complex topics like chemistry, mathematics, or engineering. But a raw video of a talking head — no matter how excellent the content — fails to captivate modern learners. Students expect dynamic visuals: formulas appearing on screen at the right moment, diagrams zooming in when referenced, charts sliding in during data discussions, and the instructor shrinking to a small picture-in-picture window when the content on the board matters more than their face.

Traditionally, this "layout direction" work is done entirely by **human video editors**. They watch the entire lecture, read the script, and manually decide — paragraph by paragraph — how the screen should look:

- *"The instructor is greeting the class? Show them full-screen."*
- *"They're explaining a chemical formula? Board takes 70%, instructor becomes a small PiP."*
- *"There are two charts to compare? Grid layout."*
- *"Summary paragraph? Back to full-screen instructor."*

For a 30-minute course with 40+ paragraphs, this process takes **hours of tedious manual work**, is **expensive**, and the quality depends entirely on the editor's experience and judgment.

### The Vision

**What if an AI agent could watch the script instead of a human editor — and automatically decide the best screen layout for every single paragraph?**

That is exactly what the **Interactive Course Platform** does.

It takes a structured course script (the paragraphs the instructor reads, timestamped with their keywords and linked visual assets), feeds it through a **hybrid AI decision pipeline**, and produces a complete set of **layout decisions** — one per paragraph — ready for a human editor to review, approve, and publish.

The result is a JSON playback file that tells a frontend player exactly:
- What layout mode to use (14 modes available)
- Where the instructor appears (position, size, style)
- Which assets appear on the board and when
- How to transition between paragraphs
- Which keywords to highlight as the instructor speaks
- Whether the instructor should remain "pinned" in place across consecutive paragraphs for visual stability

### Who Is It For?

| Role | How They Use It |
|------|-----------------|
| **Course Creator / Instructor** | Records a video, provides a script with keywords and visual assets |
| **Content Team** | Uploads the script and assets to the platform via the API |
| **AI Agent (the platform)** | Automatically generates layout decisions for every paragraph |
| **Human Editor** | Reviews the AI's decisions, overrides any that need adjustment, approves |
| **Learner** | Watches the final published course with dynamic, professionally-directed layouts |

### The Core Philosophy

> **"The script is the source of truth."**

The platform never sends video or image files to the AI. Instead, it sends **text descriptions** of assets and the **script content** to the LLM. The AI reasons about *what kind of content this is* and *what visual layout would serve the learner best* — just like an experienced human director would.

This approach has three major advantages:
1. **Cost-efficient** — No expensive vision models needed; text LLMs are cheap and fast
2. **Deterministic where possible** — Obvious cases (greetings, formulas, summaries) are handled by fast rules, not the LLM
3. **Human-in-the-loop** — Every AI decision is reviewed by a human editor before publication

---

## ✨ Features

### 🎬 14 Layout Modes

The platform supports a rich vocabulary of screen compositions, giving the AI (and human editors) fine-grained control:

| # | Mode | When To Use | Screen Composition |
|---|------|-------------|-------------------|
| 1 | `instructor_only` | Greetings, emotional moments, summaries | Instructor fills 100% of screen |
| 2 | `board_only` | Complex diagrams needing maximum space | Board fills 100%, no instructor |
| 3 | `board_dominant` | Formulas, key visuals | Board 70%, instructor as small PiP |
| 4 | `instructor_dominant` | When gestures/expression matter | Instructor 70%, small content overlay |
| 5 | `split_50_50` | Data charts with equal explanation weight | Equal split between board and instructor |
| 6 | `split_60_40` | Visual slightly more important | Board 60%, instructor 40% |
| 7 | `instructor_pip` | Large images, detailed diagrams | Content 100%, instructor 15% PiP |
| 8 | `picture_in_picture_large` | Content primary, but instructor adds value | Content 100%, instructor 30% PiP |
| 9 | `instructor_behind_board` | Creative/artistic moments | Semi-transparent instructor behind board |
| 10 | `overlay_floating` | Quick formula reference | Instructor 100%, small floating asset |
| 11 | `board_with_side_strip` | Wide horizontal content | Board center 70%, instructor side strip |
| 12 | `multi_asset_grid` | Comparing images, multi-step processes | Multiple assets in grid, instructor PiP |
| 13 | `fullscreen_asset` | High-detail photos, immersive visuals | Single asset fills 100%, no instructor |
| 14 | `stacked_vertical` | Mobile-friendly format | Instructor top half, board bottom half |

### 🤖 Hybrid AI Decision Engine            (I STILL NEED FEATURE THAT THE LLM CAN REVIEW ON RULE RESULT AND IF IT GOOD OK IF NOT EDIT IT )

The platform uses a **two-tier hybrid approach** — fast deterministic rules first, LLM intelligence second:

1. **Rule Engine (6 Rules)** — Handles obvious, predictable cases instantly:
   - Introduction/greeting paragraphs → `instructor_only`
   - Summary/recap paragraphs → `instructor_only`
   - Multiple assets present → `multi_asset_grid`
   - Formula detected → `board_dominant`
   - Single image/diagram → `board_dominant` or `fullscreen_asset`
   - Chart/graph data → `split_50_50` or `split_60_40`

2. **LLM Agent (CrewAI Layout Director)** — Handles ambiguous cases that rules can't decide:
   - Mixed content types
   - Context-dependent decisions
   - Unusual keyword combinations
   - Cases where the "right" answer depends on teaching intent

This hybrid approach means that for a typical 10-paragraph course, **6-8 paragraphs are decided by rules** (instant, free) and only **2-4 need the LLM** (slower, may cost tokens). This dramatically reduces cost and latency.

### 🔗 Cross-Paragraph Continuity (Instructor Pinning)

One of the platform's most sophisticated features. When multiple consecutive paragraphs all display visual assets, the **Sequence Analyzer** detects this pattern and "pins" the instructor in a consistent position throughout the sequence — instead of having them jump around between every paragraph.

**Why it matters:** Imagine a chemistry course where 5 paragraphs in a row show different formulas and diagrams. Without pinning, the instructor would slide from bottom-right to center to left to bottom-right every 20 seconds — creating a distracting, jarring experience. With pinning, the instructor stays as a small PiP in the bottom-right corner, and only the board content changes. The learner's eye stays focused on the content.

**How it works:**

```
Paragraph 1: Formula → board_dominant, instructor at bottom_right (PIN START)
Paragraph 2: Diagram → board_dominant, instructor stays bottom_right (PINNED)
Paragraph 3: Chart   → split_50_50, instructor stays bottom_right (PINNED)
Paragraph 4: Image   → board_dominant, instructor stays bottom_right (PINNED)
Paragraph 5: Summary → instructor_only, instructor moves to center (PIN BREAK)
```

### 📐 Board-as-Container Layout System (MVP)

The board isn't just a background — it's a **smart container** that holds everything except the instructor:
- **Script text** — with a `visibility_ratio` (0.0 = hidden, 1.0 = full text) controlling how much text appears
- **Keyword badges** — positioned across the top of the board, staggered in time
- **Assets** — images, formulas, diagrams, and charts with percentage-based positioning

All positions are expressed as percentages (0-100%), making layouts **resolution-independent**. A layout that works on a 1920×1080 screen works identically on a 4K display.

### 📝 Content-Aware Script Display

The platform intelligently decides how much of the script to show on screen at any given moment:

| Layout Mode | Script Visibility | Reasoning |
|-------------|------------------|-----------|
| `instructor_only` | 0% (hidden) | Instructor is talking directly — no text needed |
| `board_dominant` with assets | 30% (key phrases) | Asset is the focus, text is supplementary |
| `split_50_50` | 50% (half shown) | Balanced between visual and text |
| `board_only` without assets | 100% (full text) | Text IS the content |

### 👤 Human-in-the-Loop Workflow

Every decision goes through a clear lifecycle:

```
AI Generates Decision → Editor Reviews → Override if needed → Approve → Publish → Learner Playback
```

Editors can:
- View all decisions for a course
- Override any individual decision (change layout, assets, transitions)
- Re-run the AI agent on a single paragraph
- Approve decisions individually or all at once
- Publish the course when satisfied

### 🔄 Multi-Provider LLM Support

The platform is **provider-agnostic**. Switch your LLM provider by changing a single environment variable:

| Provider | Model Example | Cost |
|----------|--------------|------|
| Ollama (local) | `ollama/llama3` | Free |
| Ollama Cloud | `ollama/glm-5:cloud` | Free tier |
| Groq | `groq/llama-3.1-70b-versatile` | ~$0.000005/call |
| OpenAI | `gpt-4o` | ~$0.005/call |
| Anthropic | `claude-3-sonnet` | ~$0.007/call |
| Cohere | `cohere/command-r` | Varies |

### 📊 Token Usage Tracking

Every LLM call is tracked with detailed metrics:
- Prompt tokens and completion tokens per paragraph
- Total session usage across an entire course
- Cost estimates for all major providers
- Breakdown of which paragraphs were decided by rules vs. LLM

### 🔒 Production-Ready Error Handling

- **Retry with exponential backoff** — LLM calls retry 3 times with 1s → 2s → 4s delays
- **Configurable timeout** — Catch hung LLM calls (default: 120s)
- **Safe fallback** — If both rules and LLM fail, the system produces a safe `split_50_50` layout with a clear warning
- **Structured error codes** — Every error returns a machine-readable code for frontend integration
- **Rotating log files** — Production logs with 10MB rotation and 5 backup files

---

## 🎓 Real-World Example

The platform ships with a complete sample course: **"Introduction to Chemistry — Acids and Metals"** taught by Dr. Ahmed. This 5.5-minute course has:

- **10 paragraphs** — from greeting to summary
- **8 visual assets** — photos, formulas, diagrams, charts, and infographics
- **Full keyword coverage** — from "hydrochloric acid" to "reactivity series"

### Sample Walkthrough

| Paragraph | Content | AI Decision | Why |
|-----------|---------|-------------|-----|
| 1. Welcome | *"Welcome to this course on chemistry..."* | `instructor_only` — full screen | Rule 1: greeting keywords detected, no assets |
| 2. Experiment | *"When hydrochloric acid reacts with zinc..."* | `board_dominant` — board 70%, instructor PiP | Rule 4: formula asset detected |
| 3. Equation | *"Let's look at the chemical equation..."* | `board_dominant` — formula centered | Rule 4: formula keyword + asset |
| 4. Electron Transfer | *"Let's examine the electron transfer diagram..."* | `board_dominant` — diagram displayed | Rule 5: single diagram asset |
| 5. Reactivity | *"It all comes down to the reactivity series..."* | LLM decides → `instructor_dominant` | No rule match — LLM uses context |
| 6. Data Analysis | *"If we look at the reaction rate..."* | `split_50_50` — chart + instructor | Rule 6: chart asset detected |
| 7. Temperature | *"Comparing this rate data with temperature..."* | `split_60_40` — 2 charts, more room | Rule 6: multiple chart assets |
| 8. Close-Up Photo | *"A close-up photograph of the zinc surface..."* | `fullscreen_asset` — photo fills screen | Rule 5: detailed image keywords |
| 9. History | *"The Industrial Revolution..."* | `board_dominant` — historical image | Rule 5: single image asset |
| 10. Summary | *"Let's recap what we've learned..."* | `instructor_only` — full screen | Rule 2: summary keywords detected |

---

## 🏗️ Technical Architecture

### Technology Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| **Web Framework** | FastAPI 0.115 | REST API with auto-generated Swagger docs |
| **Validation** | Pydantic 2.10 | Request/response schema validation |
| **AI Agent Framework** | CrewAI ≥0.118 | Structured agent with role, goal, backstory |
| **LLM Provider Layer** | LiteLLM ≥1.60 | Unified interface to multiple LLM providers |
| **Native Ollama** | ollama ≥0.4.0 | Direct access to Ollama Cloud (GLM-5, Kimi) |
| **Token Counting** | tiktoken ≥0.9.0 | Accurate token estimation for cost tracking |
| **Containerization** | Docker + Docker Compose | Multi-container deployment |


LAYERED ARCHITECTURE USED IN THE APP 

### How Components Interact — Step by Step

#### Phase 1: Data Ingestion

```
Script + Keywords + Assets  →  Transcript Ingestion  →  (paragraphs, assets, video_context)
```

1. **Input**: A structured course script (JSON file) containing:
   - Course Title and description
   - Paragraphs with text, timestamps (`start_ms`, `end_ms`), and keywords
   - Visual assets (images, formulas, diagrams, charts) with descriptions

2. **Transcript Ingestion** (`ingest_transcript.py`): If the input is a file, this module, parses the JSON, converts timestamps from seconds to milliseconds, extracts visual assets, and produces the standard `(paragraphs, assets, video_context)` tuple.


#### Phase 2: Pre-Processing (Sequence Analysis)

```
All Paragraphs + Assets  →  Sequence Analyzer  →  ContinuityHints (one per paragraph)
```

Before any individual paragraph is processed, the **Sequence Analyzer** runs a global scan:

1. **Classify each paragraph**: Is it narration? A formula paragraph? Multi-asset? Data visualization?
2. **Detect consecutive asset runs**: If paragraphs 3, 4, 5, 6 all have visual assets, they form a "sequence"
3. **Determine pin position**: Based on asset types in the sequence, choose where the instructor should be pinned (e.g., bottom_right/small/pip for diagrams, right/medium/normal for charts)
4. **Generate hints**: Each paragraph gets a `ContinuityHint` with:
   - `is_sequence_start` / `is_sequence_middle` / `is_sequence_end`
   - `pin_instructor` (true/false)
   - `pin_position`, `pin_size`, `pin_style`

#### Phase 3: Per-Paragraph Decision Pipeline

For each paragraph (in order), the engine runs:

```
┌─────────────────┐     match     ┌─────────────────┐
│  Rule Engine    │──────────────▶│  DecisionOutput  │
│  (6 rules)     │               │  (instant)       │
└────────┬────────┘               └─────────────────┘
         │ no match
         ▼
┌─────────────────┐     success   ┌─────────────────┐
│  LLM Agent     │──────────────▶│  DecisionOutput  │
│  (with retry)  │               │  (validated)     │
└────────┬────────┘               └─────────────────┘
         │ all retries failed
         ▼
┌─────────────────┐
│  Safe Fallback  │──────────────▶ split_50_50 + warning
│  (always works) │
└─────────────────┘
```

**Context passed to each decision:**
- The paragraph's text, keywords, and timestamps
- Up to 3 previous decisions (sliding window)
- The continuity hint from the Sequence Analyzer
- All available course assets

#### Phase 4: Post-Processing

After each decision:

1. **Continuity Enforcement**: If the Sequence Analyzer says "pin this paragraph", the engine overrides the instructor position to match the pinned sequence — regardless of whether the rule engine or LLM made the decision.

2. **Board Layout Computation**: The `board_layout.py` module computes exact percentage-based positions for:
   - Script text (with visibility ratio)
   - Keyword badges (staggered across the top)
   - Assets (single-centered, side-by-side, or 2×2 grid depending on count)

3. **Token Tracking**: Every LLM call's token usage is recorded. Rules contribute zero tokens.

#### Phase 5: Output

The final output is a **Playback JSON** consumed by the frontend player:

```json
{
  "course_id": "54b10d9c-...",
  "title": "Introduction to Chemistry — Acids and Metals",
  "video_filename": "chemistry_101.mp4",
  "decisions": [
    {
      "paragraph_id": "c027e7f5-...",
      "layout": {
        "mode": "instructor_only",
        "description": "Instructor fills the entire screen. Welcome moment.",
        "instructor": { "visible": true, "position": "center", "size": "full", "style": "normal" },
        "board": { "visible": false, "position": "none", "size": "none" },
        "board_container": {
          "visible": false,
          "position": { "x_percent": 0, "y_percent": 0, "width_percent": 0, "height_percent": 0 }
        }
      },
      "assets": [],
      "transition": { "type": "fade", "duration_ms": 400, "instruction": "Smooth fade into greeting." },
      "script_display": {
        "instruction": "Show paragraph text at the bottom. Highlight keywords.",
        "keywords_to_highlight": ["welcome", "introduction"]
      },
      "continuity": {
        "pin_instructor": false,
        "transition_instructor": true,
        "sequence_note": "Intro — instructor takes full screen."
      },
      "director_note": "Introduction paragraph. Instructor is the sole focus — build personal connection.",
      "confidence": 0.95,
      "decided_by": "rule",
      "is_approved": true
    }
  ]
}
```






### Key Design Decisions

| Decision | Rationale |
|----------|-----------|
| **Script is the source of truth** | Speech-to-text (STT) is only used for timestamp alignment. The instructor's actual script — reviewed and edited — is what the AI reasons about. |
| **Text-only LLM input** | No video/image files are sent to the LLM. Assets are described in text. This makes the system fast, cheap, and provider-agnostic. |
| **Rules before LLM** | Obvious cases (greeting → full screen) don't need AI. Rules are instant and free. Only ambiguous paragraphs go to the LLM. |
| **Human-in-the-loop** | Every AI decision is reviewed by a human editor before publication. Trust but verify. |
| **Percentage-based positioning** | All board positions use percentages (0-100%), making layouts resolution-independent from mobile (360p) to 4K. |
| **Provider-agnostic LLM layer** | A single `.env` variable switches between Ollama (free, local), Groq (cheap, fast), OpenAI (high quality), or Anthropic. No code changes needed. |
| **Fallback safety net** | If both rules and LLM fail completely, the system generates a safe `split_50_50` layout with a warning. The show must go on. |
| **Cross-paragraph awareness** | The AI doesn't decide in isolation. It sees the last 3 decisions and continuity hints, enabling intelligent transitions and visual stability. |

---

## 🔄 Complete Workflow Summary

```
1. Instructor Records Video → Raw video file

2. Content Team Creates Script
   → Paragraphs with text + timestamps
   → Keywords per paragraph  
   → Visual assets (images, formulas, charts, diagrams)

3. Upload to Platform (via API)


4. Run AI Pipeline
  
   → Sequence Analyzer scans all paragraphs
   → For each paragraph: Rules → LLM → Continuity → Board Layout
   → All decisions stored in database

5. Editor Review
    view all decisions
    override if needed
    re-run AI on one paragraph
    approve individual
    approve all

6. Publish
  publish

7. Learner Playback
    returns full playback JSON
   
```

---

*Interactive Course Platform v0.2.0 — AI-powered layout direction for the future of education.*


































## Available Layout Modes

You MUST choose one of these 14 layout modes:

### Instructor-Focused Modes
1. **instructor_only** — Instructor fills the entire screen. No board, no assets.
   Use for: greetings, introductions, emotional moments, personal stories, summaries.

2. **instructor_dominant** — Instructor takes ~70% of screen. Board/asset appears as small overlay.
   Use for: when the instructor's expression/gesturing is important, with a supporting visual.

### Board/Content-Focused Modes
3. **board_only** — Board fills the entire screen. No instructor visible.
   Use for: complex diagrams that need maximum space, detailed infographics.

4. **board_dominant** — Board takes ~70% of screen. Instructor appears as small PiP in a corner.
   Use for: formulas, experiment images, key visuals that are the main focus.

5. **fullscreen_asset** — A single asset fills 100% of screen. No instructor, no board chrome.
   Use for: high-detail photos, detailed experiment images, immersive visuals that need every pixel.

### Split/Balanced Modes
6. **split_50_50** — Screen split equally: board on left, instructor on right (or vice versa).
   Use for: data charts/graphs where both the instructor's explanation and the visual carry equal weight.

7. **split_60_40** — Board takes 60%, instructor takes 40%. A softer split.
   Use for: when the visual is slightly more important but instructor should remain clearly visible.

### PiP (Picture-in-Picture) Modes
8. **instructor_pip** — Content fills the screen. Instructor in a small window (15%) in bottom corner.
   Use for: when a large image, experiment photo, or detailed diagram needs maximum screen space.

9. **picture_in_picture_large** — Content fills the screen. Instructor in a larger window (30%).
   Use for: when the content is primary but instructor's gestures/expressions still add value.

### Layered/Creative Modes
10. **instructor_behind_board** — Instructor appears semi-transparently behind the board content.
    Use for: creative/artistic moments, layered explanations where instructor and content merge.

11. **overlay_floating** — Instructor fills the screen normally. Asset floats as small overlay (20-30%).
    Use for: quick reference (formula callout, small diagram) while instructor continues talking.

### Multi-Element Modes
12. **board_with_side_strip** — Board takes center ~70%. Instructor appears in a vertical strip on the side.
    Use for: content that needs wide horizontal space but the instructor should remain clearly visible.

13. **multi_asset_grid** — Multiple assets displayed in a grid layout. Instructor as PiP in corner.
    Use for: comparing images, showing multiple formulas side by side, multi-step processes.

14. **stacked_vertical** — Instructor on top half, board/asset on bottom half.
    Use for: mobile-friendly format, or when vertical organization makes content clearer.
"""

ASSET_POSITIONS = """
## Asset Positions

When placing assets on the board, use these positions:
- **board_center** — Centered on the board (primary focus)
- **board_top** — Top area of the board
- **board_bottom** — Bottom area of the board
- **board_left** — Left side of the board
- **board_right** — Right side of the board
- **overlay** — Floating over the instructor or mixed content
- **grid_top_left** — Top-left cell (for multi_asset_grid mode)
- **grid_top_right** — Top-right cell (for multi_asset_grid mode)
- **grid_bottom_left** — Bottom-left cell (for multi_asset_grid mode)
- **grid_bottom_right** — Bottom-right cell (for multi_asset_grid mode)
"""

TRANSITION_TYPES = """
## Transition Types

When specifying transitions between layouts:
- **fade** — Smooth opacity fade (default, safest choice)
- **slide_left** — Content slides in from the right
- **slide_right** — Content slides in from the left
- **cut** — Instant switch (use for high-energy moments)
- **dissolve** — Cross-dissolve between layouts
- **none** — No transition (use when instructor is PINNED and only assets change)
"""

CONTINUITY_INSTRUCTIONS = """
## Cross-Paragraph Continuity

IMPORTANT: You are NOT deciding in isolation. You receive context about previous paragraphs.

### Instructor Pinning
When multiple consecutive paragraphs show visual assets, the instructor should stay in a
CONSISTENT position. This is called "pinning."

- If the previous paragraph has the instructor at "bottom_right/small/pip", and this paragraph
  also has board assets, KEEP the instructor at the same position.
- Only MOVE the instructor when there's a clear context shift (e.g., asset sequence ends,
  narration begins, or a dramatically different asset type appears).
- When pinning, set `continuity.pin_instructor: true` and `transition.type: "none"` for the
  instructor (only the ASSET content transitions, not the instructor).

### When to Break a Pin
- Moving from asset-heavy content to pure narration
- Moving from board content to instructor-focused storytelling
- A dramatic topic change that warrants visual punctuation

### The continuity field
Always include a `continuity` object in your output:
```json
"continuity": {
    "pin_instructor": true/false,
    "pin_from_paragraph": "<paragraph_id that started the pin, or null>",
    "transition_instructor": true/false,
    "sequence_note": "<explain why you're pinning or breaking the pin>"
}
```
"""

OUTPUT_SCHEMA = """
## Required Output JSON Schema

You MUST return valid JSON matching this exact structure:

```json
{
  "paragraph_id": "<the paragraph_id from the input>",
  "layout": {
    "mode": "<one of the 14 layout modes>",
    "description": "<human readable description of what the screen looks like>",
    "instructor": {
      "visible": true/false,
      "position": "<position on screen>",
      "size": "<small/medium/large/full>",
      "style": "<pip/normal/semi_transparent>"
    },
    "board": {
      "visible": true/false,
      "position": "<position on screen>",
      "size": "<small/medium/large/full/none>"
    }
  },
  "assets": [
    {
      "id": "<asset id from available_assets>",
      "type": "<asset type>",
      "name": "<asset name>",
      "position": "<where on the board>",
      "size": "<small/medium/large>",
      "display_instruction": "<clear instruction for how to render this asset>",
      "appear_at_ms": <when this asset should appear>,
      "disappear_at_ms": <when this asset should disappear>
    }
  ],
  "transition": {
    "type": "<transition type>",
    "duration_ms": <100-2000>,
    "instruction": "<human readable transition instruction>"
  },
  "script_display": {
    "instruction": "<how to show the paragraph text on screen>",
    "keywords_to_highlight": ["<keyword1>", "<keyword2>"]
  },
  "continuity": {
    "pin_instructor": true/false,
    "pin_from_paragraph": "<paragraph_id or null>",
    "transition_instructor": true/false,
    "sequence_note": "<why pin or not>"
  },
  "director_note": "<IMPORTANT: write 2-3 sentences explaining WHY you chose this layout. What is the teaching moment? Why does this layout serve the learner best at this exact moment?>",
  "confidence": <0.0-1.0>,
  "decided_by": "llm"
}
```
"""

BOARD_CONTAINER_INSTRUCTIONS = """
## Board Container (MVP)

In addition to the layout fields above, you ALSO output a `script_visibility` section.
The board is a CONTAINER for everything except the instructor. It holds:
- **Script text** — with a visibility_ratio (0.0 to 1.0) controlling how much text shows
- **Keywords** — which keywords from the paragraph should appear as visual badges
- **Assets** — the images/formulas/diagrams placed on the board

### Script Visibility Ratio
Decide how much of the paragraph script text should appear on screen:
- **0.0** — Hidden. For instructor_only moments (greetings, stories, emotional moments)
- **0.2-0.3** — Show key phrases only. When a visual asset is the primary focus
- **0.5** — Half the text. For summaries, balanced moments
- **0.7-0.8** — Most of the text. For complex explanations where reading helps
- **1.0** — Full text. For definitions, formulas, critical steps

### Keyword Visibility
Decide which keywords should appear as visual badges on the board:
- Main keywords → always show
- Key Terms → show when the term is being explained
- Callouts → show briefly to reinforce the point

Include these fields in your JSON output:
```json
"script_visibility": {
    "ratio": 0.5,
    "reasoning": "Show half the text — the image is the primary focus but key terms help"
},
"keyword_visibility": [
    {"word": "cement production", "visible": true, "style": "badge"},
    {"word": "precise journey", "visible": true, "style": "highlight"},
    {"word": "main stages", "visible": false}
]
```
"""

SYSTEM_PROMPT = f"""You are an expert educational video director and layout compositor.

Your job: Given a paragraph from an educational course script, its keywords, available visual assets,
and CONTEXT from previous paragraphs, decide the BEST screen layout to maximize learning impact.

You think like a film director — every layout choice serves the teaching moment. You consider:
- What is the core content of this paragraph? (a formula? an experiment? a narrative?)
- Which assets should appear and when within the paragraph's timespan?
- Should the instructor be prominent or step back?
- How should we transition from the previous layout?
- Should we KEEP the instructor in the same position for visual stability?

You write your reasoning in plain human language that any editor can understand.

{LAYOUT_MODES}

{ASSET_POSITIONS}

{TRANSITION_TYPES}

{CONTINUITY_INSTRUCTIONS}

## Decision Guidelines

1. **Match content to layout**: Formulas and detailed visuals → board_dominant or fullscreen_asset. Storytelling → instructor_dominant or instructor_only. Data analysis → split_50_50 or split_60_40. Multiple visuals → multi_asset_grid.
2. **Asset timing matters**: Don't show all assets at once. Stagger them — introduce the primary asset first, then add supporting assets a few seconds later.
3. **Transitions should be smooth**: Default to fade. Use cut only for dramatic shifts. Use none when instructor is pinned.
4. **Pin the instructor during asset sequences**: If the previous 2-3 paragraphs show board assets and this one does too, keep the instructor in the same position.
5. **director_note is critical**: Write it as if you're explaining to a human editor why you made this choice. Be specific.
6. **display_instruction per asset**: Tell the frontend developer exactly how to render each asset in plain language.
7. **Confidence scoring**: 0.9+ = very obvious choice. 0.7-0.89 = confident but alternatives exist. Below 0.7 = ambiguous, editor should review.
8. **Only use assets from the available_assets list**: Never invent assets that aren't provided.
9. **If no assets are relevant, show fewer or none**: Don't force assets that don't match.

{OUTPUT_SCHEMA}

{BOARD_CONTAINER_INSTRUCTIONS}

CRITICAL: Return ONLY the JSON object. No markdown formatting, no explanation outside the JSON. The director_note field inside the JSON is where your reasoning goes.
"""
