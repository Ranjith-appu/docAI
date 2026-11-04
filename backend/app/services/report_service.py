"""
Official PDF Screening Report Generator.
Generates comprehensive forensic and decision-support PDF reports with:
- Case Information & Metadata
- Uploaded Document Summary & SHA-256 Hashes
- OCR Extracted Fields & Confidence Ratings
- Computer Vision Tampering & Compression Forensics
- Biometric Face Verification Breakdown
- Explainable Risk Score & Itemized Contributing Factors
- Blockchain Proof Anchoring (Network, Tx Hash, Contract Address)
- Officer Review & Sign-off Details
"""
import io
import json
from datetime import datetime, timezone
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable, KeepTogether
)

from backend.app.models.models import ScreeningCase


class ReportService:
    @staticmethod
    def generate_case_pdf(case: ScreeningCase) -> bytes:
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=letter,
            rightMargin=36,
            leftMargin=36,
            topMargin=36,
            bottomMargin=36
        )

        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            "TitleStyle",
            parent=styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=18,
            leading=22,
            textColor=colors.HexColor("#0f172a")
        )
        subtitle_style = ParagraphStyle(
            "SubTitleStyle",
            parent=styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=11,
            leading=14,
            textColor=colors.HexColor("#2563eb")
        )
        h2_style = ParagraphStyle(
            "H2Style",
            parent=styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=12,
            leading=16,
            textColor=colors.HexColor("#1e293b"),
            spaceBefore=10,
            spaceAfter=6
        )
        body_style = ParagraphStyle(
            "BodyStyle",
            parent=styles["Normal"],
            fontName="Helvetica",
            fontSize=9,
            leading=13,
            textColor=colors.HexColor("#334155")
        )
        badge_style = ParagraphStyle(
            "BadgeStyle",
            parent=styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=9,
            leading=12,
            textColor=colors.white
        )

        elements = []

        # Header Title
        elements.append(Paragraph("AI-BASED IDENTITY & DOCUMENT SCREENING SYSTEM", subtitle_style))
        elements.append(Paragraph(f"Official Screening Dossier: {case.case_number}", title_style))
        elements.append(Paragraph(f"Generated on {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')} | Security Operations", body_style))
        elements.append(Spacer(1, 10))
        elements.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor("#cbd5e1"), spaceAfter=12))

        # Case Summary Table
        risk_score = f"{case.risk_assessment.overall_score:.1f} / 100" if case.risk_assessment else "PENDING"
        risk_class = case.risk_assessment.classification if case.risk_assessment else "PENDING"
        summary_data = [
            [Paragraph("<b>Case Number:</b>", body_style), Paragraph(case.case_number, body_style),
             Paragraph("<b>Status:</b>", body_style), Paragraph(case.status, body_style)],
            [Paragraph("<b>Applicant:</b>", body_style), Paragraph(case.applicant_name, body_style),
             Paragraph("<b>Document Type:</b>", body_style), Paragraph(case.document_type, body_style)],
            [Paragraph("<b>Risk Score:</b>", body_style), Paragraph(f"<b>{risk_score} ({risk_class})</b>", body_style),
             Paragraph("<b>Date Created:</b>", body_style), Paragraph(case.created_at.strftime("%Y-%m-%d %H:%M"), body_style)]
        ]
        t_summary = Table(summary_data, colWidths=[100, 170, 100, 170])
        t_summary.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f8fafc")),
            ("BOX", (0, 0), (-1, -1), 1, colors.HexColor("#e2e8f0")),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ("TOPPADDING", (0, 0), (-1, -1), 5),
        ]))
        elements.append(t_summary)
        elements.append(Spacer(1, 14))

        # 1. Documents & Hashes Table
        elements.append(Paragraph("1. UPLOADED DOCUMENTS & CRYPTOGRAPHIC PROOF", h2_style))
        doc_rows = [[
            Paragraph("<b>Document Type</b>", body_style),
            Paragraph("<b>File Name</b>", body_style),
            Paragraph("<b>SHA-256 Hash</b>", body_style),
            Paragraph("<b>Size</b>", body_style)
        ]]
        for doc_item in case.documents:
            short_hash = f"{doc_item.sha256_hash[:16]}...{doc_item.sha256_hash[-12:]}"
            doc_rows.append([
                Paragraph(doc_item.document_type, body_style),
                Paragraph(doc_item.file_name, body_style),
                Paragraph(f"<font face='Courier'>{short_hash}</font>", body_style),
                Paragraph(f"{doc_item.file_size // 1024} KB", body_style)
            ])

        t_docs = Table(doc_rows, colWidths=[110, 140, 220, 70])
        t_docs.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#f1f5f9")),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ]))
        elements.append(t_docs)
        elements.append(Spacer(1, 14))

        # 2. OCR Extracted Fields Table
        elements.append(Paragraph("2. AUTOMATED OCR EXTRACTION", h2_style))
        ocr_rows = [[
            Paragraph("<b>Field Name</b>", body_style),
            Paragraph("<b>Extracted Value</b>", body_style),
            Paragraph("<b>Confidence</b>", body_style)
        ]]

        has_fields = False
        for doc_item in case.documents:
            for field in doc_item.fields:
                has_fields = True
                ocr_rows.append([
                    Paragraph(field.field_name.replace("_", " ").title(), body_style),
                    Paragraph(f"<b>{field.field_value}</b>", body_style),
                    Paragraph(f"{field.confidence:.1f}%", body_style)
                ])

        if not has_fields:
            ocr_rows.append([Paragraph("No extracted fields available", body_style), Paragraph("-", body_style), Paragraph("-", body_style)])

        t_ocr = Table(ocr_rows, colWidths=[180, 260, 100])
        t_ocr.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#f1f5f9")),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ]))
        elements.append(t_ocr)
        elements.append(Spacer(1, 14))

        # 3. AI Forensics, Tampering & Face Verification
        elements.append(Paragraph("3. AI FORENSICS & BIOMETRIC VERIFICATION", h2_style))
        forensics_rows = [[
            Paragraph("<b>Module</b>", body_style),
            Paragraph("<b>Score / Status</b>", body_style),
            Paragraph("<b>Advisory Finding / Recommendation</b>", body_style)
        ]]

        # Tampering row
        for doc_item in case.documents:
            if doc_item.tampering_result:
                tr = doc_item.tampering_result
                forensics_rows.append([
                    Paragraph(f"Tampering ({doc_item.document_type})", body_style),
                    Paragraph(f"<b>{tr.tampering_score:.1f}%</b> (Suspicion)", body_style),
                    Paragraph(f"{tr.recommendation}<br/><font color='#64748b'>{tr.explanation}</font>", body_style)
                ])

        # Face verification row
        if case.face_verification:
            fv = case.face_verification
            forensics_rows.append([
                Paragraph("Biometric Face Match", body_style),
                Paragraph(f"<b>{fv.status}</b> ({fv.similarity_score:.1f}%)", body_style),
                Paragraph(f"Confidence: {fv.confidence:.1f}%<br/><font color='#64748b'>{fv.explanation}</font>", body_style)
            ])

        t_forensics = Table(forensics_rows, colWidths=[140, 130, 270])
        t_forensics.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#f1f5f9")),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ]))
        elements.append(t_forensics)
        elements.append(Spacer(1, 14))

        # 4. Explainable Risk Factors Breakdown
        elements.append(Paragraph("4. EXPLAINABLE RISK ASSESSMENT", h2_style))
        risk_rows = [[
            Paragraph("<b>Contributing Factor</b>", body_style),
            Paragraph("<b>Points</b>", body_style),
            Paragraph("<b>Description</b>", body_style)
        ]]

        if case.risk_assessment and case.risk_assessment.factors_json:
            try:
                factors_list = json.loads(case.risk_assessment.factors_json)
                for f in factors_list:
                    risk_rows.append([
                        Paragraph(f.get("factor_name", "Risk Indicator"), body_style),
                        Paragraph(f"+{f.get('contribution', 0):.0f}", body_style),
                        Paragraph(f.get("description", ""), body_style)
                    ])
            except Exception:
                pass

        if len(risk_rows) == 1:
            risk_rows.append([Paragraph("No elevated risk indicators detected", body_style), Paragraph("0", body_style), Paragraph("All standard checks passed", body_style)])

        t_risk = Table(risk_rows, colWidths=[180, 70, 290])
        t_risk.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#f1f5f9")),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ]))
        elements.append(t_risk)
        elements.append(Spacer(1, 14))

        # 5. Blockchain Integrity Record
        elements.append(Paragraph("5. BLOCKCHAIN PROOF & REGISTRY RECORD", h2_style))
        if case.blockchain_record:
            b_rec = case.blockchain_record
            bc_data = [
                [Paragraph("<b>Network:</b>", body_style), Paragraph(b_rec.network, body_style)],
                [Paragraph("<b>Contract Address:</b>", body_style), Paragraph(f"<font face='Courier'>{b_rec.contract_address}</font>", body_style)],
                [Paragraph("<b>Transaction Hash:</b>", body_style), Paragraph(f"<font face='Courier'>{b_rec.tx_hash}</font>", body_style)],
                [Paragraph("<b>Case Hash:</b>", body_style), Paragraph(f"<font face='Courier'>{b_rec.case_hash}</font>", body_style)],
                [Paragraph("<b>Document Hash:</b>", body_style), Paragraph(f"<font face='Courier'>{b_rec.document_hash}</font>", body_style)],
                [Paragraph("<b>Status:</b>", body_style), Paragraph(f"<b>CONFIRMED ON-CHAIN ({b_rec.status})</b>", body_style)]
            ]
            t_bc = Table(bc_data, colWidths=[140, 400])
            t_bc.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f8fafc")),
                ("BOX", (0, 0), (-1, -1), 1, colors.HexColor("#e2e8f0")),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ]))
            elements.append(t_bc)
        else:
            elements.append(Paragraph("Document hash has not yet been registered on the blockchain ledger.", body_style))

        elements.append(Spacer(1, 14))

        # 6. Officer Decision & Sign-off
        elements.append(Paragraph("6. AUTHORIZED OFFICER REVIEW & SIGN-OFF", h2_style))
        decision_val = case.officer_review.decision if case.officer_review else "PENDING REVIEW"
        notes_val = case.officer_review.notes if (case.officer_review and case.officer_review.notes) else "No officer notes recorded."
        officer_name = case.officer.full_name if case.officer else "Authorized Officer"

        review_data = [
            [Paragraph("<b>Reviewer:</b>", body_style), Paragraph(officer_name, body_style)],
            [Paragraph("<b>Official Decision:</b>", body_style), Paragraph(f"<b>{decision_val}</b>", body_style)],
            [Paragraph("<b>Officer Notes:</b>", body_style), Paragraph(notes_val, body_style)],
            [Paragraph("<b>Notice:</b>", body_style), Paragraph("<font color='#64748b'>AI results are strictly decision-support advisory indicators. Enforcement actions require human officer determination.</font>", body_style)]
        ]
        t_rev = Table(review_data, colWidths=[140, 400])
        t_rev.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f8fafc")),
            ("BOX", (0, 0), (-1, -1), 1, colors.HexColor("#e2e8f0")),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ]))
        elements.append(t_rev)

        doc.build(elements)
        buffer.seek(0)
        return buffer.getvalue()
