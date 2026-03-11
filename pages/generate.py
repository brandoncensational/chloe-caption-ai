"""pages/generate.py — Caption generation with star ratings and feedback loop."""

import streamlit as st
import json
import base64
from database import (
    get_clients, get_example_counts, save_generation,
    save_rating, update_rating_saved_as, add_example
)
from caption_generator import generate_captions, improve_caption

PLATFORMS = ["Instagram", "TikTok", "Facebook", "LinkedIn", "Twitter/X", "General"]

STAR_OPTIONS = {
    1: "⭐  1 — Poor",
    2: "⭐⭐  2 — Below Average",
    3: "⭐⭐⭐  3 — Decent",
    4: "⭐⭐⭐⭐  4 — Good",
    5: "⭐⭐⭐⭐⭐  5 — Excellent",
}


def _get_user_clients():
    if st.session_state.get("is_master"):
        return get_clients()
    owner_id = st.session_state.get("user", {}).get("id")
    return get_clients(owner_id=owner_id)


def encode_image(uploaded_file):
    data = uploaded_file.read()
    b64 = base64.standard_b64encode(data).decode("utf-8")
    return {"base64": b64, "media_type": uploaded_file.type or "image/jpeg"}


def star_display(rating):
    return "⭐" * rating + "☆" * (5 - rating)


def show():
    st.title("🚀 Generate Captions")

    clients = _get_user_clients()
    if not clients:
        st.warning("No clients yet. Go to **Clients** to add one first.")
        return

    client_map = {c["name"]: c for c in clients}
    selected_name = st.selectbox("Select Client", list(client_map.keys()))
    client = client_map[selected_name]
    client_id = client["id"]

    # AI readiness badge
    counts = get_example_counts(client_id)
    g, b, u = counts.get("good", 0), counts.get("bad", 0), counts.get("used", 0)
    total = g + b + u
    readiness_pct = min(100, total * 5 + g * 3)
    col_info, col_badge = st.columns([3, 1])
    with col_info:
        st.caption(f"Training data: ✅ {g} good  ❌ {b} bad  📌 {u} used")
    with col_badge:
        badge_color = "🟢" if readiness_pct >= 50 else "🟡" if readiness_pct >= 20 else "🔴"
        st.caption(f"{badge_color} AI Readiness: {min(readiness_pct, 100)}%")

    if total < 3:
        st.warning("⚠️ Add at least 3 caption examples in **Examples** for better results.")

    st.divider()

    # ── Generation Form ────────────────────────────────────────────────────────
    with st.form("generate_form"):
        st.subheader("Describe Your Content Batch")
        batch_desc = st.text_area(
            "What photos/videos are in this batch? *",
            placeholder=(
                "Describe each piece of content. Be specific!\n\n"
                "Example:\n"
                "- 3 photos of the new summer dress collection on a white backdrop\n"
                "- 1 boomerang of the owner packing orders at the studio\n"
                "- 1 reel: 15-second try-on of the floral midi dress, upbeat music\n"
                "- 2 behind-the-scenes shots of the team at a photoshoot"
            ),
            height=160,
        )
        col1, col2, col3 = st.columns(3)
        platform = col1.selectbox("Platform", PLATFORMS)
        num_captions = col2.slider("Number of captions", min_value=1, max_value=10, value=5)
        style_note = col3.text_input("Extra instruction (optional)", placeholder="e.g. 'Include a CTA to shop the link in bio'")
        uploaded_images = st.file_uploader(
            "Upload images from the batch (optional)",
            type=["jpg", "jpeg", "png", "webp"],
            accept_multiple_files=True,
        )
        submitted = st.form_submit_button("✨ Generate Captions", type="primary", use_container_width=True)

    # ── Handle generation ──────────────────────────────────────────────────────
    if submitted:
        if not batch_desc.strip():
            st.error("Please describe the content batch.")
            return

        image_data = [encode_image(f) for f in (uploaded_images or [])][:4]

        with st.spinner("🤖 Generating captions..."):
            try:
                results = generate_captions(
                    client_id=client_id,
                    batch_description=batch_desc,
                    platform=platform,
                    num_captions=num_captions,
                    extra_instructions=style_note,
                    image_data=image_data if image_data else None,
                )
                save_generation(
                    client_id=client_id,
                    batch_desc=batch_desc,
                    platform=platform,
                    num_captions=len(results),
                    captions_json=json.dumps(results),
                )
                st.session_state["last_results"]   = results
                st.session_state["last_client_id"] = client_id
                st.session_state["last_platform"]  = platform
                st.session_state["last_batch"]     = batch_desc
                st.session_state["ratings"] = {}
                st.session_state["saved"]   = {}

            except Exception as e:
                st.error(f"Generation failed: {e}")
                if "api_key" in str(e).lower() or "auth" in str(e).lower():
                    st.info("💡 Make sure your ANTHROPIC_API_KEY is set in the .env file.")
                return

    # ── Display Results ────────────────────────────────────────────────────────
    if "last_results" not in st.session_state:
        return

    results        = st.session_state["last_results"]
    last_client_id = st.session_state.get("last_client_id")
    last_platform  = st.session_state.get("last_platform", "Instagram")
    last_batch     = st.session_state.get("last_batch", "")

    if "ratings" not in st.session_state:
        st.session_state["ratings"] = {}
    if "saved" not in st.session_state:
        st.session_state["saved"] = {}

    st.divider()
    st.subheader(f"✨ {len(results)} Generated Captions")
    st.caption("Rate each caption — ratings feed back into the AI to improve future results for this client.")

    for i, cap in enumerate(results, 1):
        caption_text = cap.get("caption", "")
        hashtags     = cap.get("hashtags", "")
        notes        = cap.get("notes", "")
        keywords_used = cap.get("keywords_used", [])
        full_text    = f"{caption_text}\n\n{hashtags}".strip() if hashtags else caption_text
        cap_key      = f"cap_{i}"
        current_rating = st.session_state["ratings"].get(cap_key)
        already_saved  = st.session_state["saved"].get(cap_key)

        header = f"**Caption {i}**"
        if current_rating:
            header += f"  {star_display(current_rating)}"
        if already_saved:
            label_icon = "✅" if already_saved == "good" else "❌"
            header += f"  {label_icon} Saved as {already_saved}"

        with st.expander(header, expanded=(i == 1)):
            st.markdown(caption_text)
            if hashtags:
                st.markdown(f"`{hashtags}`")
            if notes:
                st.caption(f"💡 {notes}")
            if keywords_used:
                st.caption(f"🔑 Keywords: {', '.join(keywords_used)}")

            st.markdown("---")

            col_rate, col_save, col_copy = st.columns([3, 3, 2])

            with col_rate:
                st.markdown("**Rate this caption:**")
                rating_val = st.radio(
                    "Rating",
                    options=[1, 2, 3, 4, 5],
                    format_func=lambda x: star_display(x),
                    index=(current_rating - 1) if current_rating else 2,
                    horizontal=True,
                    key=f"radio_{i}",
                    label_visibility="collapsed",
                )

                r_col1, r_col2 = st.columns(2)
                if r_col1.button("💾 Save Rating", key=f"save_rating_{i}", use_container_width=True):
                    st.session_state["ratings"][cap_key] = rating_val
                    save_rating(
                        client_id=last_client_id,
                        caption_text=caption_text,
                        rating=rating_val,
                        hashtags=hashtags,
                        platform=last_platform,
                        batch_desc=last_batch,
                    )
                    st.success(f"Rating saved: {star_display(rating_val)}")
                    st.rerun()

            with col_save:
                st.markdown("**Add to AI training:**")

                if current_rating:
                    if current_rating >= 4:
                        suggestion = "✅ Looks like a great example!"
                        default_label = "good"
                    elif current_rating <= 2:
                        suggestion = "❌ Good candidate for a bad example."
                        default_label = "bad"
                    else:
                        suggestion = "📌 Save as used or good?"
                        default_label = "used"
                    st.caption(suggestion)
                else:
                    default_label = "good"

                save_label = st.selectbox(
                    "Save as",
                    ["good", "bad", "used"],
                    index=["good", "bad", "used"].index(default_label),
                    key=f"label_{i}",
                    format_func=lambda x: {"good": "✅ Good example", "bad": "❌ Bad example", "used": "📌 Used caption"}[x],
                    label_visibility="collapsed",
                )

                if st.button(
                    "➕ Save to Examples" if not already_saved else f"✔ Saved as {already_saved}",
                    key=f"save_ex_{i}",
                    use_container_width=True,
                    disabled=bool(already_saved),
                ):
                    add_example(
                        client_id=last_client_id,
                        caption=full_text,
                        label=save_label,
                        context=last_batch[:100],
                        platform=last_platform,
                    )
                    update_rating_saved_as(last_client_id, caption_text, save_label)
                    st.session_state["saved"][cap_key] = save_label
                    st.success(f"Saved as **{save_label}** example — AI will learn from this!")
                    st.rerun()

            with col_copy:
                st.markdown("**Copy:**")
                st.code(full_text, language=None)

            # ── Rewrite ────────────────────────────────────────────────────
            with st.form(f"improve_{i}"):
                feedback = st.text_input(
                    "🔄 Request a rewrite",
                    placeholder="e.g. 'Make it shorter' / 'More playful' / 'Add a question'",
                    key=f"feedback_{i}"
                )
                if st.form_submit_button("Rewrite", use_container_width=True):
                    if feedback.strip():
                        with st.spinner("Rewriting..."):
                            improved = improve_caption(last_client_id, caption_text, feedback, last_platform)
                            st.success("**Rewritten:**")
                            st.markdown(improved)
                            st.code(improved)

    # ── Rating summary bar ─────────────────────────────────────────────────────
    saved_ratings = st.session_state["ratings"]
    if saved_ratings:
        st.divider()
        avg = sum(saved_ratings.values()) / len(saved_ratings)
        st.caption(f"📊 This batch: {len(saved_ratings)}/{len(results)} rated  |  Average: {star_display(round(avg))}  ({avg:.1f}/5)")

    # ── Export & Clear ─────────────────────────────────────────────────────────
    st.divider()
    all_captions = "\n\n---\n\n".join(
        f"CAPTION {i}\n{c.get('caption','')}\n{c.get('hashtags','')}"
        for i, c in enumerate(results, 1)
    )
    st.download_button(
        "📥 Download All Captions (.txt)",
        data=all_captions,
        file_name=f"captions_{selected_name.replace(' ', '_')}.txt",
        mime="text/plain",
        use_container_width=True,
    )
    if st.button("🗑️ Clear Results", use_container_width=True):
        for key in ["last_results", "last_client_id", "last_platform", "last_batch", "ratings", "saved"]:
            st.session_state.pop(key, None)
        st.rerun()
