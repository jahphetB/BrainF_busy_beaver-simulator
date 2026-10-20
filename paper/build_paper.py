"""Build the editable manuscript as a paginated PDF and render review images."""

import hashlib
import html
import importlib.metadata
import json
import re
from pathlib import Path

import matplotlib
import pypdfium2 as pdfium
from pypdf import PdfReader
from reportlab.lib import colors
from reportlab.lib.enums import TA_JUSTIFY
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
	Image, PageBreak, Paragraph, Preformatted, SimpleDocTemplate, Spacer,
	Table, TableStyle,
)

PAPER = Path(__file__).resolve().parent
ROOT = PAPER.parent


def inline(value):
	"""Render the deliberately small Markdown subset used by report.md."""
	value = html.escape(value, quote=False)
	value = re.sub(r"`([^`]+)`", r'<font name="Mono">\1</font>', value)
	value = re.sub(r"\*\*([^*]+)\*\*", r"<b>\1</b>", value)
	value = re.sub(r"\*([^*]+)\*", r"<i>\1</i>", value)
	value = re.sub(r"\[([^\]]+)\]\((https?://[^)]+)\)",
		r'<link href="\2" color="#17618a">\1</link>', value)
	return value


def main():
	fonts = Path(matplotlib.get_data_path()) / "fonts/ttf"
	for name, filename in (
		("Body", "DejaVuSerif.ttf"), ("Body-Bold", "DejaVuSerif-Bold.ttf"),
		("Body-Italic", "DejaVuSerif-Italic.ttf"),
		("Body-BoldItalic", "DejaVuSerif-BoldItalic.ttf"),
		("Sans", "DejaVuSans.ttf"), ("Sans-Bold", "DejaVuSans-Bold.ttf"),
		("Mono", "DejaVuSansMono.ttf"),
	):
		pdfmetrics.registerFont(TTFont(name, str(fonts / filename)))
	pdfmetrics.registerFontFamily("Body", normal="Body", bold="Body-Bold",
		italic="Body-Italic", boldItalic="Body-BoldItalic")
	body = ParagraphStyle("Body", fontName="Body", fontSize=9.5, leading=13.6,
		spaceAfter=8, alignment=TA_JUSTIFY, textColor=colors.HexColor("#253247"))
	styles = {
		1: ParagraphStyle("Title", fontName="Sans-Bold", fontSize=22, leading=27,
			spaceAfter=12, textColor=colors.HexColor("#13364d")),
		2: ParagraphStyle("Subtitle", fontName="Sans", fontSize=14, leading=19,
			spaceAfter=17, textColor=colors.HexColor("#17618a")),
		3: ParagraphStyle("Heading", fontName="Sans-Bold", fontSize=12, leading=16,
			spaceBefore=9, spaceAfter=9, keepWithNext=True),
		4: ParagraphStyle("Subheading", fontName="Sans-Bold", fontSize=10, leading=14,
			spaceBefore=6, spaceAfter=7, keepWithNext=True),
	}
	caption = ParagraphStyle("Caption", parent=body, fontName="Sans",
		fontSize=8, leading=11, spaceAfter=10, alignment=0)
	cell = ParagraphStyle("Cell", parent=body, fontSize=8, leading=11,
		spaceAfter=0, alignment=0)
	code = ParagraphStyle("Code", fontName="Mono", fontSize=7.8, leading=11,
		spaceBefore=3, spaceAfter=9, backColor=colors.HexColor("#f1f5f8"),
		borderPadding=7)
	output = PAPER / "brainfuck-productivity.pdf"
	width = A4[0] - 104
	doc = SimpleDocTemplate(str(output), pagesize=A4,
		leftMargin=52, rightMargin=52, topMargin=47, bottomMargin=48,
		title="From Short Programs to Complex Computation",
		author="Brainfuck Computational Productivity Research",
		subject="A reproducible empirical study of bounded Brainfuck execution",
		invariant=1)
	lines = (PAPER / "report.md").read_text(encoding="utf-8").splitlines()
	story = []
	index = 0
	while index < len(lines):
		line = lines[index].strip()
		index += 1
		if not line:
			continue
		if line == "<!-- pagebreak -->":
			story.append(PageBreak())
		elif line.startswith("#"):
			level = len(line) - len(line.lstrip("#"))
			story.append(Paragraph(inline(line[level:].strip()), styles[level]))
		elif line.startswith("```"):
			block = []
			while index < len(lines) and not lines[index].startswith("```"):
				block.append(lines[index].expandtabs(4))
				index += 1
			index += 1
			story.append(Preformatted("\n".join(block), code))
		elif line.startswith("!["):
			match = re.fullmatch(r"!\[(.*)\]\((.*)\)", line)
			if match is None:
				raise ValueError(f"Invalid image line: {line}")
			from PIL import Image as PILImage
			path = PAPER / match[2]
			with PILImage.open(path) as picture:
				image_height = width * picture.height / picture.width
			story.append(Image(str(path), width=width, height=image_height))
			story.append(Paragraph(inline(match[1]), caption))
		elif line.startswith("|"):
			table_lines = [line]
			while index < len(lines) and lines[index].startswith("|"):
				table_lines.append(lines[index])
				index += 1
			values = [[p.strip() for p in row.strip("|").split("|")] for row in table_lines]
			values = [row for row in values if not all(re.fullmatch(r"[-: ]+", p) for p in row)]
			data = [[Paragraph(inline(p), cell) for p in row] for row in values]
			table = Table(data, hAlign="LEFT", repeatRows=1)
			table.setStyle(TableStyle([
				("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#e6eff4")),
				("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f6f8fa")]),
				("LINEBELOW", (0, 0), (-1, 0), 0.7, colors.HexColor("#17618a")),
				("LEFTPADDING", (0, 0), (-1, -1), 8),
				("RIGHTPADDING", (0, 0), (-1, -1), 8),
				("TOPPADDING", (0, 0), (-1, -1), 5),
				("BOTTOMPADDING", (0, 0), (-1, -1), 5),
				("VALIGN", (0, 0), (-1, -1), "TOP"),
			]))
			story.extend([table, Spacer(1, 8)])
		else:
			paragraph = [line]
			while index < len(lines) and lines[index].strip():
				paragraph.append(lines[index].strip())
				index += 1
			style = caption if line.startswith(("Table ", "Computational research report")) else body
			story.append(Paragraph(inline(" ".join(paragraph)), style))

	def footer(canvas, document):
		canvas.saveState()
		canvas.setStrokeColor(colors.HexColor("#d2dbe2"))
		canvas.line(52, 37, A4[0] - 52, 37)
		canvas.setFont("Sans", 7.5)
		canvas.setFillColor(colors.HexColor("#64748b"))
		canvas.drawString(52, 24, "BRAINFUCK COMPUTATIONAL PRODUCTIVITY | RESEARCH REPORT v1.0")
		canvas.drawRightString(A4[0] - 52, 24, str(document.page))
		canvas.restoreState()

	doc.build(story, onFirstPage=footer, onLaterPages=footer)
	reader = PdfReader(output)
	if len(reader.pages) != 8:
		raise ValueError(f"Expected 8 pages, found {len(reader.pages)}; review pagination.")
	render = ROOT / "tmp/pdfs"
	render.mkdir(parents=True, exist_ok=True)
	pdf = pdfium.PdfDocument(output)
	for index in range(len(pdf)):
		page = pdf[index]
		bitmap = page.render(scale=1.6)
		bitmap.to_pil().save(render / f"paper-page-{index + 1}.png")
		bitmap.close()
		page.close()
	pdf.close()
	packages = {name: importlib.metadata.version(name)
		for name in ("matplotlib", "reportlab", "pypdf", "pypdfium2")}
	paths = [PAPER / name for name in
		("report.md", "references.bib", "LITERATURE_AUDIT.md", "statistics.json",
		"make_figures.py", "build_paper.py", "verify_paper.py", "requirements.txt",
		"brainfuck-productivity.pdf")]
	paths += sorted((PAPER / "figures").glob("*"))
	record = {
		"pages": len(reader.pages), "render_engine": "PDFium (Poppler unavailable on host)",
		"packages": packages,
		"page_text_characters": [len(page.extract_text()) for page in reader.pages],
		"artifacts_sha256": {str(path.relative_to(ROOT)).replace("\\", "/"):
			hashlib.sha256(path.read_bytes()).hexdigest() for path in paths},
		"note": "Build and hash record; visual review is documented separately in docs/PHASE_4.md.",
	}
	(PAPER / "build-manifest.json").write_text(
		json.dumps(record, indent="\t") + "\n", encoding="utf-8", newline="\n")
	print(f"Built {len(reader.pages)} pages and rendered all pages to tmp/pdfs.")


if __name__ == "__main__":
	main()
