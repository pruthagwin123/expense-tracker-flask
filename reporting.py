from fpdf import FPDF
from datetime import datetime


def generate_monthly_report(user, expenses, month_year):
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    pdf.set_font("Arial", "B", 16)
    pdf.cell(
        0, 10, f"Expense Report - {user['username']} - {month_year}", ln=True)
    pdf.ln(5)

    pdf.set_font("Arial", "", 12)
    total = 0

    # Table Header
    pdf.cell(35, 8, "Date", 1, 0, "C")
    pdf.cell(40, 8, "Category", 1, 0, "C")
    pdf.cell(75, 8, "Description", 1, 0, "C")
    pdf.cell(30, 8, "Amount", 1, 1, "C")

    # Table Rows
    for e in expenses:
        y_start = pdf.get_y()
        line_height = 8

        # Wrap description properly
        desc = (e.get('description') or '')
        desc_lines = pdf.multi_cell(
            75, line_height, desc, border=0, align="L", split_only=True)
        row_height = line_height * len(desc_lines)

        # Draw cells manually to align height properly
        pdf.cell(35, row_height, str(e['date']), border=1)
        pdf.cell(40, row_height, str(
            e.get('category') or 'Uncategorized'), border=1)

        x = pdf.get_x()
        y = y_start
        pdf.multi_cell(75, line_height, desc, border=1)
        pdf.set_xy(x + 75, y)

        pdf.cell(30, row_height, f"{e['amount']:.2f}",
                 border=1, ln=1, align="R")
        total += float(e['amount'])

    pdf.ln(5)
    pdf.set_font("Arial", "B", 12)

    pdf.cell(0, 8, f"Total: {total:.2f}", ln=True)

    return bytes(pdf.output(dest='S'))
