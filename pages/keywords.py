"""pages/keywords.py — Manage per-client brand keywords"""

import streamlit as st
from database import (
    get_clients, get_keywords, add_keyword, add_keywords_bulk,
    update_keyword, delete_keyword, get_keyword_stats
)

CATEGORIES = ["general", "brand", "product", "vibe", "cta", "seasonal", "hashtag"]
PRIORITY_LABELS = {
    "high":   "🔴 High — in every caption",
    "normal": "🟡 Normal — rotate across captions",
    "low":    "🟢 Low — occasional use only",
}


def _get_user_clients():
    if st.session_state.get("is_master"):
        return get_clients()
    owner_id = st.session_state.get("user", {}).get("id")
    return get_clients(owner_id=owner_id)


def show():
    st.title("🔑 Brand Keywords")
    st.markdown(
        "Keywords are woven naturally into captions. "
        "The AI rotates them across a batch to avoid repetition — "
        "high-priority words appear most often, low-priority ones only occasionally."
    )

    clients = _get_user_clients()
    if not clients:
        st.warning("No clients yet. Add one in **Clients** first.")
        return

    client_map = {c["name"]: c for c in clients}
    selected_name = st.selectbox("Select Client", list(client_map.keys()))
    client_id = client_map[selected_name]["id"]

    keywords = get_keywords(client_id)
    stats    = get_keyword_stats(client_id)
    stats_map = {s["keyword"]: s for s in stats}

    # ── Summary ───────────────────────────────────────────────────────────────
    high    = sum(1 for k in keywords if k["priority"] == "high")
    normal  = sum(1 for k in keywords if k["priority"] == "normal")
    low     = sum(1 for k in keywords if k["priority"] == "low")

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Keywords", len(keywords))
    c2.metric("🔴 High", high)
    c3.metric("🟡 Normal", normal)
    c4.metric("🟢 Low", low)

    if keywords:
        total_uses = sum(k.get("use_count", 0) for k in keywords)
        st.caption(f"These keywords have been included in captions **{total_uses}** times total across all generations.")

    st.divider()

    tabs = st.tabs(["➕ Add Keywords", "📋 Manage Keywords", "📊 Usage Stats"])

    # ── Add Keywords ──────────────────────────────────────────────────────────
    with tabs[0]:
        st.subheader("Add Keywords")

        with st.form("add_keywords_form"):
            col_a, col_b = st.columns(2)
            with col_a:
                priority = st.radio(
                    "Priority",
                    ["high", "normal", "low"],
                    format_func=lambda x: PRIORITY_LABELS[x],
                )
            with col_b:
                category = st.selectbox("Category", CATEGORIES)

            kw_input = st.text_area(
                "Keywords *",
                placeholder=(
                    "Enter one keyword or phrase per line.\n\n"
                    "Examples:\n"
                    "sustainable\n"
                    "handcrafted\n"
                    "shop the look\n"
                    "made with love\n"
                    "small business"
                ),
                height=160
            )
            st.caption("Keywords can be single words OR short phrases like 'shop the link in bio'.")

            submitted = st.form_submit_button("Save Keywords", type="primary", use_container_width=True)

        if submitted:
            if not kw_input.strip():
                st.error("Please enter at least one keyword.")
            else:
                keyword_list = [k.strip() for k in kw_input.strip().split("\n") if k.strip()]
                added, skipped = add_keywords_bulk(client_id, keyword_list, category, priority)
                if added:
                    st.success(f"✅ Added {added} keyword{'s' if added > 1 else ''}!")
                if skipped:
                    st.info(f"⚠️ {skipped} keyword{'s' if skipped > 1 else ''} already existed and were skipped.")
                st.rerun()

        with st.expander("💡 Tips for great keywords"):
            st.markdown("""
**High priority** — Core brand words that define the business. Examples:
- Brand name, tagline words, core product category

**Normal priority** — Descriptive words that rotate in naturally. Examples:
- `handmade`, `sustainable`, `limited edition`, `bestseller`, `new arrival`

**Low priority** — CTAs and seasonal phrases used sparingly. Examples:
- `shop now`, `link in bio`, `DM to order`, `this season`

**Categories** help you organize:
- `brand` — identity words unique to the client
- `product` — product names or categories
- `vibe` — mood/aesthetic words
- `cta` — calls to action
- `seasonal` — time-limited keywords
- `hashtag` — words you want to appear as hashtags
""")

    # ── Manage Existing ───────────────────────────────────────────────────────
    with tabs[1]:
        if not keywords:
            st.info("No keywords yet. Add some in the **Add Keywords** tab.")
        else:
            for priority_key, priority_label in [("high","🔴 High Priority"), ("normal","🟡 Normal Priority"), ("low","🟢 Low / Occasional")]:
                group = [k for k in keywords if k["priority"] == priority_key]
                if not group:
                    continue
                st.subheader(priority_label)
                for kw in group:
                    col_kw, col_cat, col_pri, col_del = st.columns([3, 2, 2, 1])
                    col_kw.markdown(f"**{kw['keyword']}**")
                    col_cat.caption(kw.get("category", "general"))

                    new_pri = col_pri.selectbox(
                        "Priority",
                        ["high", "normal", "low"],
                        index=["high","normal","low"].index(kw["priority"]),
                        key=f"pri_{kw['id']}",
                        label_visibility="collapsed"
                    )
                    if new_pri != kw["priority"]:
                        update_keyword(kw["id"], priority=new_pri)
                        st.rerun()

                    if col_del.button("🗑️", key=f"del_kw_{kw['id']}", help="Delete"):
                        delete_keyword(kw["id"])
                        st.rerun()
                st.divider()

    # ── Usage Stats ───────────────────────────────────────────────────────────
    with tabs[2]:
        if not stats:
            st.info("No usage data yet — generate some captions first!")
        else:
            st.subheader("Keyword Usage History")
            st.caption("Tracks how often each keyword has been included in generated captions.")

            for s in stats:
                last = s.get("last_used", "Never")
                if last and last != "Never":
                    last = last[:10]
                recent = s.get("recent_uses", 0)
                total  = s.get("use_count", 0)

                col_name, col_total, col_recent, col_last = st.columns([3, 1, 2, 2])
                col_name.markdown(f"**{s['keyword']}** — `{s.get('category','general')}` `{s.get('priority','normal')}`")
                col_total.metric("Total", total, label_visibility="collapsed")
                col_recent.caption(f"Last 30 days: {recent}x")
                col_last.caption(f"Last used: {last}")
