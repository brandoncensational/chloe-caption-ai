"""pages/examples.py — Manage good/bad/used caption examples (AI training data)"""

import streamlit as st
from database import get_clients, add_example, get_examples, delete_example, relabel_example


LABEL_INFO = {
    "good":  ("✅ Good Examples", "green",  "Captions that performed well or perfectly match the brand voice. The AI will emulate these."),
    "bad":   ("❌ Bad Examples",  "red",    "Captions that flopped, felt off-brand, or got negative feedback. The AI will avoid these patterns."),
    "used":  ("📌 Used Captions", "blue",   "Captions that were actually posted. Helps the AI understand the voice and avoid exact repeats."),
}


def show():
    st.title("📚 Caption Examples")
    st.markdown("These examples train the AI for each client. The more examples you add, the better the output.")

    clients = get_clients()
    if not clients:
        st.warning("No clients yet. Add one in **Client Management** first.")
        return

    client_names = {c["name"]: c["id"] for c in clients}
    selected_name = st.selectbox("Select Client", list(client_names.keys()))
    client_id = client_names[selected_name]

    # ── Summary counts ─────────────────────────────────────────────────────────
    all_examples = get_examples(client_id)
    good_count = sum(1 for e in all_examples if e["label"] == "good")
    bad_count  = sum(1 for e in all_examples if e["label"] == "bad")
    used_count = sum(1 for e in all_examples if e["label"] == "used")

    m1, m2, m3 = st.columns(3)
    m1.metric("✅ Good", good_count)
    m2.metric("❌ Bad",  bad_count)
    m3.metric("📌 Used", used_count)

    if good_count + bad_count + used_count < 5:
        st.info("💡 **Tip:** Add at least 3–5 good examples and 2–3 bad examples to get significantly better AI output.")

    st.divider()
    tabs = st.tabs(["➕ Add Example", "✅ Good", "❌ Bad", "📌 Used"])

    # ── Add Example Tab ────────────────────────────────────────────────────────
    with tabs[0]:
        st.subheader("Add a Caption Example")
        with st.form("add_example_form"):
            label = st.radio(
                "Example Type",
                ["good", "bad", "used"],
                format_func=lambda x: LABEL_INFO[x][0],
                horizontal=True,
            )
            st.caption(LABEL_INFO[label][2])

            caption = st.text_area(
                "Caption *",
                placeholder="Paste the full caption here, exactly as written (including hashtags if any)..."
            )
            context = st.text_input(
                "Context (optional)",
                placeholder="e.g. 'Reel of a summer sale flat-lay' or 'Product launch post'"
            )
            platform = st.selectbox("Platform", ["Instagram", "TikTok", "Facebook", "LinkedIn", "Twitter/X", "General"])
            engagement = st.text_input(
                "Engagement (optional)",
                placeholder="e.g. '1,240 likes, 87 comments' — helps AI know what worked"
            )

            bulk_mode = st.checkbox("Bulk add (one caption per line)")
            submitted = st.form_submit_button("Save Example", type="primary")

        if submitted:
            if not caption.strip():
                st.error("Caption text is required.")
            else:
                if bulk_mode:
                    captions = [c.strip() for c in caption.split("\n") if c.strip()]
                    for cap in captions:
                        add_example(client_id, cap, label, context, platform, engagement)
                    st.success(f"✅ Added {len(captions)} examples!")
                else:
                    add_example(client_id, caption.strip(), label, context, platform, engagement)
                    st.success("✅ Example saved!")
                st.rerun()

    # ── View / Relabel / Delete Tabs ───────────────────────────────────────────
    for i, lbl in enumerate(["good", "bad", "used"], start=1):
        with tabs[i]:
            title, color, desc = LABEL_INFO[lbl]
            st.subheader(title)
            st.caption(desc)

            examples = get_examples(client_id, label=lbl)
            if not examples:
                st.info(f"No {lbl} examples yet. Add some using the **Add Example** tab.")
                continue

            for ex in examples:
                with st.container():
                    col_text, col_actions = st.columns([5, 2])

                    with col_text:
                        st.markdown(f"> {ex['caption'][:300]}{'...' if len(ex['caption']) > 300 else ''}")
                        meta_parts = []
                        if ex.get("platform"):
                            meta_parts.append(f"📱 {ex['platform']}")
                        if ex.get("context"):
                            meta_parts.append(f"📷 {ex['context'][:60]}")
                        if ex.get("engagement"):
                            meta_parts.append(f"📊 {ex['engagement']}")
                        if meta_parts:
                            st.caption("  ·  ".join(meta_parts))

                    with col_actions:
                        other_labels = [l for l in ["good", "bad", "used"] if l != lbl]
                        icons = {"good": "✅ Good", "bad": "❌ Bad", "used": "📌 Used"}
                        for target in other_labels:
                            if st.button(
                                f"→ {icons[target]}",
                                key=f"relabel_{ex['id']}_{target}",
                                use_container_width=True,
                            ):
                                relabel_example(ex["id"], target)
                                st.toast(f"Moved to {target}!", icon="✅")
                                st.rerun()

                        if st.button("🗑️ Delete", key=f"del_ex_{ex['id']}", use_container_width=True):
                            delete_example(ex["id"])
                            st.rerun()

                    st.markdown("---")
