"""
drive_helper.py
Google Drive integration for the Content Batch Generator.

Handles:
  - OAuth authentication (one-time browser flow, token cached locally)
  - Listing image files inside a Drive folder URL
  - Downloading image thumbnails as base64
  - Calling Claude to visually select images that match a post's theme
"""

import os
import re
import json
import base64
import io
import requests
import anthropic

from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

# ── Paths ─────────────────────────────────────────────────────────────────────
BASE_DIR        = os.path.dirname(os.path.abspath(__file__))
TOKEN_PATH      = os.path.join(BASE_DIR, "data", "drive_token.json")
CREDS_PATH      = os.path.join(BASE_DIR, "data", "drive_credentials.json")

SCOPES = ["https://www.googleapis.com/auth/drive.readonly"]

IMAGE_MIMES = {
    "image/jpeg", "image/jpg", "image/png", "image/webp",
    "image/gif", "image/heic", "image/heif",
}


# ── Auth ───────────────────────────────────────────────────────────────────────

def is_drive_configured():
    """True if credentials OR token file exists (token means auth already completed)."""
    return os.path.exists(CREDS_PATH) or os.path.exists(TOKEN_PATH)


def get_drive_service():
    """
    Return an authenticated Google Drive service.
    - First run: opens browser for OAuth, saves token.
    - Subsequent runs: loads cached token, refreshes if expired.
    """
    os.makedirs(os.path.dirname(TOKEN_PATH), exist_ok=True)
    creds = None

    if os.path.exists(TOKEN_PATH):
        creds = Credentials.from_authorized_user_file(TOKEN_PATH, SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not os.path.exists(CREDS_PATH):
                raise FileNotFoundError(
                    "drive_credentials.json not found. "
                    "Run setup_drive.bat to set up Google Drive access."
                )
            flow = InstalledAppFlow.from_client_secrets_file(CREDS_PATH, SCOPES)
            creds = flow.run_local_server(port=0)

        with open(TOKEN_PATH, "w") as f:
            f.write(creds.to_json())

    return build("drive", "v3", credentials=creds)


# ── Folder URL parsing ─────────────────────────────────────────────────────────

def extract_folder_id(url: str) -> str | None:
    """
    Extract folder ID from any Google Drive folder URL format:
      https://drive.google.com/drive/folders/FOLDER_ID
      https://drive.google.com/drive/u/0/folders/FOLDER_ID
      https://drive.google.com/open?id=FOLDER_ID
    """
    patterns = [
        r"drive\.google\.com/drive(?:/u/\d+)?/folders/([a-zA-Z0-9_-]+)",
        r"drive\.google\.com/open\?id=([a-zA-Z0-9_-]+)",
        r"^([a-zA-Z0-9_-]{25,})$",   # raw folder ID pasted directly
    ]
    for pat in patterns:
        m = re.search(pat, url.strip())
        if m:
            return m.group(1)
    return None


# ── File listing ───────────────────────────────────────────────────────────────

def list_images_in_folder(folder_id: str, max_files: int = 40) -> list[dict]:
    """
    Return a list of image file dicts from a Drive folder:
      [{"id": ..., "name": ..., "mimeType": ..., "webViewLink": ...}, ...]
    """
    service = get_drive_service()
    results = service.files().list(
        q=f"'{folder_id}' in parents and trashed=false",
        pageSize=max_files,
        fields="files(id, name, mimeType, webViewLink, thumbnailLink, size)",
        orderBy="name",
    ).execute()

    files = results.get("files", [])
    # Filter to images only
    return [f for f in files if f.get("mimeType", "") in IMAGE_MIMES]


# ── Image downloading ──────────────────────────────────────────────────────────

def download_image_as_base64(file_id: str, max_bytes: int = 3_500_000) -> tuple[str, str]:
    """
    Download a Drive image file and return (base64_data, media_type).
    Uses thumbnail if file is too large.
    """
    service  = get_drive_service()
    creds    = service._http.credentials
    headers  = {"Authorization": f"Bearer {creds.token}"}

    # Try downloading the actual file
    url = f"https://www.googleapis.com/drive/v3/files/{file_id}?alt=media"
    resp = requests.get(url, headers=headers, timeout=15)

    if resp.status_code == 200 and len(resp.content) <= max_bytes:
        b64  = base64.standard_b64encode(resp.content).decode()
        mime = resp.headers.get("Content-Type", "image/jpeg").split(";")[0].strip()
        return b64, mime

    # Fallback: use the thumbnail (lower res but always available)
    meta = service.files().get(
        fileId=file_id, fields="thumbnailLink"
    ).execute()
    thumb_url = meta.get("thumbnailLink", "").replace("=s220", "=s800")
    if thumb_url:
        r2 = requests.get(thumb_url, timeout=10)
        if r2.status_code == 200:
            b64 = base64.standard_b64encode(r2.content).decode()
            return b64, "image/jpeg"

    raise ValueError(f"Could not download image {file_id}")


# ── AI image selection ─────────────────────────────────────────────────────────

def ai_select_images(
    images: list[dict],         # [{"id":..., "name":..., "b64":..., "mime":...}]
    post_title: str,
    post_caption: str,
    post_type: str,             # "Carousel" or "Static Post"
    num_to_select: int = 5,
) -> list[dict]:
    """
    Pass images to Claude, ask it to visually inspect each one and pick
    the best matches for the given post's content/theme.

    Returns a list of selected image dicts (subset of `images`).
    """
    claude = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

    # Build message content — text prompt + all images
    content = []

    content.append({
        "type": "text",
        "text": (
            f"You are selecting images for a social media {post_type}.\n\n"
            f"POST TITLE: {post_title}\n\n"
            f"POST CAPTION:\n{post_caption}\n\n"
            f"TASK: Look at each of the {len(images)} images below carefully. "
            f"Select the {num_to_select} images that best match the mood, theme, "
            f"and subject matter of this post. Consider visual storytelling — "
            f"do the images show what the caption talks about?\n\n"
            f"Respond ONLY with a JSON array of selected image names, in the best display order:\n"
            f'["filename1.jpg", "filename2.jpg", ...]\n\n'
            f"Images to evaluate:"
        )
    })

    # Add each image with its filename label
    for img in images:
        content.append({
            "type": "text",
            "text": f"\n--- Image: {img['name']} ---"
        })
        content.append({
            "type": "image",
            "source": {
                "type":       "base64",
                "media_type": img["mime"],
                "data":       img["b64"],
            }
        })

    response = claude.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=512,
        messages=[{"role": "user", "content": content}]
    )

    raw = response.content[0].text.strip()
    # Strip markdown fences if present
    if raw.startswith("```"):
        raw = re.sub(r"^```[a-z]*\n?", "", raw)
        raw = re.sub(r"\n?```$", "", raw)

    try:
        selected_names = json.loads(raw)
    except json.JSONDecodeError:
        # Fallback: just return first N
        return images[:num_to_select]

    # Return matching image dicts in selected order
    name_map = {img["name"]: img for img in images}
    selected = []
    for name in selected_names:
        if name in name_map:
            selected.append(name_map[name])
    # If somehow none matched, fallback
    if not selected:
        selected = images[:num_to_select]
    return selected


# ── High-level convenience function ───────────────────────────────────────────

def select_images_for_post(
    folder_url: str,
    post_title: str,
    post_caption: str,
    post_type: str,
    num_to_select: int = 5,
    progress_callback=None,
) -> list[dict]:
    """
    Full pipeline: folder URL → list images → download thumbnails → AI selects.

    Returns list of dicts:
      [{"name": ..., "id": ..., "webViewLink": ..., "selected": True}, ...]
    """
    folder_id = extract_folder_id(folder_url)
    if not folder_id:
        raise ValueError(f"Could not parse a folder ID from: {folder_url}")

    if progress_callback:
        progress_callback("📂 Listing images in folder...")
    all_files = list_images_in_folder(folder_id, max_files=40)

    if not all_files:
        raise ValueError("No image files found in that folder.")

    if progress_callback:
        progress_callback(f"⬇️ Downloading {len(all_files)} image thumbnails...")

    images_with_data = []
    for i, f in enumerate(all_files):
        try:
            b64, mime = download_image_as_base64(f["id"])
            images_with_data.append({
                "id":          f["id"],
                "name":        f["name"],
                "mime":        mime,
                "b64":         b64,
                "webViewLink": f.get("webViewLink", ""),
            })
        except Exception:
            pass  # skip undownloadable files
        if progress_callback and i % 5 == 0:
            progress_callback(f"⬇️ Downloaded {i+1}/{len(all_files)} images...")

    if not images_with_data:
        raise ValueError("Could not download any images from that folder.")

    # Cap at 20 images to keep API call fast
    images_with_data = images_with_data[:20]
    num_to_select = min(num_to_select, len(images_with_data))

    if progress_callback:
        progress_callback(f"🤖 AI is reviewing {len(images_with_data)} images and choosing the best {num_to_select} for this post...")

    selected = ai_select_images(
        images=images_with_data,
        post_title=post_title,
        post_caption=post_caption,
        post_type=post_type,
        num_to_select=num_to_select,
    )

    return selected


# ── Random image picking (no specific post context needed) ────────────────────

def pick_random_images(folder_url: str, count: int = 3) -> list[dict]:
    """
    Pick `count` random images from a Drive folder.
    Returns list of {"id", "name", "webViewLink"} dicts.
    No AI vision needed — purely random selection.
    """
    import random
    folder_id = extract_folder_id(folder_url)
    if not folder_id:
        raise ValueError(f"Could not parse folder ID from: {folder_url}")
    all_files = list_images_in_folder(folder_id, max_files=50)
    if not all_files:
        raise ValueError("No images found in that folder.")
    chosen = random.sample(all_files, min(count, len(all_files)))
    return [{"id": f["id"], "name": f["name"], "webViewLink": f.get("webViewLink", "")} for f in chosen]


# ── Upload a file to Google Drive ─────────────────────────────────────────────

def upload_to_drive(
    file_bytes: bytes,
    filename: str,
    mime_type: str = "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    parent_folder_id: str = None,
) -> dict:
    """
    Upload a file to Google Drive.
    Returns the created file metadata dict with 'id' and 'webViewLink'.
    """
    from googleapiclient.http import MediaIoBaseUpload
    import io as _io

    service = get_drive_service()
    metadata = {"name": filename}
    if parent_folder_id:
        metadata["parents"] = [parent_folder_id]

    media = MediaIoBaseUpload(
        _io.BytesIO(file_bytes),
        mimetype=mime_type,
        resumable=True,
    )
    created = service.files().create(
        body=metadata,
        media_body=media,
        fields="id, name, webViewLink",
    ).execute()
    return created
