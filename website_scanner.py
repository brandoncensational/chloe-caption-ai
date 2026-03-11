"""
website_scanner.py — Scan a website URL and extract brand data using AI.

Scrapes HTML for text content, meta tags, CSS colors/fonts, then sends to Claude
for deep brand voice analysis. Returns structured brand profile data.
"""

import os
import re
import json
import requests
from bs4 import BeautifulSoup
import anthropic


def scrape_website(url: str) -> dict:
    """
    Fetch and parse a website URL. Extracts:
    - Page title, meta description, og:tags
    - Main body text (first ~3000 chars)
    - CSS colors and fonts found in inline styles and <style> tags
    - Headings (h1, h2, h3)
    - Links/nav items for context

    Returns a dict with all extracted data.
    """
    if not url.startswith(("http://", "https://")):
        url = "https://" + url

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                       "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }

    try:
        resp = requests.get(url, headers=headers, timeout=15, allow_redirects=True)
        resp.raise_for_status()
    except requests.RequestException as e:
        raise ValueError(f"Could not fetch {url}: {e}")

    soup = BeautifulSoup(resp.text, "html.parser")

    # ── Meta tags ──────────────────────────────────────────────────────────
    title = ""
    title_tag = soup.find("title")
    if title_tag:
        title = title_tag.get_text(strip=True)

    meta_desc = ""
    meta_tag = soup.find("meta", attrs={"name": "description"})
    if meta_tag:
        meta_desc = meta_tag.get("content", "")

    og_title = ""
    og_tag = soup.find("meta", attrs={"property": "og:title"})
    if og_tag:
        og_title = og_tag.get("content", "")

    og_desc = ""
    og_desc_tag = soup.find("meta", attrs={"property": "og:description"})
    if og_desc_tag:
        og_desc = og_desc_tag.get("content", "")

    og_image = ""
    og_img_tag = soup.find("meta", attrs={"property": "og:image"})
    if og_img_tag:
        og_image = og_img_tag.get("content", "")

    # ── Headings ──────────────────────────────────────────────────────────
    headings = []
    for level in ["h1", "h2", "h3"]:
        for h in soup.find_all(level)[:10]:
            text = h.get_text(strip=True)
            if text and len(text) < 200:
                headings.append(f"[{level}] {text}")

    # ── Body text ─────────────────────────────────────────────────────────
    # Remove script, style, nav, footer to get main content
    for tag in soup.find_all(["script", "style", "nav", "footer", "header", "noscript"]):
        tag.decompose()

    body_text = soup.get_text(separator=" ", strip=True)
    # Clean up whitespace
    body_text = re.sub(r'\s+', ' ', body_text)[:3000]

    # ── CSS Colors ────────────────────────────────────────────────────────
    colors = set()
    fonts = set()

    # From inline styles
    style_tags = soup.find_all("style")
    css_text = " ".join(tag.get_text() for tag in style_tags)
    # Also check inline style attributes
    for elem in soup.find_all(style=True)[:50]:
        css_text += " " + elem.get("style", "")

    # Extract hex colors
    hex_colors = re.findall(r'#(?:[0-9a-fA-F]{3}){1,2}\b', css_text)
    colors.update(hex_colors[:20])

    # Extract rgb/rgba colors
    rgb_colors = re.findall(r'rgba?\(\s*\d+\s*,\s*\d+\s*,\s*\d+(?:\s*,\s*[\d.]+)?\s*\)', css_text)
    colors.update(rgb_colors[:10])

    # Extract font-family declarations
    font_matches = re.findall(r'font-family\s*:\s*([^;}{]+)', css_text)
    for fm in font_matches[:10]:
        # Clean up and get first font in the stack
        clean = fm.strip().strip("'\"").split(",")[0].strip().strip("'\"")
        if clean and len(clean) < 50:
            fonts.add(clean)

    # ── Navigation / links context ────────────────────────────────────────
    nav_items = []
    for nav in soup.find_all("nav"):
        for link in nav.find_all("a")[:15]:
            text = link.get_text(strip=True)
            if text and len(text) < 60:
                nav_items.append(text)

    return {
        "url": url,
        "title": title,
        "meta_description": meta_desc,
        "og_title": og_title,
        "og_description": og_desc,
        "og_image": og_image,
        "headings": headings[:15],
        "body_text": body_text,
        "colors": list(colors)[:15],
        "fonts": list(fonts)[:8],
        "nav_items": nav_items[:15],
    }


def analyze_brand_with_ai(scraped_data: dict) -> dict:
    """
    Send scraped website data to Claude for deep brand analysis.

    Returns a dict with:
    - business_name, industry, brand_voice, target_audience,
      tagline, platforms_suggested, colors, fonts, notes
    """
    client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

    prompt = f"""Analyze this website data and extract a complete brand profile.

WEBSITE: {scraped_data.get('url', '')}
PAGE TITLE: {scraped_data.get('title', '')}
META DESCRIPTION: {scraped_data.get('meta_description', '')}
OG TITLE: {scraped_data.get('og_title', '')}
OG DESCRIPTION: {scraped_data.get('og_description', '')}

HEADINGS FOUND:
{chr(10).join(scraped_data.get('headings', ['(none)']))}

NAVIGATION ITEMS:
{', '.join(scraped_data.get('nav_items', ['(none)']))}

COLORS DETECTED IN CSS:
{', '.join(scraped_data.get('colors', ['(none)']))}

FONTS DETECTED:
{', '.join(scraped_data.get('fonts', ['(none)']))}

BODY TEXT (first 3000 chars):
{scraped_data.get('body_text', '(none)')[:3000]}

---

Based on ALL of the above, extract a comprehensive brand profile. Respond ONLY with a JSON object (no markdown fences, no explanation) with these exact fields:

{{
  "business_name": "The business/brand name",
  "industry": "Their industry or niche (e.g. 'Vacation Rentals', 'E-commerce Fashion', 'SaaS')",
  "brand_voice": "A detailed 2-3 sentence description of how this brand speaks. Include tone (warm, professional, edgy, etc.), style (casual, formal, storytelling), and any distinctive patterns you notice in their writing.",
  "target_audience": "Who this business is trying to reach. Be specific about demographics, interests, and pain points based on the content.",
  "tagline": "Their tagline or slogan if found, or suggest one based on their positioning",
  "platforms_suggested": ["Instagram", "TikTok", "Facebook"],
  "colors": ["#hex1", "#hex2", "#hex3"],
  "fonts": ["Font Name 1", "Font Name 2"],
  "notes": "Any additional observations about the brand that would help generate better social media content for them. Mention seasonal relevance, unique selling points, competitive positioning, etc."
}}

Be thorough and specific. The brand voice description is the MOST important field — it will be used to train an AI caption generator, so make it detailed enough that someone could write in this brand's voice just by reading your description."""

    response = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=1500,
        messages=[{"role": "user", "content": prompt}]
    )

    raw = response.content[0].text.strip()
    # Strip markdown fences if present
    if raw.startswith("```"):
        raw = re.sub(r"^```[a-z]*\n?", "", raw)
        raw = re.sub(r"\n?```$", "", raw)
    raw = raw.strip()

    try:
        result = json.loads(raw)
    except json.JSONDecodeError:
        # Try to extract JSON object
        match = re.search(r'\{.*\}', raw, re.DOTALL)
        if match:
            result = json.loads(match.group(0))
        else:
            result = {
                "business_name": scraped_data.get("title", ""),
                "industry": "",
                "brand_voice": raw[:500],
                "target_audience": "",
                "tagline": "",
                "platforms_suggested": ["Instagram", "Facebook"],
                "colors": scraped_data.get("colors", [])[:5],
                "fonts": scraped_data.get("fonts", [])[:3],
                "notes": "AI analysis returned non-JSON. Raw text saved in brand_voice field.",
            }

    return result


def scan_website(url: str) -> dict:
    """
    Full pipeline: scrape URL → AI analysis → structured brand profile.

    This is the main function to call from the UI.
    Returns the AI-analyzed brand profile dict.
    """
    scraped = scrape_website(url)
    profile = analyze_brand_with_ai(scraped)
    # Attach raw scraped data for reference
    profile["_scraped"] = {
        "url": scraped["url"],
        "og_image": scraped.get("og_image", ""),
    }
    return profile
