"""
pages/batch_generator.py  —  Content Batch Generator (v3)

FLOW:
  Step 1 ── Select client + month + (optional) image folder → Generate Full Batch
  Step 2 ── AI plans & writes all 10 posts with captions, hooks, image directions
  Step 3 ── AI auto-selects 3–5 images per carousel/static post from provided folder
  Step 4 ── Vote on each caption (👍/👎) and on the whole batch → trains the AI
  Step 5 ── Export as .docx Word file + optional save to Google Drive
"""

import streamlit as st
import json
import os
from datetime import datetime
from database import (
    get_clients, get_example_counts, get_posting_schedule,
    save_generation, add_example
)
from caption_generator import plan_full_batch


def _get_user_clients():
    """Get clients scoped to the current user."""
    if st.session_state.get("is_master"):
        return get_clients()
    owner_id = st.session_state.get("user", {}).get("id")
    return get_clients(owner_id=owner_id)

# ── Lazy imports ──────────────────────────────────────────────────────────────
def _get_drive():
    try:
        import drive_helper
        return drive_helper
    except Exception:
        return None

def _check_drive_files():
    base = os.path.dirname(os.path.abspath(__file__))
    data_dir = os.path.join(base, "..", "data")
    return (
        os.path.exists(os.path.join(data_dir, "drive_token.json")) or
        os.path.exists(os.path.join(data_dir, "drive_credentials.json"))
    )

def _get_exporter():
    try:
        import batch_exporter
        return batch_exporter
    except Exception:
        return None

# ── Constants ─────────────────────────────────────────────────────────────────
MONTHS = [
    "January","February","March","April","May","June",
    "July","August","September","October","November","December"
]
ACCOUNT_SHORT = {
    "Tipis on the Guadalupe (TOTG)": "TOTG",
    "Calm Water Rentals (CWR)":      "CWR",
    "River Road Escapes (RRE)":      "RRE",
}


# ── Main page ─────────────────────────────────────────────────────────────────
def show():
    st.title("📦 Content Batch Generator")

    clients = _get_user_clients()
    if not clients:
        st.warning("No clients yet. Go to **Clients** first.")
        return

    client_map    = {c["name"]: c for c in clients}
    selected_name = st.selectbox("Client", list(client_map.keys()))
    client        = client_map[selected_name]
    client_id     = client["id"]

    col1, col2 = st.columns(2)
    batch_month = col1.selectbox("Month", MONTHS, index=datetime.now().month - 1)
    batch_year  = col2.number_input("Year", min_value=2024, max_value=2030,
                                    value=datetime.now().year)

    # Readiness badge
    counts = get_example_counts(client_id)
    g, b, u = counts.get("good",0), counts.get("bad",0), counts.get("used",0)
    total_ex = g + b + u
    badge = "🟢" if total_ex >= 20 else "🟡" if total_ex >= 5 else "🔴"
    st.caption(f"{badge} AI Training Data: {total_ex} examples  ·  ✅{g} good  ❌{b} bad  📌{u} used")

    # Schedule summary
    schedule   = get_posting_schedule(client_id)
    post_types = schedule.get("post_types", [])
    if post_types:
        st.caption("📅 " + "  ·  ".join(f"{p['label']} ×{p['freq']}" for p in post_types))

    drive_ok = _check_drive_files()

    # ── Image folder settings ──────────────────────────────────────────────
    with st.expander("🖼️ Image Source (for carousel & static posts)", expanded=True):
        st.markdown("Paste the Google Drive folder link where your photos live. "
                    "The AI will automatically select 3–5 matching images per post.")
        image_folder_url = st.text_input(
            "Google Drive image folder URL",
            value=st.session_state.get("image_folder_url", ""),
            placeholder="https://drive.google.com/drive/folders/...",
            key="image_folder_url_input",
        )
        num_images = st.slider("Images per carousel post", min_value=2, max_value=8, value=5)
        num_static = st.slider("Images per static post",   min_value=1, max_value=3, value=1)

        if not drive_ok:
            st.warning("⚠️ Google Drive not connected. Run `setup_drive.bat` to enable image selection.")

    # ── Extra context ──────────────────────────────────────────────────────
    with st.expander("✏️ Add extra context for this month (optional)", expanded=False):
        extra_context = st.text_area(
            "Anything special about this month?",
            placeholder="e.g. 'Focus on Spring Break bookings. Mention the new kayak launch area.'",
            height=80,
            key="extra_context",
        )

    st.divider()

    # ── GENERATE button ────────────────────────────────────────────────────
    if st.button(
        f"✨ Generate Full {batch_month} {batch_year} Batch",
        type="primary",
        use_container_width=True,
    ):
        st.session_state["batch_posts"]   = []
        st.session_state["batch_ready"]   = False
        st.session_state["batch_month"]   = batch_month
        st.session_state["batch_year"]    = str(batch_year)
        st.session_state["batch_client"]  = selected_name
        st.session_state["batch_client_id"] = client_id
        st.session_state["image_folder_url"] = image_folder_url
        st.session_state["votes"]         = {}

        progress = st.progress(0, text="🤖 AI is writing all 10 posts...")
        status   = st.empty()

        try:
            status.info(f"Generating all 10 posts for **{batch_month} {batch_year}**... 15–30 seconds.")
            posts = plan_full_batch(
                client_id=client_id,
                month=batch_month,
                year=str(batch_year),
                extra_context=st.session_state.get("extra_context", ""),
            )
            progress.progress(50, text="✅ Posts written! Now selecting images...")

            # ── Auto-select images if folder provided ──────────────────────
            if image_folder_url.strip() and drive_ok:
                drive = _get_drive()
                if drive:
                    non_video = [(i, p) for i, p in enumerate(posts) if not p.get("is_video")]
                    for step, (i, post) in enumerate(non_video):
                        ptype = post.get("post_type", "Carousel")
                        n = num_images if ptype == "Carousel" else num_static
                        try:
                            status.info(f"🖼️ Selecting images for post #{i+1}: {post.get('title','')}...")
                            selected = drive.select_images_for_post(
                                folder_url=image_folder_url,
                                post_title=post.get("title", ""),
                                post_caption=post.get("caption", ""),
                                post_type=ptype,
                                num_to_select=n,
                            )
                            posts[i]["selected_images"] = selected
                        except Exception as e:
                            posts[i]["selected_images"] = []
                        progress.progress(
                            50 + int(((step+1)/len(non_video)) * 50),
                            text=f"Selecting images... {step+1}/{len(non_video)}"
                        )

            progress.progress(100, text="✅ Batch complete!")
            status.empty()
            st.session_state["batch_posts"] = posts
            st.session_state["batch_ready"] = True
            st.rerun()

        except Exception as e:
            progress.empty()
            status.empty()
            st.error(f"Generation failed: {e}")

    # ── Show batch ─────────────────────────────────────────────────────────
    posts     = st.session_state.get("batch_posts", [])
    bm        = st.session_state.get("batch_month", batch_month)
    by        = st.session_state.get("batch_year",  str(batch_year))
    bcl       = st.session_state.get("batch_client", selected_name)
    bcl_id    = st.session_state.get("batch_client_id", client_id)
    votes     = st.session_state.get("votes", {})

    if not posts:
        st.markdown("""
        <div style='text-align:center;padding:3rem 1rem;color:#888;'>
            <div style='font-size:3rem;'>✨</div>
            <div style='font-size:1.1rem;margin-top:0.5rem;'>
                Select client, month, and image folder above,<br>
                then click <strong>Generate Full Batch</strong>.
            </div>
        </div>""", unsafe_allow_html=True)
        return

    st.subheader(f"📋 {bcl} — {bm} {by}  ({len(posts)} posts)")

    col_regen, col_clear = st.columns([3,1])
    if col_regen.button("🔄 Regenerate Batch", use_container_width=True):
        st.session_state["batch_posts"] = []
        st.session_state["batch_ready"] = False
        st.session_state["votes"] = {}
        st.rerun()
    if col_clear.button("🗑️ Clear", use_container_width=True):
        st.session_state["batch_posts"] = []
        st.session_state["batch_ready"] = False
        st.session_state["votes"] = {}
        st.rerun()

    st.divider()

    # ── Post cards ─────────────────────────────────────────────────────────
    for i, post in enumerate(posts):
        is_video = post.get("is_video", False)
        is_katie = post.get("is_katie", False)
        ptype    = post.get("post_type", "Post")
        account  = post.get("account", "")
        title    = post.get("title", f"Post #{i+1}")
        icon     = "🎬" if is_video else ("📸" if ptype == "Static Post" else "🖼️")
        kicon    = "💁‍♀️ " if is_katie else ""
        short    = ACCOUNT_SHORT.get(account, account)

        # Vote state display
        vote = votes.get(str(i), None)
        vote_badge = "  👍" if vote == "good" else ("  👎" if vote == "bad" else "")
        img_count  = len(post.get("selected_images", []))
        img_badge  = f"  ✅{img_count} imgs" if img_count else ""

        header = f"{icon} **#{i+1}** · {kicon}{short} · {ptype} · *{title}*{vote_badge}{img_badge}"

        with st.expander(header, expanded=False):

            # Concept
            if post.get("angle"):
                st.caption(f"💡 {post['angle']}")

            # Reel hook + direction
            if is_video:
                st.markdown("**🎬 Reel Hook:**")
                new_hook = st.text_input("", value=post.get("reel_hook",""),
                                         key=f"hook_{i}", label_visibility="collapsed")
                if new_hook != post.get("reel_hook",""):
                    st.session_state["batch_posts"][i]["reel_hook"] = new_hook

                if post.get("video_direction"):
                    st.info(f"📹 {post['video_direction']}")

                st.markdown("**🎥 Video File:**")
                vid_file = st.text_input(
                    "", value=post.get("video_file",""),
                    placeholder="Paste video Drive link or file path (leave blank for placeholder)",
                    key=f"vid_{i}", label_visibility="collapsed"
                )
                if vid_file != post.get("video_file",""):
                    st.session_state["batch_posts"][i]["video_file"] = vid_file

            # Caption
            st.markdown("**Caption:**")
            new_cap = st.text_area("", value=post.get("caption",""),
                                   key=f"cap_{i}", height=130, label_visibility="collapsed")
            if new_cap != post.get("caption",""):
                st.session_state["batch_posts"][i]["caption"] = new_cap

            # Hashtags
            new_tags = st.text_input("Hashtags", value=post.get("hashtags",""), key=f"tags_{i}")
            if new_tags != post.get("hashtags",""):
                st.session_state["batch_posts"][i]["hashtags"] = new_tags

            # Scheduled date
            sched = st.text_input("Scheduled date", value=post.get("scheduled_date",""),
                                   placeholder="e.g. March 4", key=f"sched_{i}")
            if sched != post.get("scheduled_date",""):
                st.session_state["batch_posts"][i]["scheduled_date"] = sched

            # ── Images for carousel/static ─────────────────────────────────
            if not is_video:
                st.markdown("---")
                st.markdown(f"**🖼️ Images ({ptype}):**")

                sel = post.get("selected_images", [])
                if sel:
                    img_cols = st.columns(min(len(sel), 4))
                    for j, img in enumerate(sel):
                        with img_cols[j % 4]:
                            if img.get("webViewLink"):
                                st.markdown(f"[📄 {img['name']}]({img['webViewLink']})")
                            else:
                                st.caption(img.get("name", f"Image {j+1}"))
                    if st.button("🔄 Re-select", key=f"resel_{i}"):
                        st.session_state["batch_posts"][i]["selected_images"] = []
                        st.rerun()
                else:
                    if drive_ok and _get_drive():
                        folder = st.text_input(
                            "Drive folder URL for this post:",
                            value=st.session_state.get("image_folder_url",""),
                            key=f"folder_{i}",
                            placeholder="https://drive.google.com/drive/folders/..."
                        )
                        n_pick = num_images if ptype == "Carousel" else num_static
                        if folder.strip() and st.button(f"🤖 Select {n_pick} images", key=f"pick_{i}"):
                            status2 = st.empty()
                            try:
                                drive = _get_drive()
                                selected = drive.select_images_for_post(
                                    folder_url=folder,
                                    post_title=post.get("title",""),
                                    post_caption=post.get("caption",""),
                                    post_type=ptype,
                                    num_to_select=n_pick,
                                    progress_callback=lambda m: status2.info(m),
                                )
                                st.session_state["batch_posts"][i]["selected_images"] = selected
                                status2.empty()
                                st.rerun()
                            except Exception as e:
                                status2.empty()
                                st.error(f"Drive error: {e}")
                    else:
                        manual = st.text_area(
                            "Paste image Drive links (one per line):",
                            value="\n".join(post.get("manual_links",[])),
                            key=f"manual_{i}", height=80
                        )
                        if manual.strip():
                            links = [l.strip() for l in manual.strip().split("\n") if l.strip()]
                            st.session_state["batch_posts"][i]["manual_links"] = links

                if post.get("image_prompt") and not sel:
                    st.caption(f"🤖 AI image direction: _{post['image_prompt']}_")

            # ── VOTE on this caption ───────────────────────────────────────
            st.markdown("---")
            st.markdown("**Rate this caption to train the AI:**")
            vc1, vc2, vc3 = st.columns([1, 1, 4])

            if vc1.button("👍 Good", key=f"vote_good_{i}", use_container_width=True):
                st.session_state["votes"][str(i)] = "good"
                # Save to examples database immediately
                caption_text = post.get("caption","")
                if caption_text:
                    context = f"{post.get('account','')} {post.get('post_type','')} – {post.get('title','')} – {bm} {by}"
                    try:
                        add_example(bcl_id, caption_text, "good", context, "Instagram/TikTok", "")
                        st.toast("✅ Saved as Good example!", icon="✅")
                    except Exception:
                        pass
                st.rerun()

            if vc2.button("👎 Bad", key=f"vote_bad_{i}", use_container_width=True):
                st.session_state["votes"][str(i)] = "bad"
                caption_text = post.get("caption","")
                if caption_text:
                    context = f"{post.get('account','')} {post.get('post_type','')} – {post.get('title','')} – {bm} {by}"
                    try:
                        add_example(bcl_id, caption_text, "bad", context, "Instagram/TikTok", "")
                        st.toast("❌ Saved as Bad example — AI will avoid this style.", icon="❌")
                    except Exception:
                        pass
                st.rerun()

            if vote:
                vc3.success(f"Voted: {'👍 Good' if vote == 'good' else '👎 Bad'} — saved to AI training data")

    st.divider()

    # ── OVERALL BATCH VOTE ─────────────────────────────────────────────────
    st.subheader("📊 Rate This Entire Batch")
    st.caption("Your overall rating trains the AI for future batches.")
    bv1, bv2, bv3 = st.columns([1, 1, 3])

    batch_vote = st.session_state.get("batch_vote", None)

    if bv1.button("👍 Batch is Good", use_container_width=True):
        st.session_state["batch_vote"] = "good"
        # Save all unvoted captions as good
        saved = 0
        for i, post in enumerate(posts):
            if votes.get(str(i)) is None:
                cap = post.get("caption","")
                if cap:
                    ctx = f"{post.get('account','')} {post.get('post_type','')} – {post.get('title','')} – {bm} {by}"
                    try:
                        add_example(bcl_id, cap, "good", ctx, "Instagram/TikTok", "")
                        saved += 1
                    except Exception:
                        pass
        st.toast(f"✅ Saved {saved} captions as Good examples!", icon="✅")
        st.rerun()

    if bv2.button("👎 Batch Needs Work", use_container_width=True):
        st.session_state["batch_vote"] = "bad"
        saved = 0
        for i, post in enumerate(posts):
            if votes.get(str(i)) is None:
                cap = post.get("caption","")
                if cap:
                    ctx = f"{post.get('account','')} {post.get('post_type','')} – {post.get('title','')} – {bm} {by}"
                    try:
                        add_example(bcl_id, cap, "bad", ctx, "Instagram/TikTok", "")
                        saved += 1
                    except Exception:
                        pass
        st.toast(f"❌ Saved {saved} captions as Bad examples — AI will improve!", icon="❌")
        st.rerun()

    if batch_vote:
        bv3.info(f"Batch rated: {'👍 Good' if batch_vote == 'good' else '👎 Needs Work'}")

    voted_count = len([v for v in votes.values() if v])
    st.caption(f"{voted_count}/{len(posts)} individual captions rated · "
               f"{'✅' if batch_vote else '⬜'} Overall batch rated")

    st.divider()

    # ── EXPORT ─────────────────────────────────────────────────────────────
    st.subheader("📥 Export Batch Document")
    fname_base = f"{bcl.replace(' ','_')}_{bm}_{by}_Content_Batch"
    exporter = _get_exporter()

    col_e1, col_e2, col_e3 = st.columns(3)

    # .docx export
    if exporter:
        try:
            docx_bytes = exporter.generate_batch_docx(
                posts=posts,
                client_name=bcl,
                month=bm,
                year=by,
            )
            col_e1.download_button(
                "📄 Download Word (.docx)",
                data=docx_bytes,
                file_name=f"{fname_base}.docx",
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                use_container_width=True,
            )
        except Exception as e:
            col_e1.error(f"DOCX error: {e}")
    else:
        col_e1.info("python-docx not installed")

    # Markdown export (fallback)
    def _mk_export():
        lines = [f"# {bcl} – {bm} {by} Content Batch ({len(posts)} Posts)\n",
                 f"Generated: {datetime.now().strftime('%B %d, %Y')}\n---\n"]
        for i, p in enumerate(posts, 1):
            lines += [f"## {p.get('account','')} – {p.get('post_type','')}",
                      f"### Post #{i} – {p.get('title','')}"]
            if p.get("reel_hook"):
                lines.append(f"**Reel Hook:** {p['reel_hook']}")
            if p.get("video_direction"):
                lines.append(f"**Video Direction:** {p['video_direction']}")
            lines += [f"**Caption:**\n{p.get('caption','')}", p.get("hashtags","")]
            sel = p.get("selected_images",[])
            if sel:
                lines.append("**Images:**")
                for j, img in enumerate(sel,1):
                    lines.append(f"  {j}. {img.get('webViewLink',img.get('name',''))}")
            lines.append("---\n")
        return "\n".join(lines)

    col_e2.download_button(
        "📋 Download .md",
        data=_mk_export(),
        file_name=f"{fname_base}.md",
        mime="text/markdown",
        use_container_width=True,
    )

    # Save to Google Drive
    if col_e3.button("☁️ Save to Google Drive", use_container_width=True):
        if not drive_ok:
            st.error("Google Drive not connected. Run setup_drive.bat first.")
        elif not exporter:
            st.error("python-docx not available.")
        else:
            drive_folder = st.session_state.get("image_folder_url","").strip()
            save_status = st.empty()
            try:
                save_status.info("Uploading to Google Drive...")
                docx_bytes = exporter.generate_batch_docx(posts=posts, client_name=bcl,
                                                           month=bm, year=by)
                drive = _get_drive()
                # Try to upload to same folder as images, or root
                parent = None
                if drive_folder:
                    parent = drive.extract_folder_id(drive_folder)
                result = drive.upload_to_drive(
                    file_bytes=docx_bytes,
                    filename=f"{fname_base}.docx",
                    parent_folder_id=parent,
                )
                save_status.success(
                    f"✅ Saved to Drive: [{result.get('name',fname_base)}]({result.get('webViewLink','')})"
                )
            except Exception as e:
                save_status.error(f"Drive upload failed: {e}")

    # Save to history
    if st.button("💾 Save to Generation History", use_container_width=True):
        save_generation(
            client_id=client_id,
            batch_desc=f"{bm} {by} Content Batch",
            platform="Instagram/TikTok",
            num_captions=len(posts),
            captions_json=json.dumps([
                {"caption": p.get("caption",""), "hashtags": p.get("hashtags",""),
                 "notes": p.get("title","")}
                for p in posts
            ]),
        )
        st.success("✅ Saved to generation history!")
