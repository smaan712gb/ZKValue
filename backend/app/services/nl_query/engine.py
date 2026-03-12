import json
import logging
import re
from typing import Dict, Any, List, Optional
from uuid import UUID
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from app.services.llm.service import LLMService, _extract_json, LLMProcessingError

logger = logging.getLogger(__name__)

# Database schema context for the LLM
SCHEMA_CONTEXT = """
Available tables (all data is scoped by organization_id for multi-tenancy):

1. verifications:
   - id (UUID), organization_id (UUID), created_by (UUID)
   - module (enum: 'private_credit', 'ai_ip_valuation')
   - status (enum: 'pending', 'processing', 'completed', 'failed')
   - input_data (JSON), result_data (JSON)
   - proof_hash (varchar), metadata (JSON)
   - created_at (timestamp), completed_at (timestamp)

2. credit_portfolios:
   - id (UUID), organization_id (UUID), verification_id (UUID)
   - portfolio_name (varchar), fund_name (varchar)
   - loan_count (int), total_principal (numeric)
   - weighted_avg_rate (numeric), avg_ltv_ratio (numeric)
   - nav_value (numeric), covenant_compliance_status (JSON)
   - created_at (timestamp)

3. ai_assets:
   - id (UUID), organization_id (UUID), verification_id (UUID)
   - asset_type (enum: 'training_data', 'model_weights', 'inference_infra', 'deployed_app')
   - asset_name (varchar), description (text)
   - valuation_method (enum: 'cost_approach', 'market_approach', 'income_approach')
   - estimated_value (numeric), confidence_score (numeric)
   - ias38_compliant (bool), asc350_compliant (bool)
   - created_at (timestamp)

4. drift_alerts:
   - id (UUID), organization_id (UUID)
   - severity (enum: 'info', 'warning', 'critical')
   - status (enum: 'active', 'acknowledged', 'resolved')
   - alert_type (varchar), message (varchar)
   - drift_pct (numeric), created_at (timestamp)

5. notifications:
   - id (UUID), organization_id (UUID), user_id (UUID)
   - notification_type (enum), title (varchar), message (text)
   - is_read (bool), created_at (timestamp)
"""

# Allowed tables for querying (whitelist)
ALLOWED_TABLES = {
    "verifications", "credit_portfolios", "ai_assets",
    "drift_alerts", "notifications", "verification_schedules",
}

# Blocked SQL patterns (prevent writes, schema changes, etc.)
BLOCKED_PATTERNS = [
    r"\b(INSERT|UPDATE|DELETE|DROP|ALTER|CREATE|TRUNCATE|GRANT|REVOKE)\b",
    r"\b(INTO|SET)\b",
    r"--",  # SQL comments
    r";.*\S",  # Multiple statements
    r"\bpg_\w+",  # PostgreSQL system tables
    r"\binformation_schema\b",
    r"\busers\b",  # Don't allow querying user table
    r"\borganizations\b",  # Don't allow querying org table directly
]


class NLQueryEngine:
    """Natural language to SQL query engine with safety guardrails."""

    def __init__(self, session: AsyncSession, llm_service: LLMService):
        self.session = session
        self.llm_service = llm_service

    async def query(
        self, org_id: UUID, question: str, max_rows: int = 50
    ) -> Dict[str, Any]:
        """Process a natural language question and return results."""
        # Step 1: Generate SQL from natural language
        sql, explanation = await self._generate_sql(org_id, question)

        # Step 2: Validate SQL for safety
        validation = self._validate_sql(sql)
        if not validation["safe"]:
            return {
                "question": question,
                "error": validation["reason"],
                "sql_generated": sql,
                "results": [],
            }

        # Step 3: Inject organization_id filter for multi-tenancy
        safe_sql = self._inject_tenant_filter(sql, org_id)

        # Step 4: Execute query
        try:
            result = await self.session.execute(
                text(safe_sql).bindparams(org_id=str(org_id)),
            )
            rows = result.fetchmany(max_rows)
            columns = list(result.keys()) if result.returns_rows else []

            # Convert to dicts
            data = [dict(zip(columns, row)) for row in rows]

            # Serialize non-JSON-safe types
            serialized = []
            for row in data:
                clean_row = {}
                for k, v in row.items():
                    if hasattr(v, 'isoformat'):
                        clean_row[k] = v.isoformat()
                    elif isinstance(v, (int, float, str, bool, type(None))):
                        clean_row[k] = v
                    else:
                        clean_row[k] = str(v)
                serialized.append(clean_row)

        except Exception as e:
            logger.error(f"NL query execution failed: {e}")
            return {
                "question": question,
                "sql_generated": safe_sql,
                "explanation": explanation,
                "error": f"Query execution failed: {str(e)[:200]}",
                "results": [],
            }

        # Step 5: Generate natural language answer
        answer = await self._generate_answer(org_id, question, serialized, explanation)

        return {
            "question": question,
            "sql_generated": safe_sql,
            "explanation": explanation,
            "answer": answer,
            "results": serialized,
            "row_count": len(serialized),
        }

    async def _generate_sql(self, org_id: UUID, question: str) -> tuple[str, str]:
        """Use LLM to convert natural language to SQL."""
        provider, model = await self.llm_service.get_provider_for_org(org_id)

        messages = [
            {
                "role": "system",
                "content": (
                    "You are a SQL expert working with a PostgreSQL database. Convert natural language questions "
                    "into safe, read-only SQL queries. IMPORTANT RULES:\n"
                    "1. ONLY generate SELECT statements — never INSERT, UPDATE, DELETE, DROP, etc.\n"
                    "2. Always include a WHERE clause with organization_id = :org_id for tenant isolation\n"
                    "3. Always add is_deleted = false to filter soft-deleted records\n"
                    "4. Limit results to 50 rows unless user specifies otherwise\n"
                    "5. Use proper aggregation functions (AVG, SUM, COUNT, etc.)\n"
                    "6. Return JSON with keys: 'sql' (the query) and 'explanation' (what the query does)\n\n"
                    f"DATABASE SCHEMA:\n{SCHEMA_CONTEXT}"
                ),
            },
            {
                "role": "user",
                "content": f"Convert this question to SQL: {question}",
            },
        ]

        try:
            response = await provider.chat(messages, model=model, temperature=0.1, max_tokens=1500)
            result = _extract_json(response)
            sql = result.get("sql", "")
            explanation = result.get("explanation", "")
            return sql, explanation
        except Exception as e:
            logger.error(f"SQL generation failed: {e}")
            raise LLMProcessingError(f"Could not generate SQL query: {e}")

    def _validate_sql(self, sql: str) -> Dict[str, Any]:
        """Validate SQL for safety — only allow read-only queries."""
        if not sql or not sql.strip():
            return {"safe": False, "reason": "Empty SQL query"}

        sql_upper = sql.upper().strip()

        # Must start with SELECT or WITH (CTE)
        if not sql_upper.startswith("SELECT") and not sql_upper.startswith("WITH"):
            return {"safe": False, "reason": "Only SELECT queries are allowed"}

        # Check blocked patterns
        for pattern in BLOCKED_PATTERNS:
            if re.search(pattern, sql_upper):
                return {"safe": False, "reason": f"Blocked SQL pattern detected: {pattern}"}

        # Verify only allowed tables are referenced
        # Simple check — extract table names after FROM and JOIN
        table_refs = re.findall(r"\bFROM\s+(\w+)|\bJOIN\s+(\w+)", sql_upper)
        for groups in table_refs:
            for table in groups:
                if table and table.lower() not in ALLOWED_TABLES:
                    return {"safe": False, "reason": f"Table '{table}' is not allowed for querying"}

        return {"safe": True, "reason": ""}

    def _inject_tenant_filter(self, sql: str, org_id: UUID) -> str:
        """Ensure organization_id filter is present in the query."""
        # If the query already has :org_id binding, it's fine
        if ":org_id" in sql:
            return sql

        # Try to add org_id filter to WHERE clause
        # This is a safety net — the LLM should already include it
        sql_upper = sql.upper()
        if "WHERE" in sql_upper:
            # Add to existing WHERE
            where_idx = sql_upper.index("WHERE") + 5
            sql = sql[:where_idx] + " organization_id = :org_id AND" + sql[where_idx:]
        elif "GROUP BY" in sql_upper:
            group_idx = sql_upper.index("GROUP BY")
            sql = sql[:group_idx] + " WHERE organization_id = :org_id " + sql[group_idx:]
        elif "ORDER BY" in sql_upper:
            order_idx = sql_upper.index("ORDER BY")
            sql = sql[:order_idx] + " WHERE organization_id = :org_id " + sql[order_idx:]
        elif "LIMIT" in sql_upper:
            limit_idx = sql_upper.index("LIMIT")
            sql = sql[:limit_idx] + " WHERE organization_id = :org_id " + sql[limit_idx:]
        else:
            sql = sql.rstrip().rstrip(";") + " WHERE organization_id = :org_id"

        return sql

    async def _generate_answer(
        self, org_id: UUID, question: str, results: List[Dict], explanation: str
    ) -> str:
        """Generate a natural language answer from the query results."""
        if not results:
            return "No data found matching your question."

        provider, model = await self.llm_service.get_provider_for_org(org_id)

        # Truncate results for LLM context
        display_results = results[:10]

        messages = [
            {
                "role": "system",
                "content": (
                    "You are a financial data analyst. Given a question, the SQL query explanation, and "
                    "the query results, provide a clear, concise natural language answer. "
                    "Include specific numbers from the results. Keep it under 200 words. "
                    "Format currency values with $ and commas. Format percentages with %."
                ),
            },
            {
                "role": "user",
                "content": (
                    f"Question: {question}\n\n"
                    f"Query explanation: {explanation}\n\n"
                    f"Results ({len(results)} rows):\n{json.dumps(display_results, indent=2, default=str)}"
                ),
            },
        ]

        try:
            return await provider.chat(messages, model=model, temperature=0.3, max_tokens=500)
        except Exception:
            # Fallback to simple answer
            return f"Query returned {len(results)} results. See the data below."

    async def get_suggested_questions(self) -> List[str]:
        """Return suggested questions users can ask."""
        return [
            "What is my total portfolio NAV across all funds?",
            "Show me all verifications that failed this month",
            "What is the average LTV ratio across all credit portfolios?",
            "How many AI assets have been valued above $1 million?",
            "Which portfolios have covenant breaches?",
            "Show me the total principal by fund name",
            "What is my verification pass rate?",
            "List all critical drift alerts from the last 30 days",
            "What is the average confidence score for AI-IP valuations?",
            "How many verifications were completed each month?",
        ]
