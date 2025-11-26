from fpdf import FPDF

class PDF(FPDF):
    def header(self):
        self.set_font('Arial', 'B', 12)
        self.cell(0, 10, 'Generated Document', 0, 1, 'C')

    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.cell(0, 10, f'Page {self.page_no()}', 0, 0, 'C')

def clean_text(text):
    """
    Strips characters that aren't compatible with 'latin-1' (like emojis).
    """
    # This encodes to latin-1, ignoring errors (dropping emojis), then decodes back to string
    return text.encode('latin-1', 'ignore').decode('latin-1')

def create_pdf(text):
    """
    Converts markdown-style text to a simple PDF.
    """
    pdf = PDF()
    pdf.add_page()
    pdf.set_font("Arial", size=11)
    
    # 1. Sanitize the text (CRITICAL FIX)
    # This removes emojis that cause FPDF to crash
    safe_text = clean_text(text)
    
    # Simple Markdown cleanup
    clean_text_content = safe_text.replace("**", "").replace("## ", "").replace("# ", "")
    
    lines = clean_text_content.split('\n')
    
    for line in lines:
        stripped_line = line.strip()
        
        # Handle bullet points
        if stripped_line.startswith('*') or stripped_line.startswith('-'):
            pdf.set_font("Arial", size=11)
            pdf.cell(10) # Indent
            pdf.multi_cell(0, 7, stripped_line, 0, 1)
            
        # Handle Headers (rough heuristic)
        elif len(stripped_line) < 60 and (stripped_line.isupper() or "Overview" in stripped_line or "Endpoints" in stripped_line):
             pdf.set_font("Arial", 'B', size=12)
             pdf.ln(5)
             pdf.multi_cell(0, 7, stripped_line, 0, 1)
             pdf.set_font("Arial", size=11)
             
        # Standard text
        else:
            pdf.multi_cell(0, 7, stripped_line, 0, 1)
            
    # Output
    return pdf.output(dest='S').encode('latin-1', 'replace')