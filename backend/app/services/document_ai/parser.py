import io
import csv
import json
import logging
import re
from typing import Dict, Any, List, Optional, Tuple
from uuid import UUID
from app.services.llm.service import LLMService, _extract_json, LLMProcessingError

logger = logging.getLogger(__name__)

# Common loan tape column mappings
COLUMN_ALIASES = {
    "loan_id": ["loan_id", "loan id", "loan #", "loan number", "loan_number", "id", "deal_id"],
    "borrower_id": ["borrower_id", "borrower id", "borrower", "borrower_name", "obligor", "counterparty"],
    "principal": ["principal", "original_balance", "original balance", "commitment", "facility_amount", "loan_amount", "amount"],
    "outstanding_balance": ["outstanding_balance", "outstanding balance", "current_balance", "current balance", "balance", "par_amount"],
    "interest_rate": ["interest_rate", "interest rate", "rate", "coupon", "spread", "margin", "all_in_rate"],
    "collateral_value": ["collateral_value", "collateral value", "collateral", "appraised_value", "property_value", "asset_value"],
    "collateral_type": ["collateral_type", "collateral type", "property_type", "asset_type", "security_type"],
    "term_months": ["term_months", "term", "maturity_months", "tenor", "remaining_term"],
    "payment_status": ["payment_status", "payment status", "status", "performance_status", "loan_status", "delinquency_status"],
    "dscr": ["dscr", "debt_service_coverage", "coverage_ratio", "debt service coverage ratio"],
    "ltv_ratio": ["ltv_ratio", "ltv", "loan_to_value", "loan to value"],
}


class DocumentAIService:
    """Parse unstructured financial documents (PDF, Excel) into structured loan data using LLM."""

    def __init__(self, llm_service: LLMService):
        self.llm_service = llm_service

    async def parse_document(
        self, org_id: UUID, file_content: bytes, filename: str, content_type: str
    ) -> Dict[str, Any]:
        """Parse a document and extract structured loan data."""
        ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""

        if ext == "pdf":
            raw_text = self._extract_pdf_text(file_content)
            loans = await self._extract_loans_with_llm(org_id, raw_text, filename)
        elif ext in ("xlsx", "xls"):
            raw_data = self._extract_excel_data(file_content)
            loans = self._map_excel_columns(raw_data)
            # Use LLM to validate and enrich if needed
            if loans and not self._has_required_fields(loans[0]):
                loans = await self._enrich_with_llm(org_id, raw_data, loans)
        elif ext == "csv":
            raw_data = self._extract_csv_data(file_content)
            loans = self._map_excel_columns(raw_data)  # Same column mapping logic
        else:
            raise ValueError(f"Unsupported file format: {ext}")

        # Validate and clean
        validated_loans = self._validate_loans(loans)

        return {
            "loans": validated_loans,
            "source_file": filename,
            "extraction_method": "llm" if ext == "pdf" else "structured",
            "raw_column_count": len(raw_data[0]) if ext != "pdf" and raw_data else 0,
            "total_extracted": len(validated_loans),
            "parsing_warnings": self._get_warnings(loans, validated_loans),
        }

    def _extract_pdf_text(self, content: bytes) -> str:
        """Extract text from PDF using pdfplumber."""
        try:
            import pdfplumber
            text_parts = []
            with pdfplumber.open(io.BytesIO(content)) as pdf:
                for i, page in enumerate(pdf.pages):
                    # Extract tables first (more structured)
                    tables = page.extract_tables()
                    if tables:
                        for table in tables:
                            for row in table:
                                if row:
                                    text_parts.append("\t".join(str(cell or "") for cell in row))
                    else:
                        # Fall back to text extraction
                        page_text = page.extract_text()
                        if page_text:
                            text_parts.append(page_text)
                    if i >= 49:  # Limit to 50 pages
                        text_parts.append(f"[... truncated, {len(pdf.pages) - 50} more pages]")
                        break
            return "\n".join(text_parts)
        except ImportError:
            # Fallback: try PyPDF2
            try:
                from PyPDF2 import PdfReader
                reader = PdfReader(io.BytesIO(content))
                text_parts = []
                for i, page in enumerate(reader.pages[:50]):
                    text = page.extract_text()
                    if text:
                        text_parts.append(text)
                return "\n".join(text_parts)
            except ImportError:
                raise LLMProcessingError(
                    "PDF parsing requires pdfplumber or PyPDF2. Install with: pip install pdfplumber"
                )

    def _extract_excel_data(self, content: bytes) -> List[Dict[str, Any]]:
        """Extract data from Excel file using openpyxl."""
        try:
            import openpyxl
            wb = openpyxl.load_workbook(io.BytesIO(content), read_only=True, data_only=True)
            ws = wb.active
            if ws is None:
                return []

            rows = list(ws.iter_rows(values_only=True))
            if len(rows) < 2:
                return []

            # First row is headers
            headers = [str(h or f"col_{i}").strip().lower() for i, h in enumerate(rows[0])]
            data = []
            for row in rows[1:]:
                record = {}
                for i, val in enumerate(row):
                    if i < len(headers):
                        record[headers[i]] = val
                data.append(record)
            wb.close()
            return data
        except ImportError:
            raise LLMProcessingError(
                "Excel parsing requires openpyxl. Install with: pip install openpyxl"
            )

    def _extract_csv_data(self, content: bytes) -> List[Dict[str, Any]]:
        """Extract data from CSV file."""
        text = content.decode("utf-8", errors="replace")
        reader = csv.DictReader(io.StringIO(text))
        return [
            {k.strip().lower(): v for k, v in row.items() if k}
            for row in reader
        ]

    def _map_excel_columns(self, raw_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Map raw column names to standardized loan fields using fuzzy matching."""
        if not raw_data:
            return []

        # Build column mapping
        raw_columns = list(raw_data[0].keys())
        mapping: Dict[str, str] = {}

        for standard_name, aliases in COLUMN_ALIASES.items():
            for col in raw_columns:
                col_lower = col.lower().strip().replace("-", "_").replace(" ", "_")
                if col_lower in aliases or col.lower().strip() in aliases:
                    mapping[col] = standard_name
                    break

        # Map data
        loans = []
        for i, row in enumerate(raw_data):
            loan: Dict[str, Any] = {"loan_id": str(i + 1)}
            for raw_col, standard_col in mapping.items():
                val = row.get(raw_col)
                if val is not None:
                    loan[standard_col] = val
            # Include unmapped columns as-is
            for col, val in row.items():
                if col not in mapping and val is not None:
                    loan[col] = val
            loans.append(loan)

        return loans

    async def _extract_loans_with_llm(
        self, org_id: UUID, text: str, filename: str
    ) -> List[Dict[str, Any]]:
        """Use LLM to extract structured loan data from unstructured text."""
        provider, model = await self.llm_service.get_provider_for_org(org_id)

        # Truncate text to avoid token limits
        max_chars = 30000
        truncated = text[:max_chars]
        if len(text) > max_chars:
            truncated += "\n[... truncated]"

        messages = [
            {
                "role": "system",
                "content": (
                    "You are a financial data extraction specialist. Extract loan tape data from the document text. "
                    "Return a JSON object with a 'loans' array. Each loan object should have these fields where available:\n"
                    "- loan_id (string)\n"
                    "- borrower_id (string)\n"
                    "- principal (number)\n"
                    "- outstanding_balance (number)\n"
                    "- interest_rate (decimal, e.g., 0.065 for 6.5%)\n"
                    "- collateral_value (number)\n"
                    "- collateral_type (string)\n"
                    "- term_months (integer)\n"
                    "- payment_status (current|delinquent|default)\n"
                    "- dscr (number)\n"
                    "- ltv_ratio (decimal)\n\n"
                    "If a field is not found, omit it. Convert percentages to decimals (6.5% -> 0.065). "
                    "Convert currency strings to numbers ($1,234,567 -> 1234567). "
                    "Extract ALL loans visible in the document."
                ),
            },
            {
                "role": "user",
                "content": f"Extract loan data from this document ({filename}):\n\n{truncated}",
            },
        ]

        try:
            response = await provider.chat(messages, model=model, temperature=0.1, max_tokens=8000)
            result = _extract_json(response)
            return result.get("loans", [])
        except Exception as e:
            logger.error(f"LLM loan extraction failed: {e}")
            raise LLMProcessingError(f"Could not extract loan data from document: {e}")

    async def _enrich_with_llm(
        self, org_id: UUID, raw_data: List[Dict[str, Any]], partial_loans: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Use LLM to map ambiguous columns to standard fields."""
        provider, model = await self.llm_service.get_provider_for_org(org_id)

        # Show sample data for mapping
        sample = raw_data[:3] if len(raw_data) >= 3 else raw_data
        columns = list(raw_data[0].keys()) if raw_data else []

        messages = [
            {
                "role": "system",
                "content": (
                    "You are a financial data mapping specialist. Given column names and sample data from a loan tape, "
                    "create a mapping from the source columns to standard loan fields.\n"
                    "Standard fields: loan_id, borrower_id, principal, outstanding_balance, interest_rate, "
                    "collateral_value, collateral_type, term_months, payment_status, dscr, ltv_ratio\n\n"
                    "Return JSON: {\"column_mapping\": {\"source_col\": \"standard_field\", ...}}"
                ),
            },
            {
                "role": "user",
                "content": (
                    f"Columns: {json.dumps(columns)}\n\n"
                    f"Sample data (first 3 rows):\n{json.dumps(sample, indent=2, default=str)}"
                ),
            },
        ]

        try:
            response = await provider.chat(messages, model=model, temperature=0.1, max_tokens=2000)
            result = _extract_json(response)
            mapping = result.get("column_mapping", {})

            # Re-map using LLM-determined mapping
            enriched = []
            for row in raw_data:
                loan: Dict[str, Any] = {}
                for src_col, std_col in mapping.items():
                    if src_col in row and row[src_col] is not None:
                        loan[std_col] = row[src_col]
                enriched.append(loan)
            return enriched
        except Exception as e:
            logger.warning(f"LLM column enrichment failed, using partial data: {e}")
            return partial_loans

    def _has_required_fields(self, loan: Dict[str, Any]) -> bool:
        """Check if a loan has minimum required fields."""
        required = {"principal", "outstanding_balance", "interest_rate"}
        present = set(loan.keys())
        return len(required & present) >= 2

    def _validate_loans(self, loans: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Validate and clean extracted loan data."""
        validated = []
        for i, loan in enumerate(loans):
            cleaned: Dict[str, Any] = {
                "loan_id": str(loan.get("loan_id", f"LOAN-{i+1:04d}")),
                "borrower_id": str(loan.get("borrower_id", "")),
                "principal": self._to_float(loan.get("principal", 0)),
                "outstanding_balance": self._to_float(loan.get("outstanding_balance", loan.get("principal", 0))),
                "interest_rate": self._to_rate(loan.get("interest_rate", 0)),
                "collateral_value": self._to_float(loan.get("collateral_value", 0)),
                "collateral_type": str(loan.get("collateral_type", "unknown")),
                "term_months": int(self._to_float(loan.get("term_months", 12))),
                "payment_status": self._normalize_status(loan.get("payment_status", "current")),
                "dscr": self._to_float(loan.get("dscr", 1.5)),
            }

            # Calculate LTV if not provided
            if loan.get("ltv_ratio"):
                cleaned["ltv_ratio"] = self._to_float(loan["ltv_ratio"])
            elif cleaned["collateral_value"] > 0:
                cleaned["ltv_ratio"] = cleaned["outstanding_balance"] / cleaned["collateral_value"]

            # Skip invalid rows (zero everything)
            if cleaned["principal"] > 0 or cleaned["outstanding_balance"] > 0:
                validated.append(cleaned)

        return validated

    @staticmethod
    def _to_float(val: Any) -> float:
        """Convert various formats to float."""
        if isinstance(val, (int, float)):
            return float(val)
        if isinstance(val, str):
            # Remove currency symbols, commas, spaces
            cleaned = re.sub(r"[,$\s%()]", "", val.strip())
            if cleaned.startswith("(") or cleaned.endswith(")"):
                cleaned = cleaned.replace("(", "").replace(")", "")
                try:
                    return -float(cleaned)
                except ValueError:
                    return 0.0
            try:
                return float(cleaned)
            except ValueError:
                return 0.0
        return 0.0

    @staticmethod
    def _to_rate(val: Any) -> float:
        """Convert interest rate to decimal form."""
        f = DocumentAIService._to_float(val)
        # If > 1, assume it's a percentage (e.g., 6.5 -> 0.065)
        if f > 1:
            return f / 100
        return f

    @staticmethod
    def _normalize_status(status: Any) -> str:
        """Normalize payment status to standard values."""
        if not status:
            return "current"
        s = str(status).lower().strip()
        if s in ("current", "performing", "active", "good", "normal"):
            return "current"
        if s in ("delinquent", "late", "past due", "past_due", "30+", "60+", "90+", "sub-performing"):
            return "delinquent"
        if s in ("default", "defaulted", "non-performing", "npl", "charge-off", "charged off"):
            return "default"
        return "current"

    def _get_warnings(self, raw_loans: List, validated_loans: List) -> List[str]:
        """Generate parsing warnings."""
        warnings = []
        dropped = len(raw_loans) - len(validated_loans)
        if dropped > 0:
            warnings.append(f"{dropped} rows dropped during validation (zero principal/balance)")
        if validated_loans:
            zero_collateral = sum(1 for l in validated_loans if l.get("collateral_value", 0) == 0)
            if zero_collateral > 0:
                warnings.append(f"{zero_collateral} loans have zero collateral value")
        return warnings
