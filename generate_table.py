"""
generate_table.py

Scrapes the TecMint "60 Must-Have Free and Open-Source Linux Tools for 2026"
article, matches each tool to local images in tool_images/, and generates
a Markdown file (table.md) with the image displayed below each tool.

For tools without a downloaded image, uses 'no_image.png' as placeholder.

Usage:
    pip install requests beautifulsoup4
    python generate_table.py
"""

import os
import re
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from difflib import SequenceMatcher

# ──────────────────────────── CONFIG ────────────────────────────
URL = "https://www.tecmint.com/best-free-open-source-software/"
IMAGES_DIR = "tool_images"
OUTPUT_MD = "table.md"
PLACEHOLDER = "advanced_tool.png"  # your attached placeholder image filename

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
    )
}

# ──────────────────────── HELPER FUNCTIONS ──────────────────────


def sanitize(name: str) -> str:
    """Normalize name for comparison."""
    return re.sub(r"[^a-z0-9]", "", name.lower())


def similarity(a: str, b: str) -> float:
    return SequenceMatcher(None, sanitize(a), sanitize(b)).ratio()


# find_image removed — using direct download mapping instead


def sanitize_filename(name: str) -> str:
    name = re.sub(r'[\\/*?:"<>|]', "", name)
    return name.strip().replace(" ", "_")


def get_extension(url: str, resp: requests.Response) -> str:
    ct = resp.headers.get("Content-Type", "")
    for ext_check, ext in [("png", ".png"), ("webp", ".webp"),
                           ("svg", ".svg"), ("gif", ".gif")]:
        if ext_check in ct or url.lower().endswith(f".{ext_check}"):
            return ext
    return ".jpg"


def download_image(img_url: str, tool_name: str) -> str | None:
    """Download image, return saved filename or None."""
    try:
        resp = requests.get(img_url, headers=HEADERS, timeout=15, stream=True)
        resp.raise_for_status()

        # Skip tiny placeholder images (< 1 KB = probably a 1x1 pixel)
        content = resp.content
        if len(content) < 1024:
            return None

        ext = get_extension(img_url, resp)
        filename = sanitize_filename(tool_name) + ext
        filepath = os.path.join(IMAGES_DIR, filename)

        with open(filepath, "wb") as f:
            f.write(content)

        size_kb = len(content) / 1024
        print(f"    💾 Downloaded: {filename} ({size_kb:.1f} KB)")
        return filename

    except Exception as e:
        print(f"    ❌ Download failed: {e}")
        return None


# ──────────────────────── MAIN LOGIC ────────────────────────────


def main():
    os.makedirs(IMAGES_DIR, exist_ok=True)

    # Copy placeholder image into IMAGES_DIR if not already there
    placeholder_dest = os.path.join(IMAGES_DIR, PLACEHOLDER)
    if not os.path.exists(placeholder_dest):
        placeholder_src = os.path.join(os.path.dirname(os.path.abspath(__file__)), PLACEHOLDER)
        if os.path.exists(placeholder_src):
            import shutil
            shutil.copy2(placeholder_src, placeholder_dest)
            print(f"📋 Copied placeholder: {PLACEHOLDER} → {IMAGES_DIR}/")
        else:
            print(f"⚠️  Placeholder not found: {placeholder_src}")

    # ── Step 1: Index existing images ──
    image_files = {}  # sanitized_name -> original_filename
    for f in os.listdir(IMAGES_DIR):
        if f.lower().endswith((".png", ".jpg", ".jpeg", ".webp", ".gif", ".svg")):
            name_no_ext = os.path.splitext(f)[0]
            key = sanitize(name_no_ext)
            image_files[key] = f

    print(f"📁 Found {sum(1 for f in os.listdir(IMAGES_DIR) if os.path.splitext(f)[1].lower() in {".png", ".jpg", ".jpeg", ".webp", ".gif", ".svg"} and f != PLACEHOLDER)} images in '{IMAGES_DIR}/'")

    # ── Step 2: Scrape the article ──
    print(f"🌐 Fetching: {URL}")
    resp = requests.get(URL, headers=HEADERS, timeout=30)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")

    content = soup.find("div", class_="entry-content") or soup
    headings = content.find_all(re.compile(r"^h[23]$"))

    heading_re = re.compile(r"^\s*(\d{1,2})\.\s+(.+)")

    tools = []  # list of dicts

    for heading in headings:
        text = heading.get_text(strip=True)
        match = heading_re.match(text)
        if not match:
            continue

        number = int(match.group(1))
        raw_name = match.group(2)

        # Split "Tool Name – Description" or "Tool Name - Description"
        parts = re.split(r"\s*[–—-]\s*", raw_name, maxsplit=1)
        tool_name = parts[0].strip()
        description = parts[1].strip() if len(parts) > 1 else ""

        # ── Find image URL from article (for potential download) ──
        img_url = None
        sibling = heading.find_next_sibling()
        while sibling:
            if sibling.name and re.match(r"^h[23]$", sibling.name):
                check = sibling.get_text(strip=True)
                if heading_re.match(check):
                    break
            img_tag = sibling.find("img") if sibling.name else None
            if img_tag:
                img_url = (
                    img_tag.get("data-src")
                    or img_tag.get("data-lazy-src")
                    or img_tag.get("data-orig-file")
                    or img_tag.get("src")
                )
                if img_url and img_url.startswith("data:"):
                    img_url = None  # skip base64 placeholders
                if img_url:
                    img_url = urljoin(URL, img_url)
                break
            sibling = sibling.find_next_sibling()

        # ── Also try to extract a short description from the next <p> ──
        if not description:
            p_tag = heading.find_next_sibling("p")
            if p_tag:
                desc_text = p_tag.get_text(separator=" ", strip=True)
                if len(desc_text) > 10:
                    # Take first sentence (up to 150 chars)
                    description = desc_text[:150].rsplit(".", 1)[0] + "."

        # ── Extract links from ALL elements between this heading and the next ──
        tool_links = []
        # Use find_all_next to get ALL following elements, not just siblings
        for elem in heading.find_all_next():
            # Stop at the next numbered heading
            if elem.name and re.match(r"^h[23]$", elem.name):
                check = elem.get_text(strip=True)
                if heading_re.match(check) and elem != heading:
                    break
            # Also stop at category headings (emojis or strong category markers)
            if elem.name == "h2":
                break
            # Grab all <a> tags
            if elem.name == "a" and elem.get("href"):
                href = elem["href"]
                link_text = elem.get_text(strip=True)
                if (href and link_text
                    and not href.startswith("#")
                    and not href.startswith("javascript")
                    and "buymeacoffee" not in href
                    and "shareaholic" not in href
                    and "/author/" not in href
                    and "/category/" not in href
                    and "/tag/" not in href
                    and href != "https://www.tecmint.com/best-free-open-source-software/"
                    and href != "https://www.tecmint.com/"
                    and "amazon." not in href
                    and "disneyplus" not in href
                    and "ad." not in href
                    and "click." not in href
                    and "doubleclick" not in href
                    and len(link_text) > 1):
                    tool_links.append({"text": link_text, "url": href})
        # Deduplicate links by URL
        seen_urls = set()
        unique_links = []
        for lnk in tool_links:
            if lnk["url"] not in seen_urls:
                seen_urls.add(lnk["url"])
                unique_links.append(lnk)

        tools.append({
            "number": number,
            "name": tool_name,
            "description": description,
            "img_url": img_url,
            "links": unique_links,
        })

    print(f"🔧 Scraped {len(tools)} tools from the article\n")

    # ── Step 3: Download images directly (no fuzzy matching) ──
    print("=" * 60)
    print("🖼️  DOWNLOADING IMAGES (DIRECT FROM ARTICLE)")
    print("=" * 60)

    # Build an image registry: tool_number → filename
    image_registry = {}
    downloaded_count = 0
    placeholder_count = 0
    reused_count = 0

    for tool in tools:
        name = tool["name"]
        number = tool["number"]
        expected_filename_base = sanitize_filename(name)
        print(f"\n[{number:2d}] {name}")

        # Check if we already have an image for this exact tool name
        existing = None
        for f in os.listdir(IMAGES_DIR):
            fname_no_ext = os.path.splitext(f)[0]
            if fname_no_ext == expected_filename_base:
                existing = f
                break

        if existing and existing != PLACEHOLDER:
            print(f"    ✅ Already exists → {existing}")
            image_registry[number] = existing
            tool["image"] = existing
            reused_count += 1
            continue

        # Download from article
        if tool["img_url"]:
            print(f"    🔽 Downloading: {tool['img_url'][:80]}...")
            downloaded_file = download_image(tool["img_url"], name)
            if downloaded_file:
                image_registry[number] = downloaded_file
                tool["image"] = downloaded_file
                downloaded_count += 1
                continue

        # No image available → placeholder
        print(f"    🔲 Using placeholder: {PLACEHOLDER}")
        image_registry[number] = PLACEHOLDER
        tool["image"] = PLACEHOLDER
        placeholder_count += 1

    # Save registry for reference
    registry_path = os.path.join(IMAGES_DIR, "image_registry.txt")
    with open(registry_path, "w") as rf:
        rf.write(f"{'#':>3} | {'Tool Name':<30} | {'Image File'}\n")
        rf.write(f"{'-'*3}-+-{'-'*30}-+-{'-'*40}\n")
        for tool in tools:
            rf.write(f"{tool['number']:>3} | {tool['name']:<30} | {tool['image']}\n")
    print(f"\n📋 Image registry saved to: {registry_path}")

    matched_count = reused_count

    # ── Step 4: Categorize tools ──
    # Simple categorization based on tool names and descriptions
    categories = {
        "Screen Recording": ["SimpleScreenRecorder", "Kazam", "Kooha", "VokoscreenNG"],
        "Reporting & BI": ["Jaspersoft Studio"],
        "Graphics & Design": ["GIMP", "Inkscape", "LibreOffice Draw", "Blender"],
        "Video Editing & Conversion": ["Shotcut", "OpenShot", "DVDStyler",
                                        "OBS Studio", "HandBrake"],
        "Audio & Music": ["Audacity", "Ampache", "MuseScore", "TuxGuitar"],
        "Office & Productivity": ["ONLYOFFICE", "LibreOffice", "Thunderbird",
                                   "Cherrytree", "OpenTodoList"],
        "PDF Tools": ["PDF Mix Tool", "Master PDF Editor"],
        "Note-taking & Wiki": ["MediaWiki", "Cherrytree"],
        "Email": ["Mailspring", "Thunderbird"],
        "Cloud & File Sync": ["NextCloud", "Owncloud", "Internxt"],
        "Multimedia": ["VLC Media Player"],
        "Development & IDEs": ["Visual Studio Code", "CodeMirror", "Fyne"],
        "AI & CLI Tools": ["Gemini CLI"],
        "Finance & ERP": ["GNUCash", "GNU Health"],
        "Document Management": ["LogicalDOC"],
        "IT Asset Management": ["GLPI", "OCS Inventory NG"],
        "Network Monitoring": ["OpenNMS"],
        "Security": ["KeePass", "Security Onion", "OSQuery", "Bleachbit"],
        "Remote Access": ["FreeRDP", "Jitsi"],
        "System & Backup": ["Timeshift"],
        "Terminal & Utilities": ["Tmux"],
        "Science & Simulation": ["Celestia", "FlightGear"],
        "Bug Tracking": ["Flyspray"],
        "Installer": ["Calamares"],
        "BitTorrent": ["qBittorrent"],
        "3D Modeling & CAD": ["FreeCAD"],
        "Health": ["GNU Health"],
    }

    def get_category(tool_name: str) -> str:
        for cat, names in categories.items():
            for n in names:
                if sanitize(tool_name) == sanitize(n):
                    return cat
                if sanitize(n) in sanitize(tool_name) or sanitize(tool_name) in sanitize(n):
                    return cat
        return "Other"

    for tool in tools:
        tool["category"] = get_category(tool["name"])

    # ── Step 5: Generate Markdown ──
    lines = []
    lines.append("# 60 Must-Have Free and Open-Source Linux Tools for 2026\n")
    lines.append("> **Source:** [TecMint]"
                 "(https://www.tecmint.com/best-free-open-source-software/)"
                 " — by Gabriel Cánepa\n")
    lines.append("---\n")

    current_cat = ""
    for tool in tools:
        # Category header
        if tool["category"] != current_cat:
            current_cat = tool["category"]
            lines.append(f"\n## 📂 {current_cat}\n")

        # Tool entry
        img_path = f"{IMAGES_DIR}/{tool['image']}"
        lines.append(f"### {tool['number']}. {tool['name']}\n")
        if tool["description"]:
            # Fix any remaining spacing issues
            desc = re.sub(r"(\w),([A-Za-z])", r"\1, \2", tool["description"])
            desc = re.sub(r"(\w)([A-Z][a-z])", r"\1 \2", desc)
            lines.append(f"> {desc}\n")

        # Add links if available
        if tool.get("links"):
            link_parts = []
            for lnk in tool["links"]:
                link_parts.append(f"[{lnk['text']}]({lnk['url']})")
            lines.append(f"🔗 {' | '.join(link_parts)}\n")

        lines.append(f"![{tool['name']}]({img_path})\n")

        lines.append("---\n")

    md_content = "\n".join(lines)

    with open(OUTPUT_MD, "w", encoding="utf-8") as f:
        f.write(md_content)

    # ── Step 6: Final Report ──
    print(f"\n{'=' * 60}")
    print(f"📊 FINAL REPORT")
    print(f"{'=' * 60}")
    print(f"  🔧 Total tools scraped:    {len(tools)}")
    print(f"  ✅ Reused existing image:  {reused_count}")
    print(f"  💾 Downloaded from article: {downloaded_count}")
    print(f"  🔲 Using placeholder:      {placeholder_count}")
    print(f"  📁 Total images in folder: {sum(1 for f in os.listdir(IMAGES_DIR) if os.path.splitext(f)[1].lower() in {".png", ".jpg", ".jpeg", ".webp", ".gif", ".svg"})}")
    print(f"  📝 Output file:            {OUTPUT_MD}")
    print(f"{'=' * 60}")

    if placeholder_count > 0:
        print(f"\n⚠️  {placeholder_count} tools are using '{PLACEHOLDER}'.")
        print("   These tools had no downloadable image in the article:")
        for tool in tools:
            if tool["image"] == PLACEHOLDER:
                print(f"     • [{tool['number']}] {tool['name']}")

    print(f"\n✅ Done! Open '{OUTPUT_MD}' to see your result.")


if __name__ == "__main__":
    main()
