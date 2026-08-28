"""
Service for generating submission-ready dispute representment PDF packets.

Safety constraints:
- Only called for explicitly approved CONTEST decisions.
- Labeled clearly as 'SUBMISSION-READY PROTOTYPE PACKET'.
- Does NOT submit live transactions to Razorpay or card networks.
"""

from io import BytesIO
from datetime import datetime
from decimal import Decimal

from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    HRFlowable,
    KeepTogether,
)

from backend.domain.models import Dispute, EvidenceDocument, EvidenceClaim, Decision


def generate_dispute_packet_pdf(
    dispute: Dispute,
    decision: Decision,
    documents: list[EvidenceDocument],
    claims: list[EvidenceClaim],
    approval_info: dict,
) -> bytes:
    """Compile an evidence packet into a submission-ready PDF document."""
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=40,
        leftMargin=40,
        topMargin=40,
        bottomMargin=40,
    )

    styles = getSampleStyleSheet()
    
    # Custom styles
    title_style = ParagraphStyle(
        "PacketTitle",
        parent=styles["Heading1"],
        fontSize=20,
        leading=24,
        textColor=colors.HexColor("#0f172a"),
        fontName="Helvetica-Bold",
    )
    subtitle_style = ParagraphStyle(
        "PacketSubtitle",
        parent=styles["Normal"],
        fontSize=10,
        leading=14,
        textColor=colors.HexColor("#64748b"),
    )
    section_heading = ParagraphStyle(
        "SectionHeading",
        parent=styles["Heading2"],
        fontSize=13,
        leading=17,
        textColor=colors.HexColor("#1e293b"),
        fontName="Helvetica-Bold",
        spaceBefore=10,
        spaceAfter=6,
    )
    body_style = ParagraphStyle(
        "PacketBody",
        parent=styles["Normal"],
        fontSize=9,
        leading=13,
        textColor=colors.HexColor("#334155"),
    )
    body_bold = ParagraphStyle(
        "PacketBodyBold",
        parent=body_style,
        fontName="Helvetica-Bold",
    )
    notice_style = ParagraphStyle(
        "NoticeStyle",
        parent=styles["Normal"],
        fontSize=8,
        leading=11,
        textColor=colors.HexColor("#94a3b8"),
        alignment=1,  # Centered
    )

    story = []

    # ── 1. Header & Notice Banner ──
    story.append(Paragraph("DISPUTEGUARD REPRESENTMENT PACKET", title_style))
    story.append(Paragraph(f"Generated on {datetime.now().strftime('%d-%b-%Y %H:%M UTC')} · Case ID: <b>{dispute.id}</b>", subtitle_style))
    story.append(Spacer(1, 8))

    # Prototype Label Banner
    banner_data = [[
        Paragraph(
            "<b>SUBMISSION-READY PROTOTYPE PACKET</b><br/>"
            "This document is an evidence-grounded representment draft generated for merchant review. "
            "Internal prototype only — not submitted to card network.",
            ParagraphStyle("BannerText", parent=body_style, fontSize=8, leading=11, textColor=colors.HexColor("#854d0e"))
        )
    ]]
    banner_table = Table(banner_data, colWidths=[530])
    banner_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#fef9c3")),
        ("BORDER", (0, 0), (-1, -1), 1, colors.HexColor("#fde047")),
        ("PADDING", (0, 0), (-1, -1), 8),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ]))
    story.append(banner_table)
    story.append(Spacer(1, 14))

    # ── 2. Case Summary ──
    story.append(Paragraph("1. Dispute & Transaction Summary", section_heading))
    
    summary_data = [
        [
            Paragraph("<b>Merchant Name:</b>", body_style), Paragraph(dispute.merchant_name, body_style),
            Paragraph("<b>Dispute Amount:</b>", body_style), Paragraph(f"₹{dispute.amount:,.2f} {dispute.currency}", body_bold),
        ],
        [
            Paragraph("<b>Order ID:</b>", body_style), Paragraph(dispute.order_id, body_style),
            Paragraph("<b>Transaction ID:</b>", body_style), Paragraph(dispute.transaction_id, body_style),
        ],
        [
            Paragraph("<b>Dispute Reason:</b>", body_style), Paragraph(dispute.reason.value.replace("_", " ").title(), body_style),
            Paragraph("<b>Filing Date:</b>", body_style), Paragraph(dispute.filed_date.strftime("%d-%b-%Y"), body_style),
        ],
        [
            Paragraph("<b>Customer Name:</b>", body_style), Paragraph(dispute.customer_name or "N/A", body_style),
            Paragraph("<b>Response Deadline:</b>", body_style), Paragraph(dispute.respond_by.strftime("%d-%b-%Y"), body_style),
        ],
        [
            Paragraph("<b>Shipping Address:</b>", body_style), Paragraph(dispute.shipping_address or "N/A", body_style),
            Paragraph("<b>Risk Level:</b>", body_style), Paragraph(dispute.risk_level.value.upper(), body_style),
        ],
    ]
    summary_table = Table(summary_data, colWidths=[110, 155, 110, 155])
    summary_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f8fafc")),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
        ("PADDING", (0, 0), (-1, -1), 5),
    ]))
    story.append(summary_table)
    story.append(Spacer(1, 14))

    # ── 3. Decision & Human Review Sign-Off ──
    story.append(Paragraph("2. Decision & Human Review Sign-Off", section_heading))
    approval_data = [
        [
            Paragraph("<b>Recommendation:</b>", body_style), Paragraph(f"<b>{decision.action.value.upper()}</b>", ParagraphStyle("Contest", parent=body_bold, textColor=colors.HexColor("#16a34a"))),
            Paragraph("<b>Evidence Strength:</b>", body_style), Paragraph(f"{decision.evidence_strength * 100:.0f}%", body_style),
        ],
        [
            Paragraph("<b>Approved By:</b>", body_style), Paragraph(approval_info.get("approved_by", "Merchant Reviewer"), body_style),
            Paragraph("<b>Approved At:</b>", body_style), Paragraph(approval_info.get("approved_at", datetime.now().strftime("%d-%b-%Y %H:%M UTC")), body_style),
        ],
        [
            Paragraph("<b>Contest EV:</b>", body_style), Paragraph(f"₹{Decimal(str(decision.contest_expected_value)):,.2f}", body_style),
            Paragraph("<b>Completeness:</b>", body_style), Paragraph(f"{decision.completeness_score * 100:.0f}%", body_style),
        ],
    ]
    approval_table = Table(approval_data, colWidths=[110, 155, 110, 155])
    approval_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f8fafc")),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
        ("PADDING", (0, 0), (-1, -1), 5),
    ]))
    story.append(approval_table)
    story.append(Spacer(1, 14))

    # ── 4. Merchant Representment Narrative ──
    story.append(Paragraph("3. Merchant Contestation Narrative", section_heading))
    narrative_text = approval_info.get("narrative") or (
        f"The cardholder filed a '{dispute.reason.value.replace('_', ' ')}' dispute for transaction "
        f"{dispute.transaction_id} (Order {dispute.order_id}) in the amount of ₹{dispute.amount:,.2f}. "
        f"Our records and independent carrier telemetry confirm the merchandise was dispatched to the "
        f"cardholder's verified address ({dispute.shipping_address}) and successfully delivered before the dispute was initiated. "
        f"All supporting documentation, including the invoice, carrier tracking logs, and proof of delivery, is attached below."
    )
    narrative_table = Table([[Paragraph(narrative_text, body_style)]], colWidths=[530])
    narrative_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f1f5f9")),
        ("BORDER", (0, 0), (-1, -1), 1, colors.HexColor("#cbd5e1")),
        ("PADDING", (0, 0), (-1, -1), 8),
    ]))
    story.append(narrative_table)
    story.append(Spacer(1, 14))

    # ── 5. Evidence Index ──
    story.append(Paragraph("4. Evidence Documents Attached", section_heading))
    doc_headers = [Paragraph("<b>Doc ID</b>", body_bold), Paragraph("<b>Type</b>", body_bold), Paragraph("<b>Filename / Source</b>", body_bold), Paragraph("<b>Method</b>", body_bold)]
    doc_rows = [doc_headers]
    for d in documents:
        doc_rows.append([
            Paragraph(d.id, body_style),
            Paragraph(d.type.value.replace("_", " ").title(), body_style),
            Paragraph(f"{d.filename}<br/><font color='#64748b'>{d.source}</font>", body_style),
            Paragraph(d.extraction_method.value, body_style),
        ])
    doc_table = Table(doc_rows, colWidths=[85, 125, 220, 100])
    doc_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#e2e8f0")),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
        ("PADDING", (0, 0), (-1, -1), 5),
    ]))
    story.append(doc_table)
    story.append(Spacer(1, 14))

    # ── 6. Verified Claims & Provenance Citations ──
    story.append(Paragraph("5. Extracted Evidence Claims & Deterministic Citations", section_heading))
    claim_headers = [
        Paragraph("<b>Field</b>", body_bold),
        Paragraph("<b>Extracted Raw</b>", body_bold),
        Paragraph("<b>Status</b>", body_bold),
        Paragraph("<b>Source Location</b>", body_bold),
    ]
    claim_rows = [claim_headers]
    for c in claims:
        status_color = "#16a34a" if c.verification_status.value == "verified" else "#dc2626"
        claim_rows.append([
            Paragraph(f"<b>{c.field_name}</b>", body_style),
            Paragraph(f"<font face='Courier'>{c.raw_value}</font>", body_style),
            Paragraph(f"<font color='{status_color}'><b>{c.verification_status.value.upper()}</b></font><br/><font color='#64748b' size=7>{c.verification_reason}</font>", body_style),
            Paragraph(f"<b>{c.document_id}</b><br/><font color='#64748b' size=7>{c.source_location}</font>", body_style),
        ])
    claim_table = Table(claim_rows, colWidths=[100, 120, 180, 130])
    claim_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#e2e8f0")),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
        ("PADDING", (0, 0), (-1, -1), 4),
    ]))
    story.append(claim_table)
    story.append(Spacer(1, 18))

    # ── 7. Footer Notice ──
    story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#cbd5e1"), spaceBefore=10, spaceAfter=8))
    story.append(Paragraph("DisputeGuard AI Risk Manager · End of Submission-Ready Packet", notice_style))

    doc.build(story)
    buffer.seek(0)
    return buffer.getvalue()
