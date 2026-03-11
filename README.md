# TecMint Web Scraper

Web Scraping with Python — Extracts the **60 Best Free and Open Source Software** from a [TecMint article](https://www.tecmint.com/best-free-open-source-software/) and generates a clean Markdown table with tool images.

## 🛠️ How It Works

1. Scrapes the article for tool names, descriptions, and images
2. Downloads all tool images into `tool_images/`
3. Generates a `table.md` with a formatted Markdown table
4. Creates an `image_registry.txt` for tracking

## 📋 Requirements

- Python 3.x
```bash
# Debian/Ubuntu
sudo apt install python3-bs4 python3-requests

# Fedora
sudo dnf install python3-beautifulsoup4 python3-requests

# Arch
sudo pacman -S python-beautifulsoup4 python-requests

# Windows
pip install beautifulsoup4 requests
```

## 🚀 Usage

~~~bash
python3 generate_table.py
~~~

## 📊 Output

| Metric | Value |
|--------|------:|
| Tools scraped | 60 |
| Images downloaded | 52 |
| Placeholder (CLI/server-only tools) | 8 |

## 📝 Result

Check the final generated table here: **[table.md](table.md)**

## ⚠️ Tools Using Placeholder

These tools had no downloadable image in the article:

- Dracut
- Ollama
- Jan
- GPT4All
- OpenWebUI
- DocumentDB
- OpenHPC
- Odoo POS

---

## 📄 Generate .docx and .pdf

### Requirements

```bash
# Debian/Ubuntu
sudo apt install python3-docx python3-pil libreoffice

# Fedora
sudo dnf install python3-docx python3-pillow libreoffice

# Arch
sudo pacman -S python-docx python-pillow libreoffice-fresh

# Windows
pip install python-docx Pillow
```

> 💡 On Windows, install [LibreOffice](https://www.libreoffice.org/download/) and make sure `soffice` is in your PATH for PDF conversion.

### Usage

```bash
python3 generate_docx_pdf.py
```

This will:
1. Parse `table.md` and extract all tools, categories, images, and links
2. Generate a styled `.docx` with GitHub-like formatting
3. Convert to `.pdf` using LibreOffice (with bookmarks and metadata)

### Output

| File | Description |
|------|-------------|
| `60_Best_Free_Open_Source_Software.docx` | Styled Word document |
| `60_Best_Free_Open_Source_Software.pdf` | PDF with bookmarks and table of contents |

### Features

- 📑 **One tool per page** — clean, no cut images
- 🔖 **PDF bookmarks** — navigable by category and tool
- 🖼️ **All image formats** — PNG, JPG, WebP auto-converted via Pillow
- 🎨 **GitHub-style tables** — dark headers, alternating rows, light borders
- 📝 **Blockquote descriptions** — styled with left gray border
