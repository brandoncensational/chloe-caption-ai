"""pages/dashboard.py — Home dashboard"""

import streamlit as st
import json
from database import get_stats, get_clients, get_example_counts, add_example


def show():
    st.title("✨ Dashboard")
    st.markdown("Welcome back to **Chloe's Caption AI** — your social media automation hub.")

    stats   = get_stats()
    clients = get_clients()

    # ── Stat Cards ────────────────────────────────────────────────────────────
    col1, col2, col3 = st.columns(3)
    col1.metric("👤 Total Clients",       stats["total_clients"])
    col2.metric("📚 Caption Examples",    stats["total_examples"])
    col3.metric("🚀 Captions Generated",  stats["total_generated"])

    st.divider()

    # ── Quick Actions ─────────────────────────────────────────────────────────
    st.subheader("Quick Actions")
    qa1, qa2, qa3 = st.columns(3)
    with qa1:
        st.markdown("**Add a new client**")
        st.markdown("Set up brand voice, audience, and platforms.")
        if st.button("➕ New Client", use_container_width=True):
            st.session_state["nav_override"] = "Clients"
            st.rerun()
    with qa2:
        st.markdown("**Train the AI**")
        st.markdown("Upload good, bad, and used caption examples.")
        if st.button("📚 Add Examples", use_container_width=True):
            st.session_state["nav_override"] = "Caption Examples"
            st.rerun()
    with qa3:
        st.markdown("**Generate Captions**")
        st.markdown("Describe your batch and get captions instantly.")
        if st.button("🚀 Generate Now", use_container_width=True, type="primary"):
            st.session_state["nav_override"] = "Generate Captions"
            st.rerun()

    st.divider()

    # ── Recent Generation History + Voting ───────────────────────────────────
    st.subheader("📜 Generation History")
    st.caption("Vote on past captions to keep training the AI — every 👍 or 👎 gets saved instantly.")

    recent = stats.get("recent_generations", [])

    if not recent:
        st.info("No captions generated yet. Head to **Generate Captions** to get started!")
    else:
        client_id_map = {c["name"]: c["id"] for c in clients}

        if "history_votes" not in st.session_state:
            st.session_state["history_votes"] = {}

        for row in recent:
            client_name = row["client_name"]
            client_id   = client_id_map.get(client_name)
            batch_desc  = row["batch_desc"]
            platform    = row["platform"]
            created_at  = row["created_at"][:16]
            gen_id      = row["id"] if "id" in row.keys() else created_at

            with st.expander(
                f"**{client_name}** — {created_at}  ·  {platform}  ·  {row['num_captions']} captions",
                expanded=False,
            ):
                st.caption(f"Batch: {batch_desc}")

                if not row["captions_json"]:
                    st.caption("(no caption data saved)")
                    continue

                try:
                    caps = json.loads(row["captions_json"])
                except Exception:
                    st.text(row["captions_json"])
                    continue

                for i, c in enumerate(caps):
                    caption_text = c.get("caption", "")
                    hashtags     = c.get("hashtags", "")
                    cap_title    = c.get("notes", f"Caption {i+1}")
                    vote_key     = f"{gen_id}_{i}"
                    current_vote = st.session_state["history_votes"].get(vote_key)

                    st.markdown(f"**{i+1}. {cap_title}**" if cap_title else f"**{i+1}.**")
                    st.markdown(caption_text)
                    if hashtags:
                        st.caption(hashtags)

                    v1, v2, v3 = st.columns([1, 1, 4])

                    if v1.button("👍", key=f"hist_good_{vote_key}", use_container_width=True,
                                 help="Save as Good example"):
                        st.session_state["history_votes"][vote_key] = "good"
                        if client_id and caption_text:
                            try:
                                add_example(
                                    client_id=client_id,
                                    caption=caption_text,
                                    label="good",
                                    context=f"{cap_title} – {batch_desc}",
                                    platform=platform,
                                    engagement="",
                                )
                                st.toast("✅ Saved as Good example!", icon="✅")
                            except Exception:
                                pass
                        st.rerun()

                    if v2.button("👎", key=f"hist_bad_{vote_key}", use_container_width=True,
                                 help="Save as Bad example"):
                        st.session_state["history_votes"][vote_key] = "bad"
                        if client_id and caption_text:
                            try:
                                add_example(
                                    client_id=client_id,
                                    caption=caption_text,
                                    label="bad",
                                    context=f"{cap_title} – {batch_desc}",
                                    platform=platform,
                                    engagement="",
                                )
                                st.toast("❌ Saved as Bad example!", icon="❌")
                            except Exception:
                                pass
                        st.rerun()

                    if current_vote:
                        v3.success(f"{'👍 Good' if current_vote == 'good' else '👎 Bad'} — saved")

                    st.markdown("---")

    # ── Client Overview ───────────────────────────────────────────────────────
    if clients:
        st.divider()
        st.subheader("Your Clients")
        for c in clients:
            counts    = get_example_counts(c["id"])
            g         = counts.get("good", 0)
            b         = counts.get("bad",  0)
            u         = counts.get("used", 0)
            readiness = min(100, int((g * 3 + u * 2 + b) / max(1, g+b+u+1) * 20 + (g+b+u) * 4))
            st.markdown(
                f"**{c['name']}** — {c.get('industry','Unknown industry')}  "
                f"| ✅ {g} good  ❌ {b} bad  📌 {u} used  "
                f"| 🧠 AI Readiness: {min(readiness,100)}%"
            )
