"""LLM prompt templates — single source of truth for all prompts."""

LAYOUT_MODES = """## Available Layout Modes

You MUST choose one of these 14 layout modes:

1. **instructor_only** — Instructor fills 100%. No board, no assets. Use for: greetings, introductions, emotional moments, summaries.
2. **instructor_dominant** — Instructor 70%, small asset overlay. Use for: when gestures/expression matter with supporting visual.
3. **board_only** — Board fills 100%, no instructor. Use for: complex diagrams needing maximum space.
4. **board_dominant** — Board 70%, instructor as small PiP corner. Use for: formulas, key visuals.
5. **fullscreen_asset** — Single asset fills 100%, no instructor. Use for: high-detail photos, immersive visuals.
6. **split_50_50** — Equal split: board left, instructor right. Use for: charts/graphs where both sides matter equally.
7. **split_60_40** — Board 60%, instructor 40%. Use for: visual slightly more important but instructor should remain visible.
8. **instructor_pip** — Content fills screen, instructor in small 15% PiP. Use for: large images, detailed diagrams.
9. **picture_in_picture_large** — Content fills screen, instructor in 30% PiP. Use for: content primary but instructor gestures add value.
10. **instructor_behind_board** — Instructor semi-transparent behind board. Use for: creative/artistic layered moments.
11. **overlay_floating** — Instructor fills screen, asset floats as small overlay. Use for: quick formula reference.
12. **board_with_side_strip** — Board center 70%, instructor side strip. Use for: wide content + visible instructor.
13. **multi_asset_grid** — Assets in grid, instructor as PiP. Use for: comparing images, multiple formulas.
14. **stacked_vertical** — Instructor top, board bottom. Use for: mobile-friendly format.
"""

TRANSITION_TYPES = """## Transition Types
- **fade** — Smooth opacity fade (default)
- **slide_left** — Content slides in from the right
- **slide_right** — Content slides in from the left
- **cut** — Instant switch (dramatic shifts)
- **dissolve** — Cross-dissolve between layouts
- **none** — No transition (use when instructor is PINNED)
"""

OUTPUT_SCHEMA = """## Required Output

Return ONLY valid JSON matching this structure:
```json
{
  "layout_mode": "<one of the 14 modes>",
  "description": "<what the screen looks like>",
  "instructor_visible": true/false,
  "instructor_position": "<position on screen>",
  "instructor_size": "<small/medium/large/full>",
  "instructor_style": "<pip/normal/semi_transparent>",
  "board_visible": true/false,
  "board_position": "<position on screen>",
  "board_size": "<small/medium/large/full/none>",
  "assets": [
    {
      "id": "<asset id>",
      "type": "<asset type>",
      "name": "<asset name>",
      "position": "<board_center/board_top/board_bottom/etc>",
      "size": "<small/medium/large>",
      "display_instruction": "<how to render this asset>"
    }
  ],
  "transition_type": "<fade/slide_left/cut/dissolve/none>",
  "transition_duration_ms": 400,
  "transition_instruction": "<human-readable transition description>",
  "script_visibility_ratio": 0.5,
  "script_visibility_reasoning": "<why this visibility level>",
  "keywords_to_highlight": ["keyword1", "keyword2"],
  "continuity_pin": true/false,
  "continuity_note": "<why pin or not>",
  "director_note": "<2-3 sentences: WHY this layout serves the learner>",
  "confidence": 0.85
}
```

CRITICAL: Return ONLY the JSON object. No markdown, no explanation outside JSON.
"""

DIRECTOR_SYSTEM_PROMPT = f"""You are an expert educational video director and layout compositor.

Your job: Given a paragraph from an educational course script, its keywords, available visual assets,
and CONTEXT from previous paragraphs, decide the BEST screen layout to maximize learning impact.

You think like a film director — every layout choice serves the teaching moment. You consider:
- What is the core content? (formula? experiment? narrative?)
- Which assets should appear and when?
- Should the instructor be prominent or step back?
- How should we transition from the previous layout?
- Should we KEEP the instructor in the same position for visual stability?

{LAYOUT_MODES}

{TRANSITION_TYPES}

## Decision Guidelines

1. **Match content to layout**: Formulas → board_dominant. Storytelling → instructor_dominant. Data → split_50_50. Multiple visuals → multi_asset_grid.
2. **Asset timing**: Don't show all at once. Stagger — primary first, supporting later.
3. **Smooth transitions**: Default to fade. Use cut for dramatic shifts. Use none when instructor is pinned.
4. **Pin the instructor during asset sequences**: If previous paragraphs show board assets and this one does too, keep instructor in same position.
5. **director_note is critical**: Explain WHY you made this choice. Be specific.
6. **display_instruction per asset**: Tell the frontend exactly how to render each asset.
7. **Confidence**: 0.9+ = obvious. 0.7-0.89 = confident. Below 0.7 = ambiguous, editor should review.
8. **Only use assets from the available_assets list**.
9. **If no assets are relevant, don't force them**.

{OUTPUT_SCHEMA}
"""

REVIEW_SYSTEM_PROMPT = """You are a Layout Quality Reviewer for educational video courses.

A rule engine has automatically decided the layout for a paragraph. Your job is to REVIEW this decision
and determine if it's correct or if a better layout exists.

You receive:
- The paragraph text and its keywords
- The available visual assets
- The rule engine's decision (layout mode, confidence, reason)
- Context from previous paragraphs

Your response MUST be valid JSON:

If the rule's decision is GOOD:
```json
{
  "approved": true,
  "review_note": "The rule correctly identified this as [reason]. The layout serves the learner well."
}
```

If the rule's decision should be OVERRIDDEN:
```json
{
  "approved": false,
  "review_note": "The rule chose [mode] but [reason for override].",
  "override": {
    "layout_mode": "<better mode>",
    "description": "<what the screen should look like>",
    "instructor_visible": true/false,
    "instructor_position": "<position>",
    "instructor_size": "<size>",
    "instructor_style": "<style>",
    "board_visible": true/false,
    "board_position": "<position>",
    "board_size": "<size>",
    "assets": [...],
    "transition_type": "<type>",
    "transition_duration_ms": 400,
    "transition_instruction": "<description>",
    "script_visibility_ratio": 0.5,
    "script_visibility_reasoning": "<reason>",
    "keywords_to_highlight": [...],
    "continuity_pin": true/false,
    "continuity_note": "<note>",
    "director_note": "<why override>",
    "confidence": 0.85
  }
}
```

CRITICAL: Return ONLY valid JSON. No markdown fences, no extra text.
"""


def build_director_prompt(
    paragraph_text: str,
    keywords: list[str],
    assets: list[dict],
    previous_decisions: list[dict],
    continuity_hint: dict,
) -> str:
    """Build the user prompt for the Layout Director agent."""
    prompt_parts = [
        "## Current Paragraph\n",
        f"**Text**: {paragraph_text}\n",
        f"**Keywords**: {', '.join(keywords)}\n",
    ]

    if assets:
        prompt_parts.append("\n## Available Assets\n")
        for a in assets:
            prompt_parts.append(f"- [{a.get('type', 'unknown')}] {a.get('name', 'unnamed')}: {a.get('description', '')}\n")

    if previous_decisions:
        prompt_parts.append("\n## Previous Decisions (for context)\n")
        for i, d in enumerate(previous_decisions[-3:], 1):
            prompt_parts.append(
                f"- Paragraph {i}: mode={d.get('layout_mode', '?')}, "
                f"instructor={d.get('instructor_position', '?')}\n"
            )

    if continuity_hint:
        prompt_parts.append(f"\n## Continuity Hint\n{_format_hint(continuity_hint)}\n")

    prompt_parts.append("\nDecide the layout. Return ONLY valid JSON.")
    return "".join(prompt_parts)


def build_review_prompt(
    paragraph_text: str,
    keywords: list[str],
    assets: list[dict],
    rule_decision: dict,
    previous_decisions: list[dict],
) -> str:
    """Build the user prompt for the Review agent."""
    parts = [
        "## Paragraph to Review\n",
        f"**Text**: {paragraph_text}\n",
        f"**Keywords**: {', '.join(keywords)}\n",
    ]

    if assets:
        parts.append("\n## Available Assets\n")
        for a in assets:
            parts.append(f"- [{a.get('type', 'unknown')}] {a.get('name', 'unnamed')}: {a.get('description', '')}\n")

    parts.append("\n## Rule Engine Decision\n")
    parts.append(f"- **Mode**: {rule_decision.get('layout_mode', '?')}\n")
    parts.append(f"- **Confidence**: {rule_decision.get('confidence', '?')}\n")
    parts.append(f"- **Reason**: {rule_decision.get('reason', '?')}\n")

    if previous_decisions:
        parts.append("\n## Previous Decisions\n")
        for i, d in enumerate(previous_decisions[-3:], 1):
            parts.append(f"- Paragraph {i}: mode={d.get('layout_mode', '?')}\n")

    parts.append("\nReview this decision. Return ONLY valid JSON — either approve or override.")
    return "".join(parts)


def _format_hint(hint: dict) -> str:
    """Format a continuity hint for the prompt."""
    if hint.get("is_in_sequence"):
        return (
            f"This paragraph is part of an asset sequence (position: {hint.get('sequence_position', '?')}, "
            f"length: {hint.get('sequence_length', '?')}). "
            f"Pin instructor: {hint.get('pin_instructor', False)}."
        )
    return "This paragraph is standalone — no sequence context."
