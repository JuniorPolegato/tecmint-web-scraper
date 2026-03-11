# TecMint Web Scraper

Web Scraping with Python — Extracts the **60 Best Free and Open Source Software** from a [TecMint article](https://www.tecmint.com/best-free-open-source-software/) and generates a clean Markdown table with tool images.

## 🛠️ How It Works

1. Scrapes the article for tool names, descriptions, and images
2. Downloads all tool images into `tool_images/`
3. Generates a `table.md` with a formatted Markdown table
4. Creates an `image_registry.txt` for tracking

## 📋 Requirements

- Python 3.x
- `requests`
- `beautifulsoup4`

## 🚀 Usage

~~~bash
pip install requests beautifulsoup4
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
