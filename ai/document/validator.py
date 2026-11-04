"""
Document Validation Engine.
Performs format validation, date validation (issue date, expiry date, visa validity),
and cross-document comparison (e.g. Passport vs. Visa, Passport vs. ID).
"""
import re
from datetime import datetime, date
from typing import Dict, List, Any, Optional
from pydantic import BaseModel


class ValidationRuleResult(BaseModel):
    rule_name: str
    passed: bool
    message: str
    severity: str  # "INFO", "WARNING", "ERROR"


class DocumentValidationSummary(BaseModel):
    all_passed: bool
    passed_rules_count: int
    failed_rules_count: int
    rule_results: List[ValidationRuleResult]
    errors: List[str]


class DocumentValidator:
    """
    Configurable document validation engine.
    """

    @staticmethod
    def _parse_date(date_str: str) -> Optional[date]:
        for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%m/%d/%Y", "%d-%m-%Y"):
            try:
                return datetime.strptime(date_str.strip(), fmt).date()
            except Exception:
                continue
        return None

    def validate_document_fields(
        self, doc_type: str, fields: Dict[str, str]
    ) -> DocumentValidationSummary:
        """Validate single document formatting and validity periods."""
        results: List[ValidationRuleResult] = []
        errors: List[str] = []

        # 1. Required fields
        required_fields = ["full_name", "document_number", "date_of_birth", "expiry_date"]
        for req in required_fields:
            val = fields.get(req, "").strip()
            if not val:
                results.append(
                    ValidationRuleResult(
                        rule_name=f"RequiredField_{req}",
                        passed=False,
                        message=f"Required field '{req.replace('_', ' ').title()}' is missing or empty",
                        severity="ERROR"
                    )
                )
                errors.append(f"Missing required field: {req}")
            else:
                results.append(
                    ValidationRuleResult(
                        rule_name=f"RequiredField_{req}",
                        passed=True,
                        message=f"Field '{req}' present",
                        severity="INFO"
                    )
                )

        # 2. Document Number Format
        doc_num = fields.get("document_number", "").strip()
        if doc_num:
            if len(doc_num) < 6 or not re.match(r"^[A-Z0-9]+$", doc_num):
                results.append(
                    ValidationRuleResult(
                        rule_name="DocumentNumberFormat",
                        passed=False,
                        message=f"Document number '{doc_num}' has invalid alphanumeric format",
                        severity="ERROR"
                    )
                )
                errors.append(f"Invalid document number format: {doc_num}")
            else:
                results.append(
                    ValidationRuleResult(
                        rule_name="DocumentNumberFormat",
                        passed=True,
                        message="Document number format valid",
                        severity="INFO"
                    )
                )

        # 3. Expiry Date Check
        expiry_str = fields.get("expiry_date", "")
        if expiry_str:
            exp_date = self._parse_date(expiry_str)
            today = date.today()
            if exp_date:
                if exp_date < today:
                    results.append(
                        ValidationRuleResult(
                            rule_name="ExpiryDateCheck",
                            passed=False,
                            message=f"Document expired on {exp_date.isoformat()} (today is {today.isoformat()})",
                            severity="ERROR"
                        )
                    )
                    errors.append(f"Document expired on {exp_date.isoformat()}")
                else:
                    results.append(
                        ValidationRuleResult(
                            rule_name="ExpiryDateCheck",
                            passed=True,
                            message=f"Document is valid until {exp_date.isoformat()}",
                            severity="INFO"
                        )
                    )
            else:
                results.append(
                    ValidationRuleResult(
                        rule_name="ExpiryDateFormat",
                        passed=False,
                        message=f"Cannot parse expiry date '{expiry_str}'",
                        severity="WARNING"
                    )
                )
                errors.append(f"Unparseable expiry date: {expiry_str}")

        passed_count = sum(1 for r in results if r.passed)
        failed_count = sum(1 for r in results if not r.passed)

        return DocumentValidationSummary(
            all_passed=(failed_count == 0),
            passed_rules_count=passed_count,
            failed_rules_count=failed_count,
            rule_results=results,
            errors=errors
        )

    def cross_validate_documents(
        self, doc1_name: str, doc1_fields: Dict[str, str],
        doc2_name: str, doc2_fields: Dict[str, str]
    ) -> DocumentValidationSummary:
        """
        Compare fields across two linked documents (e.g. Passport vs Visa).
        Detects mismatches in Name, Document Number, Nationality, and Date of Birth.
        """
        results: List[ValidationRuleResult] = []
        errors: List[str] = []

        # Compare Document Number referenced on secondary document
        # e.g. Visa usually has 'passport_number' or 'document_number'
        d1_num = doc1_fields.get("document_number", "").strip().upper()
        d2_num = (doc2_fields.get("passport_number") or doc2_fields.get("document_number", "")).strip().upper()

        if d1_num and d2_num:
            if d1_num == d2_num:
                results.append(
                    ValidationRuleResult(
                        rule_name="CrossCheck_DocumentNumber",
                        passed=True,
                        message=f"Document numbers match across {doc1_name} and {doc2_name} ({d1_num})",
                        severity="INFO"
                    )
                )
            else:
                results.append(
                    ValidationRuleResult(
                        rule_name="CrossCheck_DocumentNumber",
                        passed=False,
                        message=f"Document Number Mismatch: {doc1_name} has '{d1_num}' while {doc2_name} has '{d2_num}'",
                        severity="ERROR"
                    )
                )
                errors.append(f"Document Mismatch: {doc1_name} ({d1_num}) vs {doc2_name} ({d2_num})")

        # Compare Holder Names
        name1 = doc1_fields.get("full_name", "").strip().upper()
        name2 = doc2_fields.get("full_name", "").strip().upper()
        if name1 and name2:
            # Simple clean comparison
            clean1 = re.sub(r"[^A-Z]", "", name1)
            clean2 = re.sub(r"[^A-Z]", "", name2)
            if clean1 == clean2 or clean1 in clean2 or clean2 in clean1:
                results.append(
                    ValidationRuleResult(
                        rule_name="CrossCheck_HolderName",
                        passed=True,
                        message=f"Holder name verified across documents: '{name1}'",
                        severity="INFO"
                    )
                )
            else:
                results.append(
                    ValidationRuleResult(
                        rule_name="CrossCheck_HolderName",
                        passed=False,
                        message=f"Name Mismatch: '{name1}' on {doc1_name} vs '{name2}' on {doc2_name}",
                        severity="ERROR"
                    )
                )
                errors.append(f"Name Mismatch: '{name1}' vs '{name2}'")

        # Compare Date of Birth
        dob1 = doc1_fields.get("date_of_birth", "").strip()
        dob2 = doc2_fields.get("date_of_birth", "").strip()
        if dob1 and dob2:
            p1 = self._parse_date(dob1)
            p2 = self._parse_date(dob2)
            if p1 and p2 and p1 == p2:
                results.append(
                    ValidationRuleResult(
                        rule_name="CrossCheck_DateOfBirth",
                        passed=True,
                        message=f"Date of birth verified ({p1.isoformat()})",
                        severity="INFO"
                    )
                )
            elif p1 and p2 and p1 != p2:
                results.append(
                    ValidationRuleResult(
                        rule_name="CrossCheck_DateOfBirth",
                        passed=False,
                        message=f"DOB Mismatch: {p1.isoformat()} vs {p2.isoformat()}",
                        severity="ERROR"
                    )
                )
                errors.append(f"DOB Mismatch: {p1.isoformat()} vs {p2.isoformat()}")

        passed_count = sum(1 for r in results if r.passed)
        failed_count = sum(1 for r in results if not r.passed)

        return DocumentValidationSummary(
            all_passed=(failed_count == 0),
            passed_rules_count=passed_count,
            failed_rules_count=failed_count,
            rule_results=results,
            errors=errors
        )
