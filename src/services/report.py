"""PDF report generation and email delivery."""

import io
import logging
from datetime import datetime
from typing import Dict, Any

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER

from src.config import get_settings
from src.database.models.user import UserModel
from src.database.models.waste import WasteClassificationModel
from src.database.models.system import UserInteractionModel
from src.services.email import send_email

logger = logging.getLogger(__name__)


class ReportService:

    def __init__(self):
        self.user_model = UserModel()
        self.waste_model = WasteClassificationModel()
        self.interaction_model = UserInteractionModel()

    def generate_and_send(self) -> Dict[str, Any]:
        """Generate a PDF report and send it via email."""
        try:
            pdf_bytes = self._generate_pdf()
            result = send_email(
                subject=f"EcoBot Report — {datetime.now().strftime('%Y-%m-%d')}",
                html="<p>Laporan EcoBot terlampir.</p>",
                attachments=[{
                    "filename": f"ecobot_report_{datetime.now().strftime('%Y%m%d')}.pdf",
                    "content": list(pdf_bytes),
                }],
            )
            return result
        except Exception as e:
            logger.error("Report generation error: %s", e)
            return {"success": False, "error": str(e)}

    def _generate_pdf(self) -> bytes:
        buf = io.BytesIO()
        doc = SimpleDocTemplate(buf, pagesize=A4, topMargin=0.75 * inch, bottomMargin=0.75 * inch)
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle("Title2", parent=styles["Title"], fontSize=18, alignment=TA_CENTER)
        elements = []

        settings = get_settings()
        now = datetime.now().strftime("%d %B %Y %H:%M")

        # Title
        elements.append(Paragraph(f"EcoBot Report — {settings.app.village_name or 'System'}", title_style))
        elements.append(Spacer(1, 12))
        elements.append(Paragraph(f"Generated: {now}", styles["Normal"]))
        elements.append(Spacer(1, 24))

        # User stats
        total_users = self.user_model.count_users()
        elements.append(Paragraph(f"Total Users: {total_users}", styles["Heading2"]))
        elements.append(Spacer(1, 12))

        # Waste classification stats
        waste_stats = self.waste_model.get_statistics(days=7)
        if waste_stats:
            data = [
                ["Metric", "Count"],
                ["Total Classifications", str(waste_stats.get("total", 0))],
                ["Organik", str(waste_stats.get("organic", 0))],
                ["Anorganik", str(waste_stats.get("inorganic", 0))],
                ["B3", str(waste_stats.get("b3", 0))],
            ]
            table = Table(data, colWidths=[3 * inch, 2 * inch])
            table.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#2d6a4f")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                ("FONTSIZE", (0, 0), (-1, -1), 10),
            ]))
            elements.append(Paragraph("Waste Classifications (Last 7 Days)", styles["Heading2"]))
            elements.append(Spacer(1, 6))
            elements.append(table)

        # Interaction stats
        elements.append(Spacer(1, 24))
        int_stats = self.interaction_model.get_stats(days=7)
        if int_stats:
            elements.append(Paragraph("Interaction Stats (Last 7 Days)", styles["Heading2"]))
            elements.append(Spacer(1, 6))
            elements.append(Paragraph(f"Active Users: {int_stats.get('active_users', 0)}", styles["Normal"]))
            elements.append(Paragraph(f"Total Interactions: {int_stats.get('total_interactions', 0)}", styles["Normal"]))
            elements.append(Paragraph(f"Images Processed: {int_stats.get('images_processed', 0)}", styles["Normal"]))

        doc.build(elements)
        return buf.getvalue()
