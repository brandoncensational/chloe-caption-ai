"""pages/clients.py — Add and manage clients including posting schedules and website scanning."""

import streamlit as st
import json
from database import (
    add_client, get_clients, update_client, delete_client,
    get_example_counts, save_posting_schedule, get_posting_schedule
)

PLATFORM_OPTIONS = ["Instagram", "TikTok", "Facebook", "LinkedIn", "Twitter/X"]

POST_TYPE_PRESETS = {
    "Reel + Carousel":          {"label": "Reel + Carousel", "freq": 1, "notes": ""},
    "Static Post":              {"label": "Static Post",     "freq": 1, "notes": ""},
    "Katie-Focused Reel":       {"label": "Katie-Focused Reel", "freq": 4, "notes": "Posted across all profiles"},
    "Story":                    {"label": "Story",           "freq": 4, "notes": ""},
    "Google Business Profile":  {"label": "Google Business Profile Post", "freq": 10, "notes": ""},
    "Custom":                   {"label": "",                "freq": 1, "notes": ""},
}


def _get_user_clients():
    """Get clients scoped to the current user."""
    if st.session_state.get("is_master"):
        return get_clients()
    owner_id = st.session_state.get("user", {}).get("id")
    return get_clients(owner_id=owner_id)


def _get_owner_id():
    """Get the owner_id to assign when creating a new client."""
    user = st.session_state.get("user", {})
    if user.get("role") == "master":
        return None  # Master-created clients are shared/global
    return user.get("id")


def schedule_editor(client_id, key_prefix=""):
    """Reusable posting schedule editor widget."""
    schedule = get_posting_schedule(client_id)
    post_types = schedule.get("post_types", [])

    st.markdown("#### 📅 Monthly Posting Schedule")
    st.caption("Define the recurring content types posted each month for this client.")

    # Add post type row
    with st.expander("➕ Add Content Type", expanded=len(post_types) == 0):
        col1, col2, col3 = st.columns([3, 1, 2])
        preset = col1.selectbox("Preset", list(POST_TYPE_PRESETS.keys()), key=f"{key_prefix}_preset")
        defaults = POST_TYPE_PRESETS[preset]
        label_val = defaults["label"] if preset != "Custom" else ""

        label  = col1.text_input("Content Type Label", value=label_val, key=f"{key_prefix}_label")
        freq   = col2.number_input("Per Month", min_value=1, max_value=31, value=defaults["freq"], key=f"{key_prefix}_freq")
        notes  = col3.text_input("Notes", value=defaults["notes"], placeholder="e.g. Posted to all 3 accounts", key=f"{key_prefix}_notes")

        if st.button("Add Row", key=f"{key_prefix}_add_row"):
            if label.strip():
                post_types.append({"label": label.strip(), "freq": int(freq), "notes": notes})
                schedule["post_types"] = post_types
                save_posting_schedule(client_id, json.dumps(schedule))
                st.success(f"Added: {label}")
                st.rerun()
            else:
                st.error("Please enter a content type label.")

    # Show existing rows
    if post_types:
        total = sum(p.get("freq", 1) for p in post_types)
        st.caption(f"**Total posts/month: {total}**")

        for i, pt in enumerate(post_types):
            c1, c2, c3, c4 = st.columns([3, 1, 3, 1])
            c1.markdown(f"**{pt['label']}**")
            c2.markdown(f"`{pt['freq']}x`")
            c3.caption(pt.get("notes", ""))
            if c4.button("🗑️", key=f"{key_prefix}_del_{i}"):
                post_types.pop(i)
                schedule["post_types"] = post_types
                save_posting_schedule(client_id, json.dumps(schedule))
                st.rerun()

    # Proposal / notes
    st.markdown("#### 📋 Strategy Notes / Proposal")
    proposal = st.text_area(
        "Paste the client's content strategy or proposal here",
        value=schedule.get("proposal", ""),
        height=180,
        key=f"{key_prefix}_proposal",
        placeholder="Paste the full proposal text, pricing, goals, etc."
    )
    notes = st.text_input(
        "Quick notes",
        value=schedule.get("notes", ""),
        key=f"{key_prefix}_notes_main",
        placeholder="e.g. Reconvene after 3 months. Posts to all 3 brands."
    )

    if st.button("💾 Save Schedule", key=f"{key_prefix}_save_sched", type="primary"):
        schedule["post_types"] = post_types
        schedule["proposal"]   = proposal
        schedule["notes"]      = notes
        schedule["total_monthly"] = sum(p.get("freq", 1) for p in post_types)
        save_posting_schedule(client_id, json.dumps(schedule))
        st.success("✅ Posting schedule saved!")


def _website_scanner_section():
    """Website URL scanner widget for auto-populating brand data."""
    st.markdown("#### 🌐 Scan Website for Brand Data")
    st.caption(
        "Paste your website URL and we'll automatically extract your brand voice, "
        "colors, fonts, industry, and target audience using AI."
    )

    scan_url = st.text_input(
        "Website URL",
        placeholder="https://yourbusiness.com",
        key="scan_url_input",
    )

    if st.button("🔍 Scan Website", key="scan_website_btn", type="primary"):
        if not scan_url.strip():
            st.error("Please enter a URL.")
            return None

        with st.spinner("🌐 Scanning website and analyzing brand..."):
            try:
                from website_scanner import scan_website
                result = scan_website(scan_url.strip())
                st.session_state["scan_result"] = result
                st.success("✅ Website scanned successfully!")
            except Exception as e:
                st.error(f"Scan failed: {e}")
                st.info("Make sure the URL is correct and the website is publicly accessible.")
                return None

    # Show scan results if available
    result = st.session_state.get("scan_result")
    if result:
        st.markdown("---")
        st.markdown("**📊 Scan Results** — review and edit before saving:")

        col_a, col_b = st.columns(2)
        with col_a:
            st.markdown(f"**Business:** {result.get('business_name', 'N/A')}")
            st.markdown(f"**Industry:** {result.get('industry', 'N/A')}")
            if result.get("tagline"):
                st.markdown(f"**Tagline:** _{result['tagline']}_")
        with col_b:
            colors = result.get("colors", [])
            if colors:
                color_html = " ".join(
                    f'<span style="display:inline-block;width:24px;height:24px;'
                    f'background:{c};border-radius:4px;margin:2px;border:1px solid #ccc;" '
                    f'title="{c}"></span>'
                    for c in colors[:6]
                )
                st.markdown(f"**Colors:** {color_html}", unsafe_allow_html=True)
            fonts = result.get("fonts", [])
            if fonts:
                st.markdown(f"**Fonts:** {', '.join(fonts)}")

        st.markdown("**Brand Voice (AI-analyzed):**")
        st.info(result.get("brand_voice", "N/A"))

        st.markdown("**Target Audience:**")
        st.caption(result.get("target_audience", "N/A"))

        if result.get("notes"):
            st.markdown("**Additional Notes:**")
            st.caption(result["notes"])

        return result

    return None


def show():
    st.title("👤 Client Management")

    clients = _get_user_clients()
    tabs = st.tabs(["➕ Add New Client", "📋 Manage Existing Clients"])

    # ── Add New Client ─────────────────────────────────────────────────────────
    with tabs[0]:
        st.subheader("Add a New Client")

        # Website scanner section
        scan_result = _website_scanner_section()

        st.markdown("---")

        # Pre-fill form with scan results if available
        sr = scan_result or {}
        prefill_name = sr.get("business_name", "")
        prefill_industry = sr.get("industry", "")
        prefill_voice = sr.get("brand_voice", "")
        prefill_audience = sr.get("target_audience", "")
        prefill_notes = sr.get("notes", "")
        prefill_platforms = sr.get("platforms_suggested", ["Instagram", "TikTok"])

        # Validate platform names against our options
        valid_prefill = [p for p in prefill_platforms if p in PLATFORM_OPTIONS]
        if not valid_prefill:
            valid_prefill = ["Instagram", "TikTok"]

        with st.form("add_client_form"):
            name     = st.text_input("Client / Business Name *",
                                     value=prefill_name,
                                     placeholder="e.g. Katie Riedel – Calm Water")
            industry = st.text_input("Industry",
                                     value=prefill_industry,
                                     placeholder="e.g. Vacation Rentals, Glamping, Hospitality")
            brand_voice = st.text_area(
                "Brand Voice & Tone",
                value=prefill_voice,
                placeholder="Describe how this brand speaks. e.g. 'Warm, inviting, nature-focused.'"
            )
            target_audience = st.text_area(
                "Target Audience",
                value=prefill_audience,
                placeholder="e.g. Couples and families seeking Texas Hill Country getaways."
            )
            platforms = st.multiselect("Active Platforms", PLATFORM_OPTIONS, default=valid_prefill)
            notes = st.text_area("Additional Notes",
                                 value=prefill_notes,
                                 placeholder="Anything else the AI should know...")
            submitted = st.form_submit_button("Save Client", type="primary")

        if submitted:
            if not name.strip():
                st.error("Client name is required.")
            else:
                try:
                    add_client(
                        name=name.strip(),
                        industry=industry,
                        brand_voice=brand_voice,
                        target_audience=target_audience,
                        platforms=", ".join(platforms),
                        notes=notes,
                        owner_id=_get_owner_id(),
                    )
                    st.success(f"✅ Client **{name}** added! You can now set up their posting schedule below.")
                    # Clear scan result
                    st.session_state.pop("scan_result", None)
                    st.rerun()
                except Exception as e:
                    if "UNIQUE" in str(e):
                        st.error(f"A client named '{name}' already exists.")
                    else:
                        st.error(f"Error: {e}")

    # ── Manage Existing ────────────────────────────────────────────────────────
    with tabs[1]:
        if not clients:
            st.info("No clients yet. Add one using the **Add New Client** tab.")
            return

        for client in clients:
            counts = get_example_counts(client["id"])
            g = counts.get("good", 0)
            b = counts.get("bad",  0)
            u = counts.get("used", 0)
            schedule = get_posting_schedule(client["id"])
            total_posts = schedule.get("total_monthly", 0)

            header = f"**{client['name']}** — {client.get('industry', 'No industry')}  |  ✅{g} ❌{b} 📌{u}"
            if total_posts:
                header += f"  |  📅 {total_posts} posts/mo"

            with st.expander(header):
                inner_tabs = st.tabs(["✏️ Profile", "📅 Posting Schedule", "🌐 Re-scan Website"])

                # ── Profile tab ────────────────────────────────────────────────
                with inner_tabs[0]:
                    with st.form(f"edit_{client['id']}"):
                        n   = st.text_input("Name",            value=client["name"])
                        ind = st.text_input("Industry",        value=client.get("industry", ""))
                        bv  = st.text_area("Brand Voice",      value=client.get("brand_voice", ""))
                        ta  = st.text_area("Target Audience",  value=client.get("target_audience", ""))
                        current_platforms = [p.strip() for p in (client.get("platforms") or "").split(",") if p.strip()]
                        pl  = st.multiselect("Platforms", PLATFORM_OPTIONS,
                                             default=[p for p in current_platforms if p in PLATFORM_OPTIONS])
                        nt  = st.text_area("Notes",            value=client.get("notes", ""))

                        col_save, col_del = st.columns([3, 1])
                        if col_save.form_submit_button("💾 Save Changes", use_container_width=True):
                            update_client(client["id"], name=n, industry=ind, brand_voice=bv,
                                          target_audience=ta, platforms=", ".join(pl), notes=nt)
                            st.success("Updated!")
                            st.rerun()

                    if st.button("🗑️ Delete Client", key=f"del_{client['id']}"):
                        st.session_state[f"confirm_del_{client['id']}"] = True

                    if st.session_state.get(f"confirm_del_{client['id']}"):
                        st.warning(f"Delete **{client['name']}** and ALL their data?")
                        c1, c2 = st.columns(2)
                        if c1.button("Yes, delete", key=f"yes_{client['id']}"):
                            delete_client(client["id"])
                            st.success("Deleted.")
                            st.rerun()
                        if c2.button("Cancel", key=f"no_{client['id']}"):
                            st.session_state.pop(f"confirm_del_{client['id']}", None)
                            st.rerun()

                # ── Schedule tab ───────────────────────────────────────────────
                with inner_tabs[1]:
                    schedule_editor(client["id"], key_prefix=f"sched_{client['id']}")

                # ── Re-scan Website tab ────────────────────────────────────────
                with inner_tabs[2]:
                    st.caption("Re-scan a website to update this client's brand data.")
                    rescan_url = st.text_input(
                        "Website URL",
                        placeholder="https://yourbusiness.com",
                        key=f"rescan_url_{client['id']}",
                    )
                    if st.button("🔍 Scan & Update", key=f"rescan_btn_{client['id']}"):
                        if rescan_url.strip():
                            with st.spinner("Scanning..."):
                                try:
                                    from website_scanner import scan_website
                                    result = scan_website(rescan_url.strip())
                                    # Update client with scanned data
                                    update_client(
                                        client["id"],
                                        industry=result.get("industry", client.get("industry", "")),
                                        brand_voice=result.get("brand_voice", client.get("brand_voice", "")),
                                        target_audience=result.get("target_audience", client.get("target_audience", "")),
                                        notes=result.get("notes", client.get("notes", "")),
                                    )
                                    st.success("✅ Client updated with scanned brand data!")
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"Scan failed: {e}")
                        else:
                            st.error("Please enter a URL.")
