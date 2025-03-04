import os
import csv
import re
import requests
import xml.etree.ElementTree as ET
from fpdf import FPDF
from datetime import datetime
import traceback

# Log helper function
def log(message, emoji="ℹ️"):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {emoji} {message}")

# Ensure that the Unicode font is available; download if not present
def ensure_font(font_filename="DejaVuSans.ttf"):
    if not os.path.exists(font_filename):
        log(f"Downloading {font_filename} for Unicode support", "🌍")
        # Use Matplotlib's DejaVuSans.ttf as a reliable TrueType font source
        font_url = "https://github.com/matplotlib/matplotlib/blob/main/lib/matplotlib/mpl-data/fonts/ttf/DejaVuSans.ttf?raw=true"
        try:
            r = requests.get(font_url, timeout=10)
            r.raise_for_status()
            with open(font_filename, "wb") as f:
                f.write(r.content)
            log(f"{font_filename} downloaded successfully.", "✅")
        except requests.exceptions.RequestException as e:
            log(f"Failed to download {font_filename}: {e}", "❌")
            raise

# Function to fetch subtitles from a URL
def fetch_subtitles(url):
    try:
        log(f"Fetching subtitles from {url}", "🌍")
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        return response.text
    except requests.exceptions.RequestException as e:
        log(f"Failed to fetch subtitles: {e}", "❌")
        return None

# Function to parse the EBU-TT subtitle XML format
def parse_ebu_tt(xml_content):
    try:
        log("Parsing EBU-TT subtitle XML...", "📜")
        root = ET.fromstring(xml_content)
        namespace = {'tt': 'http://www.w3.org/ns/ttml'}

        subtitles = []
        for p in root.findall(".//tt:p", namespace):
            start_time = p.attrib.get("begin", "00:00:00.000")
            text_content = " ".join(p.itertext()).strip()
            if text_content:
                subtitles.append(f"[{str(start_time)}]: {str(text_content)}")
        return subtitles
    except ET.ParseError as e:
        log(f"Error parsing XML: {e}", "❌")
        return None

# Function to parse WebVTT subtitle files
def parse_vtt(vtt_content):
    try:
        log("Parsing VTT subtitles...", "📜")
        subtitles = []
        lines = vtt_content.splitlines()
        # Remove header if present
        if lines and lines[0].strip().startswith("WEBVTT"):
            lines = lines[1:]
        
        block = []
        for line in lines:
            if line.strip() == "":
                if block:
                    time_line = None
                    text_lines = []
                    for item in block:
                        if "-->" in item:
                            time_line = item.strip()
                        else:
                            text_lines.append(item.strip())
                    # Filter out lines that are just an index number
                    text_lines = [t for t in text_lines if not t.isdigit()]
                    if time_line:
                        parts = time_line.split("-->")
                        start_time = parts[0].strip() if parts else "00:00:00.000"
                        text_content = " ".join(text_lines).strip()
                        if text_content:
                            subtitles.append(f"[{start_time}]: {text_content}")
                    block = []
            else:
                block.append(line)
        # Process any remaining block
        if block:
            time_line = None
            text_lines = []
            for item in block:
                if "-->" in item:
                    time_line = item.strip()
                else:
                    text_lines.append(item.strip())
            text_lines = [t for t in text_lines if not t.isdigit()]
            if time_line:
                parts = time_line.split("-->")
                start_time = parts[0].strip() if parts else "00:00:00.000"
                text_content = " ".join(text_lines).strip()
                if text_content:
                    subtitles.append(f"[{start_time}]: {text_content}")
        return subtitles
    except Exception as e:
        log(f"Error parsing VTT: {e}", "❌")
        return None

# Function to generate a PDF from subtitles with full Unicode support
def create_pdf(title, subtitles, output_folder):
    try:
        title_str = str(title)
        safe_title = "".join(c if c.isalnum() or c in " _-" else "_" for c in title_str)
        filename = os.path.join(output_folder, f"{safe_title}.pdf")
        log(f"Generating PDF: {filename}", "🖨️")

        font_filename = "DejaVuSans.ttf"
        ensure_font(font_filename)

        pdf = FPDF()
        pdf.set_auto_page_break(auto=True, margin=15)
        pdf.add_page()
        
        pdf.add_font("DejaVu", "", font_filename, uni=True)
        pdf.set_font("DejaVu", "", 12)

        pdf.cell(0, 10, title_str, ln=True, align="C")
        pdf.ln(5)

        for i, subtitle in enumerate(subtitles):
            try:
                # log(f"Adding subtitle {i}: {subtitle} (type: {type(subtitle)})", "🔍")
                # Remove any font tags using regex
                subtitle_clean = re.sub(r'</?font[^>]*>', '', str(subtitle))
                pdf.multi_cell(0, 10, subtitle_clean)
                pdf.ln(2)
            except Exception as e:
                log(f"Error adding subtitle at index {i}: {subtitle} (type: {type(subtitle)}): {e}", "❌")
                log("Full traceback:", "❌")
                log(traceback.format_exc(), "❌")
                raise

        pdf.output(filename, "F")
        log(f"PDF saved: {filename}", "✅")
    except Exception as e:
        log(f"Error generating PDF: {e}", "❌")
        log("Full traceback:", "❌")
        log(traceback.format_exc(), "❌")

# Main function to process the CSV
def process_csv(csv_filename):
    if not os.path.exists(csv_filename):
        log(f"CSV file not found: {csv_filename}", "❌")
        return

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_folder = f"pdf_output_{timestamp}"
    os.makedirs(output_folder, exist_ok=True)
    log(f"PDF output folder created: {output_folder}", "📁")

    with open(csv_filename, mode="r", encoding="utf-8") as file:
        reader = csv.reader(file, delimiter=";")
        next(reader)  # Skip header row
        
        for row in reader:
            if len(row) < 2:
                log("Invalid row format, skipping.", "❌")
                continue

            title, url = row
            log(f"Processing: {title}", "🎬")

            content = fetch_subtitles(url)
            if content:
                if url.lower().endswith(".vtt") or content.strip().startswith("WEBVTT"):
                    subtitles = parse_vtt(content)
                else:
                    subtitles = parse_ebu_tt(content)
                if subtitles:
                    create_pdf(title, subtitles, output_folder)
                else:
                    log(f"No subtitles found for {title}", "❌")

# Run the script
if __name__ == "__main__":
    csv_file = "subtitles.csv"
    log("Starting subtitle to PDF conversion tool", "🚀")
    process_csv(csv_file)
    log("Processing complete!", "🏁")