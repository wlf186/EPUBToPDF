# EPUB to PDF Converter

A cross-platform Python tool to convert EPUB files to PDF while preserving images and formatting.

## Features

- Converts EPUB files to PDF format
- Preserves images embedded in EPUB
- Maintains chapter structure
- Cross-platform support (Windows / Linux / macOS)
- Handles CSS styling from EPUB

## Requirements

- Python 3.8 or higher
- pip (Python package installer)

## Installation

1. Clone this repository:
```bash
git clone https://github.com/wlf186/EPUBToPDF.git
cd EPUBToPDF
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

**Note for Linux users:** WeasyPrint requires some system packages. Install them first:

**Ubuntu/Debian:**
```bash
sudo apt-get install python3-dev python3-pip python3-cffi libcairo2 libpango-1.0-0 libpangocairo-1.0-0 libgdk-pixbuf2.0-0 libffi-dev shared-mime-info
```

**Fedora:**
```bash
sudo dnf install python3-devel cairo-devel pango-devel gdk-pixbuf2-devel
```

**macOS:**
```bash
brew install cairo pango gdk-pixbuf libffi
```

## Usage

### Command Line

Basic usage (PDF will have same name as EPUB):
```bash
python epub_to_pdf.py book.epub
```

Specify output file:
```bash
python epub_to_pdf.py book.epub -o output.pdf
```

### As a Python Module

```python
from epub_to_pdf import epub_to_pdf

# Convert with default output name
epub_to_pdf("book.epub")

# Convert with custom output name
epub_to_pdf("book.epub", "output.pdf")
```

## Example

```bash
$ python epub_to_pdf.py "Dollars and Sense.epub"

Converting: Dollars and Sense.epub
Output: Dollars and Sense.pdf
Book title: Dollars and Sense - How We Misthink Money and How to Spend Smarter
Chapters found: 33
Images found: 31
Success! PDF created: Dollars and Sense.pdf (1,240,035 bytes)
```

## Dependencies

- **ebooklib** - EPUB file parsing
- **weasyprint** - PDF generation from HTML/CSS
- **beautifulsoup4** - HTML processing

## License

MIT License

## Contributing

Pull requests are welcome!
