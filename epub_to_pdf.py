#!/usr/bin/env python3
"""
EPUB to PDF Converter
Convert EPUB files to PDF using ebooklib and weasyprint.
Supports embedding images from EPUB.
"""

import os
import sys
import argparse
import base64
from ebooklib import epub
from weasyprint import HTML
from io import StringIO
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from typing import Dict, Tuple, List


def extract_epub_content(epub_path):
    """Extract HTML content, CSS, and images from EPUB file."""
    try:
        book = epub.read_epub(epub_path)
    except Exception as e:
        print(f"Error reading EPUB: {e}")
        return None, None, None, None

    # Get title
    title = book.get_metadata('DC', 'title')
    title = title[0][0] if title else os.path.basename(epub_path)

    # Get all items
    items = list(book.get_items())
    html_content = []
    css_content = []
    images = {}  # Map image filename to base64 data

    # Extract CSS first
    for item in items:
        if isinstance(item, epub.EpubItem):
            if item.get_type() == 9:  # stylesheet
                try:
                    css_content.append(item.get_content())
                except:
                    pass

    # Extract images
    for item in items:
        if isinstance(item, epub.EpubImage):
            try:
                # Get image content and media type
                img_data = item.get_content()
                img_name = item.get_name()

                # Determine media type
                media_type = item.media_type
                if not media_type:
                    # Try to determine from file extension
                    ext = os.path.splitext(img_name)[1].lower()
                    mime_map = {
                        '.jpg': 'image/jpeg',
                        '.jpeg': 'image/jpeg',
                        '.png': 'image/png',
                        '.gif': 'image/gif',
                        '.svg': 'image/svg+xml',
                        '.webp': 'image/webp',
                    }
                    media_type = mime_map.get(ext, 'image/jpeg')

                # Store as base64 data URL
                b64_data = base64.b64encode(img_data).decode('ascii')
                images[img_name] = f"data:{media_type};base64,{b64_data}"
            except Exception as e:
                print(f"Warning: Could not extract image {item.get_name()}: {e}")

    # Extract HTML content in spine order
    spine = book.spine if hasattr(book, 'spine') else []
    processed_items = set()

    for item in spine:
        if isinstance(item, tuple):
            item_id = item[0]
        else:
            item_id = item

        if item_id in processed_items:
            continue
        processed_items.add(item_id)

        book_item = book.get_item_with_id(item_id)
        if book_item and isinstance(book_item, epub.EpubHtml):
            try:
                content = book_item.get_content().decode('utf-8', errors='ignore')
                # Replace image references with data URIs
                content = process_html_images(content, book_item.file_name, images, book)
                html_content.append(content)
            except Exception as e:
                print(f"Warning: Could not read item {item_id}: {e}")
        elif book_item is None and item_id.startswith('nav'):
            continue

    # If spine is empty, get all HTML items
    if not html_content:
        for item in items:
            if isinstance(item, epub.EpubHtml):
                try:
                    content = item.get_content().decode('utf-8', errors='ignore')
                    content = process_html_images(content, item.file_name, images, book)
                    html_content.append(content)
                except:
                    pass

    return title, html_content, css_content, images


def process_html_images(html_content: str, html_file_name: str,
                         images: Dict[str, str], book) -> str:
    """Replace image references in HTML with data URIs."""
    soup = BeautifulSoup(html_content, 'html.parser')

    for img in soup.find_all('img'):
        src = img.get('src')
        if not src:
            continue

        # Handle different src formats
        # Relative path like ../images/cover.jpg
        if src.startswith('../'):
            # Navigate from the HTML file location
            html_dir = os.path.dirname(html_file_name)
            img_path = os.path.normpath(os.path.join(html_dir, src))
            # Convert to forward slashes for EPUB
            img_path = img_path.replace('\\', '/')
        elif src.startswith('/'):
            img_path = src.lstrip('/')
        else:
            # Same directory
            html_dir = os.path.dirname(html_file_name)
            img_path = os.path.join(html_dir, src) if html_dir else src
            img_path = img_path.replace('\\', '/')

        # Try to find the image
        if img_path in images:
            img['src'] = images[img_path]
        else:
            # Try to find by filename only
            img_name = os.path.basename(src)
            if img_name in images:
                img['src'] = images[img_name]
            else:
                # Try to get from book directly
                for item in book.get_items():
                    if isinstance(item, epub.EpubImage):
                        item_name = item.get_name()
                        if item_name == img_path or item_name.endswith(img_name) or src in item_name:
                            try:
                                img_data = item.get_content()
                                media_type = item.media_type or 'image/jpeg'
                                b64_data = base64.b64encode(img_data).decode('ascii')
                                data_uri = f"data:{media_type};base64,{b64_data}"
                                img['src'] = data_uri
                                images[item_name] = data_uri
                                break
                            except:
                                pass

    return str(soup)


def create_pdf(title, html_content, css_content, output_path, images=None):
    """Create PDF from HTML content, CSS, and embedded images."""
    # Combine all HTML content
    combined_html = StringIO()

    combined_html.write('''<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <style>
        @page {
            margin: 2cm;
        }
        body {
            font-family: serif;
            line-height: 1.6;
            max-width: 100%;
            padding: 1em;
        }
        img {
            max-width: 100%;
            height: auto;
            display: block;
            margin: 0.5em auto;
        }
        table {
            border-collapse: collapse;
            width: 100%;
        }
        p, div, h1, h2, h3, h4, h5, h6 {
            max-width: 100%;
            word-wrap: break-word;
        }
    ''')

    # Add custom CSS
    for css in css_content:
        try:
            css_str = css.decode('utf-8', errors='ignore') if isinstance(css, bytes) else css
            combined_html.write(css_str)
        except:
            pass

    combined_html.write('</style></head><body>')

    # Add page breaks between chapters
    for i, html in enumerate(html_content):
        if i > 0:
            combined_html.write('<div style="page-break-after: always;"></div>')

        # Parse HTML and extract body content
        soup = BeautifulSoup(html, 'html.parser')
        body = soup.find('body')
        if body:
            # Unwrap body but keep its contents
            for child in body.children:
                combined_html.write(str(child))
        else:
            combined_html.write(html)

    combined_html.write('</body></html>')

    # Generate PDF
    try:
        html_obj = HTML(string=combined_html.getvalue())
        html_obj.write_pdf(output_path)
        return True
    except Exception as e:
        print(f"Error generating PDF: {e}")
        return False


def epub_to_pdf(epub_path, pdf_path=None):
    """Convert EPUB file to PDF."""
    if not os.path.exists(epub_path):
        print(f"Error: File not found: {epub_path}")
        return False

    if pdf_path is None:
        pdf_path = os.path.splitext(epub_path)[0] + '.pdf'

    print(f"Converting: {epub_path}")
    print(f"Output: {pdf_path}")

    # Extract content
    title, html_content, css_content, images = extract_epub_content(epub_path)

    if not html_content:
        print("Error: No HTML content found in EPUB")
        return False

    print(f"Book title: {title}")
    print(f"Chapters found: {len(html_content)}")
    print(f"Images found: {len(images)}")

    # Create PDF
    if create_pdf(title, html_content, css_content, pdf_path, images):
        file_size = os.path.getsize(pdf_path)
        print(f"Success! PDF created: {pdf_path} ({file_size:,} bytes)")
        return True
    else:
        return False


def main():
    import glob

    parser = argparse.ArgumentParser(description='Convert EPUB to PDF')
    parser.add_argument('epub_file', nargs='?', help='Path to EPUB file (default: all .epub files in input/ directory)')
    parser.add_argument('-o', '--output', help='Output PDF path (default: output/ directory with same name)')
    args = parser.parse_args()

    # If no epub_file specified, convert all epub files in input/ directory
    if args.epub_file is None:
        input_dir = 'input'
        output_dir = 'output'

        # Create output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)

        # Find all epub files in input directory
        pattern = os.path.join(input_dir, '*.epub')
        epub_files = glob.glob(pattern)

        if not epub_files:
            print(f"No EPUB files found in '{input_dir}/' directory.")
            return

        print(f"Found {len(epub_files)} EPUB file(s) in '{input_dir}/' directory.")
        print(f"Output will be saved to '{output_dir}/' directory.\n")

        success_count = 0
        for epub_file in epub_files:
            print("=" * 60)
            # Generate output path in output directory
            base_name = os.path.splitext(os.path.basename(epub_file))[0]
            output_path = os.path.join(output_dir, base_name + '.pdf')
            if epub_to_pdf(epub_file, output_path):
                success_count += 1
            print()
        print("=" * 60)
        print(f"Conversion complete: {success_count}/{len(epub_files)} succeeded")
    else:
        # Single file mode - use specified output or default to input directory
        if args.output:
            output_path = args.output
        else:
            # If no output specified, place in output/ directory
            base_name = os.path.splitext(os.path.basename(args.epub_file))[0]
            os.makedirs('output', exist_ok=True)
            output_path = os.path.join('output', base_name + '.pdf')
        epub_to_pdf(args.epub_file, output_path)


if __name__ == '__main__':
    main()
