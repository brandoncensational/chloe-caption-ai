"""
caption_generator.py — AI caption engine
Uses Anthropic's Claude with per-client few-shot examples + smart keyword rotation.
"""

import os
import json
import re
import anthropic
from database import get_client, get_examples, get_keywords_for_generation, record_keyword_usage

_client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

PLATFORM_GUIDANCE = {
    "Instagram": "Use 3-10 relevant hashtags at the end. Tone can be aspirational and visual. Up to 2,200 chars.",
    "TikTok":    "Keep it punchy, trend-aware, and conversational. 1-5 hashtags. Under 300 chars is ideal.",
    "Facebook":  "More conversational, can be longer. Storytelling works well. Hashtags optional.",
    "LinkedIn":  "Professional yet human. Tell a story or share a lesson. 3 hashtags max.",
    "Twitter/X": "Concise and punchy. Under 280 characters. Emojis optional.",
    "General":   "Engaging and on-brand. Use hashtags as appropriate.",
}


def build_system_prompt(client, examples, keywords):
    good_examples = [e for e in examples if e["label"] == "good"]
    bad_examples  = [e for e in examples if e["label"] == "bad"]
    used_examples = [e for e in examples if e["label"] == "used"]

    def fmt_examples(exs, limit=6):
        if not exs:
            return "  (none yet)"
        lines = []
        for e in exs[:limit]:
            ctx = f" [context: {e['context']}]" if e.get("context") else ""
            eng = f" [engagement: {e['engagement']}]" if e.get("engagement") else ""
            lines.append(f'  * "{e["caption"]}"{ctx}{eng}')
        return "\n".join(lines)

    always_kws     = keywords.get("always", [])
    rotate_kws     = keywords.get("rotate", [])
    occasional_kws = keywords.get("occasional", [])
    kw_section = ""

    if always_kws or rotate_kws or occasional_kws:
        kw_section = "\n## BRAND KEYWORDS\nWeave these naturally into captions. Never force them or repeat the same keyword across multiple captions in the same batch.\n\n"
        if always_kws:
            kw_section += f"HIGH PRIORITY - include in every caption if possible:\n   {', '.join(always_kws)}\n\n"
        if rotate_kws:
            kw_section += f"ROTATE - spread across captions, max 1-2 per caption, no repeats:\n   {', '.join(rotate_kws)}\n\n"
        if occasional_kws:
            kw_section += f"OCCASIONAL - use only 1-2 across the entire batch:\n   {', '.join(occasional_kws)}\n\n"
        kw_section += (
            "KEYWORD RULES:\n"
            "* Each keyword should appear in AT MOST 2 captions per batch\n"
            "* Spread different keywords across captions so they each feel distinct\n"
            "* Keywords must feel like a natural part of the sentence\n"
            "* If a keyword does not fit a caption naturally, skip it\n"
            "* Include a 'keywords_used' array in your JSON response\n"
        )

    return f"""You are an expert social media copywriter for {client['name']}.

## CLIENT PROFILE
- Industry: {client.get('industry', 'Not specified')}
- Brand Voice: {client.get('brand_voice', 'Not specified')}
- Target Audience: {client.get('target_audience', 'Not specified')}
- Active Platforms: {client.get('platforms', 'Not specified')}
- Notes: {client.get('notes', 'None')}
{kw_section}
## CAPTION STYLE REFERENCE

GREAT CAPTIONS (emulate these):
{fmt_examples(good_examples)}

BAD CAPTIONS (avoid these patterns):
{fmt_examples(bad_examples)}

RECENTLY USED (match voice, never repeat):
{fmt_examples(used_examples)}

Generate compelling captions that match brand voice, fit the platform, feel fresh, vary in structure, and include brand keywords naturally with minimal repetition across captions.

Always respond with a valid JSON array of caption objects."""


def extract_used_keywords(results, all_keywords):
    used = []
    all_kw_words = [kw["keyword"].lower() for kw in all_keywords] if all_keywords and isinstance(all_keywords[0], dict) else [k.lower() for k in all_keywords]
    for cap_obj in results:
        text = (cap_obj.get("caption", "") + " " + cap_obj.get("hashtags", "")).lower()
        ai_reported = [k.lower() for k in cap_obj.get("keywords_used", [])]
        for kw in all_kw_words:
            pattern = r'\b' + re.escape(kw) + r'\b'
            if re.search(pattern, text) or kw in ai_reported:
                if kw not in used:
                    used.append(kw)
    return used


def generate_captions(client_id, batch_description, platform="Instagram",
                      num_captions=5, extra_instructions="", image_data=None):
    client = get_client(client_id)
    if not client:
        raise ValueError(f"Client ID {client_id} not found.")

    examples = get_examples(client_id)
    keywords = get_keywords_for_generation(client_id, num_captions)
    system_prompt = build_system_prompt(client, examples, keywords)
    platform_tip = PLATFORM_GUIDANCE.get(platform, PLATFORM_GUIDANCE["General"])

    user_message_text = f"""## CONTENT BATCH DESCRIPTION
{batch_description}

## PLATFORM
{platform} - {platform_tip}

## TASK
Generate exactly {num_captions} unique captions for this batch.
{f'Additional instructions: {extra_instructions}' if extra_instructions else ''}

Respond ONLY with a JSON array - no markdown fences, no extra text:
[
  {{
    "caption": "Full caption text including emojis if appropriate",
    "hashtags": "#tag1 #tag2 #tag3",
    "notes": "Brief note: why this works / which content piece it suits best",
    "keywords_used": ["keyword1", "keyword2"]
  }}
]"""

    content = [{"type": "text", "text": user_message_text}]
    if image_data:
        for img in (image_data or [])[:4]:
            content.append({
                "type": "image",
                "source": {"type": "base64", "media_type": img["media_type"], "data": img["base64"]}
            })

    response = _client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=2048,
        system=system_prompt,
        messages=[{"role": "user", "content": content}]
    )

    raw = response.content[0].text.strip()
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    raw = raw.strip()

    try:
        results = json.loads(raw)
    except json.JSONDecodeError:
        results = [{"caption": raw, "hashtags": "", "notes": "Raw output - JSON parse failed", "keywords_used": []}]

    # Record which keywords were used for rotation tracking
    all_kws = keywords.get("all", [])
    if all_kws:
        used_keywords = extract_used_keywords(results, all_kws)
        for kw in used_keywords:
            record_keyword_usage(client_id, kw)

    return results


def improve_caption(client_id, original_caption, feedback, platform="Instagram"):
    client = get_client(client_id)
    examples = get_examples(client_id)
    keywords = get_keywords_for_generation(client_id, 1)
    system_prompt = build_system_prompt(client, examples, keywords)

    user_msg = f"""Rewrite this caption based on the feedback.

Original: "{original_caption}"
Feedback: {feedback}
Platform: {platform}

Respond with ONLY the improved caption text."""

    response = _client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=512,
        system=system_prompt,
        messages=[{"role": "user", "content": user_msg}]
    )
    return response.content[0].text.strip()


# ─────────────────────────────────────────────────────────────────────────────
# FULL BATCH PLANNER
# Plans AND writes all posts for an entire monthly content batch in one shot.
# ─────────────────────────────────────────────────────────────────────────────

KATIE_BATCH_STRUCTURE = """
Katie's fixed monthly content structure (10 posts total):

BRANDED PROPERTY POSTS (6 posts — 2 per property):
  1. Tipis on the Guadalupe (TOTG) — Reel
  2. Tipis on the Guadalupe (TOTG) — Carousel
  3. Calm Water Rentals (CWR) — Reel
  4. Calm Water Rentals (CWR) — Carousel
  5. River Road Escapes (RRE) — Reel
  6. River Road Escapes (RRE) — Carousel

KATIE-FOCUSED POSTS (4 posts — posted across all 3 accounts):
  7. Katie Post #1 — Reel or Static (your choice based on what feels right)
  8. Katie Post #2 — Reel or Static
  9. Katie Post #3 — Reel or Static
  10. Katie Post #4 — Reel or Static

PROPERTY GUIDE:
- TOTG (Tipis on the Guadalupe): glamping tipis on the Guadalupe River in Texas Hill Country. 
  Romantic, adventurous, nature-immersed. Tipi accommodations with river access, kayak rentals, 
  glamping amenities. Great for couples, families, Spring Break, weekend getaways.
- CWR (Calm Water Rentals): retreat cabins on the river. More intimate/romantic. 
  Couples getaways, cozy stays, riverside romance, peaceful escapes.
- RRE (River Road Escapes): fishing cabins. Fishing-focused, family adventures, 
  full-house rentals, rustic comfort. Up to 18 guests in the full house.
- Katie-focused: Personal brand posts featuring Katie Riedel (women-owned business owner). 
  Behind-the-scenes, personal stories, guest reactions, morning reflections, 
  her love for the properties. Builds trust and personal connection with audience.
"""

def plan_full_batch(client_id: int, month: str, year: str,
                    extra_context: str = "") -> list[dict]:
    """
    Generate a complete 10-post batch plan WITH captions, hooks, and image prompts.

    Returns a list of 10 dicts:
    {
      "post_num": 1,
      "account": "Tipis on the Guadalupe (TOTG)",
      "post_type": "Reel",          # Reel | Carousel | Static Post
      "is_video": True,             # True for Reels
      "is_katie": False,
      "title": "Spring Break Starts Here",
      "angle": "...",               # The creative concept/angle
      "caption": "...",             # Full caption text
      "hashtags": "#tag1 #tag2",
      "reel_hook": "...",           # One-liner on-screen text (Reels only)
      "image_prompt": "...",        # Description of ideal images (Carousel/Static)
      "video_direction": "...",     # Direction notes for video (Reels)
    }
    """
    from database import get_client, get_examples, get_keywords_for_generation, get_posting_schedule
    import json as _json

    client   = get_client(client_id)
    if not client:
        raise ValueError(f"Client {client_id} not found")

    examples  = get_examples(client_id)
    keywords  = get_keywords_for_generation(client_id, 10)
    schedule  = get_posting_schedule(client_id)

    good_ex  = [e for e in examples if e["label"] == "good"][:8]
    used_ex  = [e for e in examples if e["label"] == "used"][:15]
    bad_ex   = [e for e in examples if e["label"] == "bad"][:4]

    def fmt_ex(exs):
        if not exs: return "  (none)"
        return "\n".join(
            f'  • [{e.get("context","no context")}]: "{e["caption"][:200]}"'
            for e in exs
        )

    kw_list = (
        keywords.get("always", []) +
        keywords.get("rotate", []) +
        keywords.get("occasional", [])
    )

    schedule_notes = schedule.get("notes", "")
    proposal_text  = schedule.get("proposal", "")[:800]

    system_prompt = f"""You are an expert social media content strategist and copywriter 
for {client['name']}, a women-owned vacation rental business in the Texas Hill Country.

{KATIE_BATCH_STRUCTURE}

CLIENT PROFILE:
- Brand Voice: {client.get('brand_voice', 'Warm, personal, inviting, nature-focused')}
- Target Audience: {client.get('target_audience', 'Couples, families, adventure-seekers, Texas travelers')}
- Notes: {client.get('notes', '')}
- Schedule Notes: {schedule_notes}

GREAT CAPTION EXAMPLES (emulate this style, voice, structure):
{fmt_ex(good_ex)}

RECENTLY USED CAPTIONS (never repeat these themes or phrases):
{fmt_ex(used_ex)}

BAD CAPTIONS (avoid these patterns):
{fmt_ex(bad_ex)}

KEYWORDS TO WEAVE IN NATURALLY (spread across posts, don't force):
{', '.join(kw_list) if kw_list else 'None set yet'}

Your job: Plan and write ALL 10 posts for {month} {year}.
Respond ONLY with a valid JSON array — no markdown, no explanation, just the JSON."""

    user_msg = f"""Generate the complete {month} {year} content batch — all 10 posts.

Month context: Think carefully about what {month} means for Texas Hill Country vacation rentals. 
What are guests thinking about? What seasonal angles, holidays, or events are relevant? 
What would make someone stop scrolling and book a stay right now?

{f'Additional context: {extra_context}' if extra_context else ''}

For each of the 10 posts, return a JSON object with these exact fields:
{{
  "post_num": 1,
  "account": "Tipis on the Guadalupe (TOTG)",
  "post_type": "Reel",
  "is_video": true,
  "is_katie": false,
  "title": "Short punchy title for this post",
  "angle": "1-2 sentences: the creative concept/story angle for this post",
  "caption": "The complete, ready-to-post caption with emojis and everything",
  "hashtags": "#hashtag1 #hashtag2 #hashtag3",
  "reel_hook": "ONE short punchy line for on-screen reel text — a hook/question that stops the scroll. Only for Reels, empty string for others.",
  "image_prompt": "Description of what images would be perfect for this post — what should they show, what mood/lighting/subjects. Only for Carousel and Static posts, empty string for Reels.",
  "video_direction": "Brief direction notes for what the 15-19 second reel should show. Only for Reels, empty string for others."
}}

Rules:
- Each post MUST have a unique angle — no two posts should feel similar
- Captions should vary in length and structure — mix short punchy ones with longer storytelling ones
- Katie posts should feel personal and authentic, like she's speaking directly to her audience
- Reel hooks must be <= 8 words, captivating, make someone want to stop and watch
- Seasonal/timely content for {month} should feel fresh and relevant
- Hashtags: 8-12 per post, mix of brand (#TipisOnTheGuadalupe etc) and discovery tags
- Return exactly 10 objects in the array, in the order: TOTG Reel, TOTG Carousel, CWR Reel, CWR Carousel, RRE Reel, RRE Carousel, then 4 Katie posts"""

    response = _client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=8000,
        system=system_prompt,
        messages=[{"role": "user", "content": user_msg}]
    )

    raw = response.content[0].text.strip()
    # Strip markdown fences
    if raw.startswith("```"):
        raw = re.sub(r"^```[a-z]*\n?", "", raw)
        raw = re.sub(r"\n?```$", "", raw)
    raw = raw.strip()

    try:
        posts = _json.loads(raw)
    except _json.JSONDecodeError as e:
        # Try to extract JSON array if there's surrounding text
        match = re.search(r'\[.*\]', raw, re.DOTALL)
        if match:
            posts = _json.loads(match.group(0))
        else:
            raise ValueError(f"AI returned invalid JSON: {e}\n\nRaw: {raw[:500]}")

    # Record keyword usage
    all_kws = keywords.get("all", [])
    if all_kws:
        from database import record_keyword_usage
        used_keywords = extract_used_keywords(posts, all_kws)
        for kw in used_keywords:
            record_keyword_usage(client_id, kw)

    return posts
