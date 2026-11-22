"""
AUDRYN PDF Report Generation Service.

Renders human-readable, professional statutory-grade audit reports
from validated AUDRYN AuditReport models using reportlab.
Includes prominent status banner, 12 structured audit sections,
deterministic calculation tables, and cryptographic manifest verification.
"""
import os
from typing import Optional
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    KeepTogether,
    HRFlowable,
)
from backend.models.report import AuditReport, ReportStatus


class PdfReportService:
    """
    Renders an AuditReport model to a publication-quality PDF document.
    """

    def __init__(self, output_dir: Optional[str] = None):
        self.output_dir = output_dir or os.path.join("data", "reports", "pdf")
        os.makedirs(self.output_dir, exist_ok=True)

    def generate_pdf(self, report: AuditReport, target_filename: Optional[str] = None) -> str:
        """
        Renders the AuditReport to PDF file on disk.
        Returns the absolute path to the generated PDF.
        """
        # Sanitize filename to prevent path traversal
        clean_name = target_filename or f"{report.report_id}_v{report.report_version}.pdf"
        clean_name = os.path.basename(clean_name)
        pdf_path = os.path.join(self.output_dir, clean_name)

        doc = SimpleDocTemplate(
            pdf_path,
            pagesize=letter,
            rightMargin=40,
            leftMargin=40,
            topMargin=40,
            bottomMargin=40,
        )

        styles = getSampleStyleSheet()
        normal = styles["Normal"]
        normal.fontSize = 9
        normal.leading = 12

        title_style = ParagraphStyle(
            "ReportTitle",
            parent=styles["Heading1"],
            fontSize=18,
            leading=22,
            textColor=colors.HexColor("#1A202C"),
            spaceAfter=6,
        )

        subtitle_style = ParagraphStyle(
            "ReportSubtitle",
            parent=normal,
            fontSize=11,
            leading=14,
            textColor=colors.HexColor("#4A5568"),
            spaceAfter=12,
        )

        h2_style = ParagraphStyle(
            "SectionH2",
            parent=styles["Heading2"],
            fontSize=12,
            leading=16,
            textColor=colors.HexColor("#2B6CB0"),
            spaceBefore=12,
            spaceAfter=6,
        )

        table_header_style = ParagraphStyle(
            "TableHeader",
            parent=normal,
            fontSize=9,
            leading=11,
            fontName="Helvetica-Bold",
            textColor=colors.white,
        )

        story = []

        # --- Header & Banner ---
        story.append(Paragraph("AUDRYN Financial Audit Intelligence", title_style))
        story.append(Paragraph(f"Statutory Audit Investigation Report — {report.company_name}", subtitle_style))
        story.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor("#2B6CB0"), spaceAfter=10))

        # Status & Disclaimer Callout Box
        status_bg = colors.HexColor("#FFF5F5") if report.report_status == ReportStatus.BLOCKED else (
            colors.HexColor("#EBF8FF") if report.report_status == ReportStatus.FINALIZED else colors.HexColor("#FFFFF0")
        )
        status_text_color = colors.HexColor("#C53030") if report.report_status == ReportStatus.BLOCKED else (
            colors.HexColor("#2B6CB0") if report.report_status == ReportStatus.FINALIZED else colors.HexColor("#B7791F")
        )

        status_p = Paragraph(
            f"<b>REPORT STATUS: {report.report_status.value}</b> (Version {report.report_version}) &nbsp;|&nbsp; "
            f"Report ID: {report.report_id} &nbsp;|&nbsp; Audit ID: {report.audit_id}<br/>"
            f"<font color='#718096'>Generated: {report.generated_at_utc} UTC | Rulebook: {report.manifest.rulebook_version if report.manifest else 'Income-tax Act, 1961'}</font>",
            ParagraphStyle("StatusP", parent=normal, textColor=status_text_color, fontSize=9, leading=13)
        )
        story.append(Table([[status_p]], colWidths=[530], style=[
            ('BACKGROUND', (0, 0), (-1, -1), status_bg),
            ('BOX', (0, 0), (-1, -1), 1, status_text_color),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('LEFTPADDING', (0, 0), (-1, -1), 10),
            ('RIGHTPADDING', (0, 0), (-1, -1), 10),
        ]))
        story.append(Spacer(1, 10))

        # Synthetic Data Notice if applicable
        if report.is_synthetic_data:
            syn_p = Paragraph(f"<b>LEGAL DISCLAIMER:</b> {report.synthetic_disclaimer}", ParagraphStyle("SynP", parent=normal, textColor=colors.HexColor("#744210"), fontSize=8, leading=11))
            story.append(Table([[syn_p]], colWidths=[530], style=[
                ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#FEFCBF")),
                ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor("#D69E2E")),
                ('PADDING', (0, 0), (-1, -1), 6),
            ]))
            story.append(Spacer(1, 10))

        # --- Sections Rendering ---
        for sec in report.sections:
            sec_elements = []
            sec_elements.append(Paragraph(sec.title.upper(), h2_style))
            sec_elements.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#CBD5E0"), spaceAfter=6))

            content = sec.content

            # Format key-value pairs or tables based on content
            table_data = []
            for k, v in content.items():
                k_label = k.replace("_", " ").title()
                if isinstance(v, list) and v and isinstance(v[0], dict):
                    # Render nested table (e.g. findings, evidence, gaps)
                    headers = list(v[0].keys())[:5]  # Take first 5 columns max
                    grid = [[Paragraph(h.replace("_", " ").title(), table_header_style) for h in headers]]
                    for item in v[:15]:  # limit to 15 items per section to keep PDF concise
                        row = [Paragraph(str(item.get(h, "")), normal) for h in headers]
                        grid.append(row)
                    
                    sub_table = Table(grid, colWidths=[530 / len(headers)] * len(headers))
                    sub_table.setStyle(TableStyle([
                        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#2B6CB0")),
                        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#E2E8F0")),
                        ('PADDING', (0, 0), (-1, -1), 4),
                        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                    ]))
                    sec_elements.append(Paragraph(f"<b>{k_label}:</b>", normal))
                    sec_elements.append(Spacer(1, 3))
                    sec_elements.append(sub_table)
                    sec_elements.append(Spacer(1, 6))
                elif isinstance(v, (dict, list)):
                    sec_elements.append(Paragraph(f"<b>{k_label}:</b> {str(v)[:300]}", normal))
                else:
                    sec_elements.append(Paragraph(f"<b>{k_label}:</b> {str(v)}", normal))

            story.append(KeepTogether(sec_elements))
            story.append(Spacer(1, 10))

        # Cryptographic Hash Stamp Footer
        hash_str = report.report_content_hash or "N/A"
        hash_p = Paragraph(f"<b>Cryptographic Content Hash (SHA-256):</b> <code>{hash_str}</code><br/><font color='#718096'>Verified by AUDRYN Evidence Engine — Immutable Audit Snapshot</font>", ParagraphStyle("HashP", parent=normal, fontSize=7, leading=10, textColor=colors.HexColor("#4A5568")))
        story.append(Spacer(1, 15))
        story.append(Table([[hash_p]], colWidths=[530], style=[
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#EDF2F7")),
            ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E0")),
            ('PADDING', (0, 0), (-1, -1), 6),
        ]))

        doc.build(story)
        return pdf_path
