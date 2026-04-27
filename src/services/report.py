"""PDF report generation and email delivery."""

import io
import logging
from datetime import datetime
from typing import Dict, Any

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, mm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable,
)
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_RIGHT

from src.config import get_settings
from src.database.models.user import UserModel
from src.database.models.waste import WasteClassificationModel
from src.database.models.system import UserInteractionModel
from src.services.email import send_email

logger = logging.getLogger(__name__)

# Brand colours
_GREEN = colors.HexColor("#1B5E20")
_GREEN_LIGHT = colors.HexColor("#E8F5E9")
_GREEN_MID = colors.HexColor("#2E7D32")
_GREY = colors.HexColor("#F5F5F5")
_DARK = colors.HexColor("#212121")
_MUTED = colors.HexColor("#757575")


class ReportService:

    def __init__(self):
        self.user_model = UserModel()
        self.waste_model = WasteClassificationModel()
        self.interaction_model = UserInteractionModel()

    # ------------------------------------------------------------------
    # Public
    # ------------------------------------------------------------------
    def generate_and_send(self) -> Dict[str, Any]:
        """Generate a PDF report and send it via email."""
        try:
            stats = self._collect_stats()
            pdf_bytes = self._generate_pdf(stats)
            html_body = self._build_email_html(stats)
            settings = get_settings()
            date_str = datetime.now().strftime("%Y-%m-%d")
            village = settings.app.village_name or "EcoBot"

            result = send_email(
                subject=f"Laporan {village} — {date_str}",
                html=html_body,
                attachments=[{
                    "filename": f"ecobot_report_{datetime.now().strftime('%Y%m%d')}.pdf",
                    "content": list(pdf_bytes),
                }],
            )
            return result
        except Exception as e:
            logger.error("Report generation error: %s", e)
            return {"success": False, "error": str(e)}

    # ------------------------------------------------------------------
    # Data collection
    # ------------------------------------------------------------------
    def _collect_stats(self) -> Dict[str, Any]:
        total_users = self.user_model.count_users()
        waste = self.waste_model.get_statistics(days=7)
        interactions = self.interaction_model.get_stats(days=7)
        settings = get_settings()
        return {
            "village": settings.app.village_name or "EcoBot",
            "date": datetime.now().strftime("%d %B %Y"),
            "time": datetime.now().strftime("%H:%M WIB"),
            "total_users": total_users,
            "waste_total": waste.get("total", 0) if waste else 0,
            "waste_organic": waste.get("organic", 0) if waste else 0,
            "waste_inorganic": waste.get("inorganic", 0) if waste else 0,
            "waste_b3": waste.get("b3", 0) if waste else 0,
            "active_users": interactions.get("active_users", 0) if interactions else 0,
            "total_interactions": interactions.get("total_interactions", 0) if interactions else 0,
            "images_processed": interactions.get("images_processed", 0) if interactions else 0,
        }

    # ------------------------------------------------------------------
    # PDF
    # ------------------------------------------------------------------
    def _generate_pdf(self, stats: Dict[str, Any]) -> bytes:
        buf = io.BytesIO()
        doc = SimpleDocTemplate(
            buf, pagesize=A4,
            topMargin=30 * mm, bottomMargin=25 * mm,
            leftMargin=20 * mm, rightMargin=20 * mm,
        )
        styles = getSampleStyleSheet()

        # Custom styles
        s_title = ParagraphStyle(
            "RptTitle", parent=styles["Title"],
            fontSize=22, textColor=_GREEN, spaceAfter=4,
        )
        s_subtitle = ParagraphStyle(
            "RptSub", parent=styles["Normal"],
            fontSize=10, textColor=_MUTED, alignment=TA_CENTER, spaceAfter=16,
        )
        s_section = ParagraphStyle(
            "RptSection", parent=styles["Heading2"],
            fontSize=13, textColor=_GREEN, spaceBefore=20, spaceAfter=8,
            borderPadding=(0, 0, 2, 0),
        )
        s_body = ParagraphStyle(
            "RptBody", parent=styles["Normal"],
            fontSize=10, textColor=_DARK, leading=14,
        )
        s_footer = ParagraphStyle(
            "RptFooter", parent=styles["Normal"],
            fontSize=8, textColor=_MUTED, alignment=TA_CENTER,
        )

        elements = []

        # ── Header ───────────────────────────────────────────────
        elements.append(Paragraph(f"Laporan {stats['village']}", s_title))
        elements.append(Paragraph(f"{stats['date']} • {stats['time']}", s_subtitle))
        elements.append(HRFlowable(width="100%", thickness=1, color=_GREEN, spaceAfter=12))

        # ── Summary cards (table layout) ─────────────────────────
        card_data = [
            ["Total Pengguna", "Pengguna Aktif (7h)", "Total Interaksi", "Foto Diproses"],
            [
                str(stats["total_users"]),
                str(stats["active_users"]),
                str(stats["total_interactions"]),
                str(stats["images_processed"]),
            ],
        ]
        card_table = Table(card_data, colWidths=[doc.width / 4] * 4)
        card_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), _GREEN),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTSIZE", (0, 0), (-1, 0), 8),
            ("FONTSIZE", (0, 1), (-1, 1), 18),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("BACKGROUND", (0, 1), (-1, 1), _GREEN_LIGHT),
            ("TEXTCOLOR", (0, 1), (-1, 1), _GREEN),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.white),
            ("TOPPADDING", (0, 0), (-1, 0), 8),
            ("BOTTOMPADDING", (0, 0), (-1, 0), 8),
            ("TOPPADDING", (0, 1), (-1, 1), 12),
            ("BOTTOMPADDING", (0, 1), (-1, 1), 12),
        ]))
        elements.append(card_table)

        # ── Waste Classifications ────────────────────────────────
        elements.append(Paragraph("Klasifikasi Sampah (7 Hari Terakhir)", s_section))

        waste_data = [
            ["Jenis Sampah", "Jumlah", "Persentase"],
            ["Organik", str(stats["waste_organic"]), self._pct(stats["waste_organic"], stats["waste_total"])],
            ["Anorganik", str(stats["waste_inorganic"]), self._pct(stats["waste_inorganic"], stats["waste_total"])],
            ["B3 (Berbahaya)", str(stats["waste_b3"]), self._pct(stats["waste_b3"], stats["waste_total"])],
            ["Total", str(stats["waste_total"]), "100%"],
        ]
        waste_table = Table(waste_data, colWidths=[doc.width * 0.45, doc.width * 0.25, doc.width * 0.30])
        waste_table.setStyle(TableStyle([
            # Header
            ("BACKGROUND", (0, 0), (-1, 0), _GREEN),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTSIZE", (0, 0), (-1, 0), 9),
            # Body
            ("FONTSIZE", (0, 1), (-1, -1), 10),
            ("TEXTCOLOR", (0, 1), (-1, -1), _DARK),
            ("ALIGN", (1, 0), (-1, -1), "CENTER"),
            # Alternating rows
            ("BACKGROUND", (0, 1), (-1, 1), _GREEN_LIGHT),
            ("BACKGROUND", (0, 3), (-1, 3), _GREEN_LIGHT),
            # Total row bold
            ("BACKGROUND", (0, -1), (-1, -1), _GREY),
            ("FONTSIZE", (0, -1), (-1, -1), 10),
            # Grid
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#E0E0E0")),
            ("TOPPADDING", (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ]))
        elements.append(waste_table)

        # ── Interaction Stats ────────────────────────────────────
        elements.append(Paragraph("Aktivitas Pengguna (7 Hari Terakhir)", s_section))

        int_data = [
            ["Metrik", "Nilai"],
            ["Pengguna Aktif", str(stats["active_users"])],
            ["Total Interaksi", str(stats["total_interactions"])],
            ["Foto Diproses", str(stats["images_processed"])],
            ["Rata-rata Interaksi/User",
             f"{stats['total_interactions'] / max(stats['active_users'], 1):.1f}"],
        ]
        int_table = Table(int_data, colWidths=[doc.width * 0.6, doc.width * 0.4])
        int_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), _GREEN),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTSIZE", (0, 0), (-1, 0), 9),
            ("FONTSIZE", (0, 1), (-1, -1), 10),
            ("ALIGN", (1, 0), (1, -1), "CENTER"),
            ("BACKGROUND", (0, 1), (-1, 1), _GREEN_LIGHT),
            ("BACKGROUND", (0, 3), (-1, 3), _GREEN_LIGHT),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#E0E0E0")),
            ("TOPPADDING", (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ]))
        elements.append(int_table)

        # ── Footer ───────────────────────────────────────────────
        elements.append(Spacer(1, 30))
        elements.append(HRFlowable(width="100%", thickness=0.5, color=_MUTED, spaceAfter=6))
        elements.append(Paragraph(
            f"Laporan ini di-generate otomatis oleh EcoBot v{get_settings().app.version} "
            f"pada {stats['date']} {stats['time']}.",
            s_footer,
        ))

        doc.build(elements)
        return buf.getvalue()

    # ------------------------------------------------------------------
    # Email HTML
    # ------------------------------------------------------------------
    def _build_email_html(self, stats: Dict[str, Any]) -> str:
        """Build a professional HTML email body with inline stats summary."""
        village = stats["village"]
        return f"""\
<!DOCTYPE html>
<html>
<head><meta charset="utf-8"></head>
<body style="margin:0;padding:0;background:#f4f4f4;font-family:Segoe UI,Roboto,Helvetica,Arial,sans-serif;">
  <table width="100%" cellpadding="0" cellspacing="0" style="background:#f4f4f4;padding:24px 0;">
    <tr><td align="center">
      <table width="600" cellpadding="0" cellspacing="0" style="background:#ffffff;border-radius:8px;overflow:hidden;box-shadow:0 2px 8px rgba(0,0,0,0.08);">
        <!-- Header -->
        <tr>
          <td style="background:#1B5E20;padding:28px 32px;text-align:center;">
            <h1 style="margin:0;color:#ffffff;font-size:22px;font-weight:600;">Laporan {village}</h1>
            <p style="margin:8px 0 0;color:#A5D6A7;font-size:13px;">{stats['date']} &bull; {stats['time']}</p>
          </td>
        </tr>
        <!-- Summary Cards -->
        <tr>
          <td style="padding:24px 32px 0;">
            <table width="100%" cellpadding="0" cellspacing="0">
              <tr>
                {self._email_card("Total Pengguna", stats["total_users"])}
                {self._email_card("Aktif (7h)", stats["active_users"])}
                {self._email_card("Interaksi", stats["total_interactions"])}
                {self._email_card("Foto", stats["images_processed"])}
              </tr>
            </table>
          </td>
        </tr>
        <!-- Waste Stats -->
        <tr>
          <td style="padding:24px 32px 0;">
            <h2 style="margin:0 0 12px;font-size:15px;color:#1B5E20;">Klasifikasi Sampah (7 Hari)</h2>
            <table width="100%" cellpadding="0" cellspacing="0" style="border:1px solid #E0E0E0;border-radius:6px;overflow:hidden;">
              <tr style="background:#1B5E20;color:#fff;">
                <td style="padding:8px 12px;font-size:12px;">Jenis</td>
                <td style="padding:8px 12px;font-size:12px;text-align:center;">Jumlah</td>
                <td style="padding:8px 12px;font-size:12px;text-align:center;">%</td>
              </tr>
              {self._email_waste_row("Organik", stats["waste_organic"], stats["waste_total"], "#E8F5E9")}
              {self._email_waste_row("Anorganik", stats["waste_inorganic"], stats["waste_total"], "#ffffff")}
              {self._email_waste_row("B3", stats["waste_b3"], stats["waste_total"], "#E8F5E9")}
              <tr style="background:#F5F5F5;">
                <td style="padding:8px 12px;font-weight:600;">Total</td>
                <td style="padding:8px 12px;text-align:center;font-weight:600;">{stats["waste_total"]}</td>
                <td style="padding:8px 12px;text-align:center;font-weight:600;">100%</td>
              </tr>
            </table>
          </td>
        </tr>
        <!-- CTA -->
        <tr>
          <td style="padding:24px 32px;">
            <p style="margin:0;font-size:13px;color:#757575;">Laporan lengkap tersedia dalam file PDF terlampir.</p>
          </td>
        </tr>
        <!-- Footer -->
        <tr>
          <td style="background:#F5F5F5;padding:16px 32px;text-align:center;border-top:1px solid #E0E0E0;">
            <p style="margin:0;font-size:11px;color:#9E9E9E;">
              EcoBot v{get_settings().app.version} &bull; Laporan otomatis &bull; Jangan membalas email ini
            </p>
          </td>
        </tr>
      </table>
    </td></tr>
  </table>
</body>
</html>"""

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    @staticmethod
    def _pct(value: int, total: int) -> str:
        if total == 0:
            return "0%"
        return f"{value / total * 100:.0f}%"

    @staticmethod
    def _email_card(label: str, value: int) -> str:
        return (
            f'<td width="25%" style="text-align:center;padding:12px 4px;">'
            f'<div style="background:#E8F5E9;border-radius:8px;padding:14px 8px;">'
            f'<div style="font-size:22px;font-weight:700;color:#1B5E20;">{value}</div>'
            f'<div style="font-size:11px;color:#757575;margin-top:4px;">{label}</div>'
            f'</div></td>'
        )

    @staticmethod
    def _email_waste_row(label: str, count: int, total: int, bg: str) -> str:
        pct = f"{count / total * 100:.0f}%" if total > 0 else "0%"
        return (
            f'<tr style="background:{bg};">'
            f'<td style="padding:8px 12px;font-size:13px;">{label}</td>'
            f'<td style="padding:8px 12px;font-size:13px;text-align:center;">{count}</td>'
            f'<td style="padding:8px 12px;font-size:13px;text-align:center;">{pct}</td>'
            f'</tr>'
        )
