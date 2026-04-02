import re
import os
from fpdf import FPDF

PAGE_W = 180  # effective content width (A4 210 - 15 margins each side)


class _ReportPDF(FPDF):
    def header(self):
        self.set_font("Courier", "B", 9)
        self.set_text_color(130, 130, 130)
        self.cell(0, 8, "Agentic Research Paper Evaluator", align="R")
        self.ln(6)

    def footer(self):
        self.set_y(-13)
        self.set_font("Courier", "", 8)
        self.set_text_color(150, 150, 150)
        self.cell(0, 8, f"Page {self.page_no()}", align="C")


def _clean(text: str) -> str:
    """Strip markdown bold and non-ASCII characters for PDF output."""
    text = re.sub(r'\*\*(.*?)\*\*', r'\1', text)
    return text.encode("latin-1", errors="replace").decode("latin-1")


def export_pdf(markdown_text: str, title: str = "report") -> str:
    """Convert markdown report to PDF. Returns the output file path."""
    pdf = _ReportPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    pdf.set_left_margin(15)
    pdf.set_right_margin(15)

    for line in markdown_text.split("\n"):
        pdf.set_x(15)  # always reset to left margin before each line

        # H1
        if line.startswith("# "):
            pdf.set_font("Courier", "B", 14)
            pdf.set_text_color(20, 20, 20)
            pdf.multi_cell(PAGE_W, 8, _clean(line[2:].strip()))
            pdf.ln(1)

        # H2
        elif line.startswith("## "):
            pdf.ln(3)
            pdf.set_font("Courier", "B", 11)
            pdf.set_text_color(30, 30, 30)
            pdf.multi_cell(PAGE_W, 7, _clean(line[3:].strip()))
            pdf.ln(1)

        # H3
        elif line.startswith("### "):
            pdf.ln(2)
            pdf.set_font("Courier", "B", 10)
            pdf.set_text_color(50, 50, 50)
            pdf.multi_cell(PAGE_W, 6, _clean(line[4:].strip()))

        # Horizontal rule
        elif line.strip() == "---":
            pdf.ln(2)
            pdf.set_draw_color(190, 190, 190)
            pdf.line(15, pdf.get_y(), 195, pdf.get_y())
            pdf.ln(3)

        # Table rows
        elif line.startswith("|"):
            cells = [c.strip() for c in line.strip("|").split("|")]
            # Skip separator rows (---|---|---)
            if all(re.match(r'^[-: ]+$', c) for c in cells if c):
                continue
            pdf.set_font("Courier", "", 7)
            pdf.set_text_color(40, 40, 40)
            col_w = [88, 28, 49]  # total = 165, fits in 180
            for i, cell in enumerate(cells[:3]):
                cell_clean = _clean(cell)
                if i == 1:
                    if "Verified" in cell_clean:
                        cell_clean = "[OK]"
                    elif "Suspicious" in cell_clean:
                        cell_clean = "[!!]"
                    else:
                        cell_clean = "[??]"
                w = col_w[i] if i < len(col_w) else 40
                pdf.cell(w, 5, cell_clean[:70], border=1)
            pdf.ln()

        # Bullet points
        elif line.startswith("- "):
            pdf.set_font("Courier", "", 9)
            pdf.set_text_color(40, 40, 40)
            pdf.multi_cell(PAGE_W, 5, _clean("  * " + line[2:].strip()))

        # Normal text
        elif line.strip():
            pdf.set_font("Courier", "", 9)
            pdf.set_text_color(40, 40, 40)
            pdf.multi_cell(PAGE_W, 5, _clean(line.strip()))

        # Blank line
        else:
            pdf.ln(2)

    output_dir = os.path.join(os.path.dirname(__file__), "..", "sample_report")
    os.makedirs(output_dir, exist_ok=True)
    safe_title = re.sub(r'[^\w\s-]', '', title)[:40].strip().replace(" ", "_")
    output_path = os.path.join(output_dir, f"{safe_title}_report.pdf")
    pdf.output(output_path)
    return os.path.abspath(output_path)
