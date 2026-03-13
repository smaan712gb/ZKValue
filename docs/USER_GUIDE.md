# ZKValue User Guide

**Version 1.0** | Last updated: March 2026

---

## Table of Contents

1. [Getting Started](#1-getting-started)
2. [Core Modules](#2-core-modules)
3. [Advanced Features](#3-advanced-features)
4. [Analytics & Reporting](#4-analytics--reporting)
5. [Administration](#5-administration)
6. [Security & Compliance](#6-security--compliance)
7. [Notifications](#7-notifications)

---

## 1. Getting Started

### 1.1 What is ZKValue

ZKValue is a verification and valuation platform designed for financial institutions and asset managers. It uses zero-knowledge proof technology to provide cryptographically verifiable attestations for private credit portfolios and AI intellectual property assets. Every verification generates an immutable proof that can be anchored on-chain for tamper-proof audit trails.

### 1.2 Registration and First Login

1. Navigate to the ZKValue application URL provided by your organization administrator.
2. If you have received an invitation email, click the link to set up your account.
3. Enter your full name, email address, and a secure password.
4. After registration, you will be redirected to the login page.
5. Enter your credentials and click **Sign In** to access the dashboard.

> **Note:** If you do not have an account, ask your organization's Owner or Admin to send you an invitation from **Settings > Team Members**.

### 1.3 Dashboard Overview

The main dashboard provides a high-level summary of your organization's verification activity. It is divided into the following sections:

| Section | Description |
|---------|-------------|
| **Stat Cards** | Four summary cards showing Total Verifications, Total Asset Value, Credit Portfolios, and AI Assets Valued. Each card includes a sparkline trend and percentage change indicator. |
| **Recent Verifications** | A list of the most recent verification requests with their name, module (Credit or AI-IP), status badge, and timestamp. Click any row to view details. |
| **Monthly Usage** | A progress bar showing how many verifications you have used this billing cycle versus your plan limit. |
| **Value by Module** | A donut chart breaking down total verified value by module (Private Credit vs. AI-IP). |
| **Quick Actions** | Shortcut buttons to **Upload Loan Tape** (Private Credit) and **New AI-IP Valuation**. |

### 1.4 User Roles

ZKValue supports four user roles with hierarchical permissions:

| Role | Permissions |
|------|-------------|
| **Owner** | Full access. Can manage billing, delete the organization, transfer ownership, and perform all Admin actions. One per organization. |
| **Admin** | Can invite/remove users, manage settings, configure LLM providers, create blockchain anchors, and perform all Analyst actions. |
| **Analyst** | Can create verifications, upload loan tapes, run valuations, execute stress tests, generate reports, and view all data. |
| **Viewer** | Read-only access. Can view verifications, reports, analytics, and audit logs but cannot create or modify data. |

### 1.5 Sidebar Navigation

The left sidebar provides access to all modules. It is organized into three groups:

**Core:**
- Dashboard
- Verifications
- Private Credit
- AI-IP Valuation
- Document AI

**Analysis & Compliance:**
- Stress Testing
- NL Query
- Regulatory
- Blockchain
- Model Registry

**Administration:**
- Schedules
- Analytics
- Audit Log
- Team
- Billing
- Settings

> **Tip:** Click the chevron icon at the top of the sidebar to collapse it, giving more horizontal space to the main content area.

---

## 2. Core Modules

### 2.1 Private Credit Verification

#### What It Does

The Private Credit module allows you to upload loan portfolio data (loan tapes) and receive a verified analysis of portfolio metrics including Net Asset Value (NAV), weighted average interest rates, loan-to-value (LTV) ratios, and covenant compliance -- all backed by a zero-knowledge proof.

#### How to Upload a Loan Tape

1. Navigate to **Private Credit** in the sidebar.
2. Click the **Upload Loan Tape** button in the header (or click the **Add New Portfolio** card if you already have portfolios).
3. In the upload modal, either:
   - Drag and drop your file onto the drop zone, or
   - Click **Browse Files** to select a file from your computer.
4. Wait for the file to process. A success notification will appear when the upload is complete and verification has started.

**Supported file formats:**

| Format | Extension | Notes |
|--------|-----------|-------|
| CSV | `.csv` | Comma-separated values |
| Excel | `.xlsx` | Modern Excel format |
| JSON | `.json` | Structured JSON loan data |

#### Understanding Portfolio Results

Once processing is complete, each portfolio card displays four key metrics:

| Metric | Description |
|--------|-------------|
| **NAV** | Net Asset Value -- the computed fair value of the loan portfolio. |
| **Loans** | Total number of individual loans in the portfolio. |
| **Avg Rate** | The weighted average interest rate across all loans, displayed as a percentage. |
| **Avg LTV** | The average loan-to-value ratio, indicating collateral coverage. |

The summary bar at the top of the page aggregates these metrics across all portfolios: Total NAV, number of Portfolios, Total Loans, and overall Average Rate.

#### Reading Covenant Compliance Cards

Each portfolio card includes a covenant compliance indicator:

- **All Covenants Met** (green badge with checkmark): Every covenant condition in the portfolio has been satisfied.
- **Covenant Breach** (amber badge with warning icon): One or more covenant conditions have been violated and require attention.

Click **View Details** on any portfolio card to see a breakdown of individual covenant statuses.

#### Downloading Verification Reports

From the Verifications list (see Section 2.3), click the download icon next to any completed verification to obtain a PDF proof certificate and detailed report.

---

### 2.2 AI-IP Asset Valuation

#### What It Does

The AI-IP Valuation module assesses the fair market value of artificial intelligence intellectual property assets. It supports multiple asset types and valuation methodologies, and checks compliance with international accounting standards (IAS 38 and ASC 350).

#### How to Create a New Valuation

1. Navigate to **AI-IP Valuation** in the sidebar.
2. Click the **New Valuation** button in the header.
3. Fill out the valuation form:
   - **Asset Name** (required): A descriptive name for the asset (e.g., "Proprietary LLM Training Dataset").
   - **Asset Type** (required): Select one of the four types (see table below).
   - **Description**: A free-text description of the asset, its characteristics, and relevant context.
   - **Training Cost ($)**: The total cost invested in training or creating the asset.
   - **Compute Hours**: The number of GPU/compute hours consumed.
   - **Monthly Revenue ($)**: Current monthly revenue attributable to the asset.
   - **Model Parameters**: The number of parameters (for model-type assets).
4. Click **Start Valuation**. The system will process the inputs and generate a valuation with a confidence score.

#### Asset Types

| Asset Type | Description | Example |
|-----------|-------------|---------|
| **Training Data** | Proprietary datasets used for model training | Curated financial document corpus |
| **Model Weights** | Trained neural network parameters | Fine-tuned 70B parameter LLM |
| **Inference Infrastructure** | Optimized serving and deployment systems | Custom inference pipeline with GPU cluster |
| **Deployed Application** | Production AI applications generating revenue | AI-powered document analysis SaaS |

#### Valuation Methods

ZKValue applies three industry-standard approaches to determine fair value:

| Method | Approach |
|--------|----------|
| **Cost Approach** | Values the asset based on the cost to recreate it (training cost, compute, data acquisition). |
| **Market Approach** | Compares the asset to similar assets that have been sold or licensed in the market. |
| **Income Approach** | Projects future revenue streams and discounts them to present value. |

The valuation method used is displayed as a badge on each asset card.

#### Understanding Confidence Scores

Each valuation includes a confidence score (0--100%) displayed as both a percentage and a progress bar. Higher scores indicate greater reliability of the valuation estimate based on the quantity and quality of input data provided.

> **Tip:** Provide as much input data as possible (training cost, compute hours, revenue, parameters) to maximize the confidence score.

#### IAS 38 and ASC 350 Compliance

Each asset card displays compliance badges:

- **IAS 38**: International Accounting Standard 38 -- Intangible Assets (IFRS).
- **ASC 350**: Accounting Standards Codification 350 -- Intangibles (US GAAP).

A green badge with a checkmark indicates the valuation meets the respective standard's recognition and measurement criteria.

The summary bar shows the ratio of compliant assets (e.g., "4/5" means 4 out of 5 assets are IAS 38 compliant).

---

### 2.3 Verification Management

#### Viewing All Verifications

Navigate to **Verifications** in the sidebar. The page displays a paginated table of all verification requests across both modules.

Each row shows:

| Column | Description |
|--------|-------------|
| **Verification** | Name of the portfolio or asset, plus a unique verification ID. |
| **Module** | Either "Credit" (Private Credit) or "AI-IP" (AI-IP Valuation). |
| **Status** | Current processing state (see status table below). |
| **Value** | The computed NAV or estimated value (if available). |
| **Date** | When the verification was created. |
| **Proof** | A truncated proof hash if the ZK proof has been generated. |
| **Actions** | Download report (if available) and view details. |

**Verification statuses:**

| Status | Meaning |
|--------|---------|
| **Completed** | Verification finished successfully. Proof and results are available. |
| **Processing** | Verification is currently being computed. |
| **Pending** | Verification is queued and waiting to start. |
| **Failed** | Verification encountered an error. Check details for more information. |

#### Filtering by Module and Status

Use the filter dropdowns above the table:

- **Module filter**: Select "All Modules", "Private Credit", or "AI-IP Valuation".
- **Status filter**: Select "All Statuses", "Completed", "Processing", "Pending", or "Failed".
- **Search**: Type in the search box to filter by portfolio or asset name.

Results update immediately. Pagination adjusts to reflect the filtered count.

#### Verification Detail Page

Click any verification row to open its detail page, which is organized into tabs:

- **Overview**: Displays full verification metadata, portfolio/asset summary, and computed results.
- **Proof**: Shows the zero-knowledge proof hash, generation timestamp, and proof verification status.
- **Report**: Provides a downloadable PDF report with detailed findings and the proof certificate.

#### Proof Verification and Certificates

Each completed verification generates a cryptographic proof hash (displayed in monospace format, e.g., `0xabc123...`). This hash can be:

1. Verified against on-chain data using the **Blockchain** module.
2. Downloaded as part of the PDF proof certificate.
3. Shared with third parties for independent verification.

---

## 3. Advanced Features

### 3.1 Document AI

#### What It Does

Document AI uses artificial intelligence to parse loan tape documents in various formats. It extracts structured loan data from PDFs and spreadsheets, including loan IDs, principal amounts, balances, interest rates, LTV ratios, and loan statuses.

Navigate to **Document AI** in the sidebar to access this feature.

#### Supported Formats and Size Limits

| Format | Extensions | Maximum Size |
|--------|-----------|-------------|
| PDF | `.pdf` | 50 MB |
| Excel | `.xlsx`, `.xls` | 50 MB |
| CSV | `.csv` | 50 MB |

#### How to Use Document AI

1. Click or drag a file into the upload zone.
2. Once a file is selected, its name and size are displayed with a green confirmation. Click the **Remove** button to clear the selection and choose a different file.
3. Choose one of two actions:

| Action | Description |
|--------|-------------|
| **Parse Only** | Extracts loan data from the document and displays a preview table. No verification is created. Use this to inspect the data before committing. |
| **Parse & Verify** | Extracts loan data and immediately initiates a Private Credit verification. A verification ID is assigned and the process begins automatically. |

#### Understanding Results

After processing, the results section displays:

- **Extraction Method**: The AI technique used (e.g., OCR for PDFs, table parsing for spreadsheets).
- **Loans Extracted**: Total count of loan records found.
- **Warnings**: Any data quality issues detected during extraction (e.g., missing fields, format inconsistencies). Warnings are displayed as amber-colored alert cards.
- **Loan Preview**: A table showing the first 5 extracted loans with their Loan ID, Principal, Balance, Rate, LTV, and Status columns.

> **Tip:** Use **Parse Only** first to verify that the extraction is accurate before running **Parse & Verify** to avoid creating unnecessary verification records.

---

### 3.2 Blockchain Anchoring

#### What On-Chain Proof Anchoring Means

Blockchain anchoring creates an immutable, tamper-proof record of verification proofs on a public blockchain. ZKValue batches multiple proof hashes into a Merkle tree and publishes the Merkle root as a single on-chain transaction. This allows anyone to independently verify that a proof existed at a specific point in time without revealing the underlying data.

Navigate to **Blockchain** in the sidebar.

#### Viewing Anchors and Transactions

The Anchors table displays all blockchain anchor records with the following columns:

| Column | Description |
|--------|-------------|
| **Date** | When the anchor was created. |
| **Merkle Root** | The root hash of the Merkle tree containing the batched proofs. |
| **Proofs** | Number of individual proofs included in this anchor. |
| **TX Hash** | The blockchain transaction hash. Click to view on the block explorer (e.g., Etherscan). |
| **Status** | "Confirmed" (finalized on-chain), "Pending" (awaiting confirmation), or "Failed". |
| **Chain** | The blockchain network used (e.g., Polygon, Ethereum, Base). |

Summary stats at the top show **Total Anchors** and **Total Proofs Anchored**.

#### Creating a Daily Anchor

Admins and Owners can click the **Create Daily Anchor** button to batch all unanchored proofs into a new Merkle tree and submit the root hash on-chain.

> **Note:** Only users with the Admin or Owner role can create anchors.

#### Verifying Proof Integrity

Use the **Proof Verification** section at the bottom of the page:

1. Enter a proof hash in the input field (e.g., `0xabc...`).
2. Click **Verify On-Chain** (or press Enter).
3. The verification result displays:
   - **Anchored**: Whether the proof is included in an on-chain anchor (Yes/No).
   - **Merkle Valid**: Whether the proof's Merkle path is valid (Valid/Invalid).
   - **TX Hash**: The associated transaction hash (clickable link to block explorer).
   - **Block Number**: The block in which the anchor transaction was included.

#### Supported Chains

| Chain | Use Case |
|-------|----------|
| **Polygon** | Default chain; low-cost, fast finality. |
| **Ethereum** | Maximum security and decentralization. |
| **Base** | Ethereum L2 with lower fees. |

---

### 3.3 Stress Testing

Navigate to **Stress Testing** in the sidebar. Stress testing is available for completed Private Credit verifications.

#### Getting Started

1. Select a completed Private Credit verification from the dropdown at the top of the page.
2. Choose one of three tabs: **Scenario Presets**, **Custom Scenario**, or **Monte Carlo**.

#### Preset Scenarios

Click **Run All Scenarios** to execute all predefined stress scenarios simultaneously. Each scenario card displays:

- **Scenario Name**: The type of stress applied.
- **Severity Badge**: Low (green, loss rate < 5%), Moderate (amber, 5--15%), or High (red, > 15%).
- **Loss Rate**: Percentage of portfolio value lost under the scenario.
- **Stressed NAV**: The portfolio NAV after applying the stress.
- **Loans Underwater**: Number of loans where the balance exceeds collateral value.
- **Avg Default Probability**: The mean probability of default across loans.

#### Custom Scenarios

Configure your own stress parameters using three adjustable controls:

| Parameter | Range | Default | Description |
|-----------|-------|---------|-------------|
| **Rate Shock (bps)** | -500 to +1,000 | 200 | Basis point change in interest rates. |
| **Default Multiplier** | 0.1x to 10x | 2.0x | Multiplier applied to baseline default probabilities. |
| **Collateral Haircut (%)** | 0% to 80% | 20% | Percentage reduction in collateral values. |

Each parameter can be set using either the slider or the numeric input field. Click **Run Custom Scenario** to execute.

#### Monte Carlo Simulation

Monte Carlo simulation runs thousands of randomized scenarios to estimate the distribution of potential outcomes.

1. Set the **Number of Simulations** (100 to 10,000). Higher values yield more accurate results but take longer.
2. Click **Run Monte Carlo**.

Results include:

| Metric | Description |
|--------|-------------|
| **VaR 95%** | Value at Risk at the 95th percentile -- the loss rate exceeded only 5% of the time. |
| **VaR 99%** | Value at Risk at the 99th percentile -- the loss rate exceeded only 1% of the time. |
| **Expected Loss Rate** | The mean loss rate across all simulations. |
| **NAV Distribution** | Shows the 5th percentile (worst case), median (most likely), and 95th percentile (best case) NAV outcomes, along with a visual gradient bar. |

After running Monte Carlo, click **Generate Narrative** to produce an AI-written plain-English summary of the stress test results.

---

### 3.4 Regulatory Reports

Navigate to **Regulatory** in the sidebar.

ZKValue supports two regulatory report types, presented side-by-side:

#### SEC Form PF

Quarterly reporting form for registered investment advisers managing private funds. Provides systemic risk data to the SEC.

1. Click **Generate Report**.
2. The report is generated and displayed as expandable accordion sections. Click any section title to expand and view the underlying data fields.
3. Optionally, click **Generate Narrative** to produce an AI-written narrative covering:
   - **Filing Summary**: Overview of the filing.
   - **Risk Disclosure**: Key risk factors and exposures.
   - **Compliance Attestation**: Statement of regulatory compliance.
   - **Recommendations**: Suggested actions and improvements.

#### AIFMD Annex IV

Alternative Investment Fund Managers Directive Annex IV reporting for EU regulatory transparency. The workflow is identical to SEC Form PF:

1. Click **Generate Report** to create the report.
2. Expand accordion sections to review data.
3. Click **Generate Narrative** for AI-generated narratives.

> **Note:** Reports are generated from your current verification data. Ensure your portfolios are up to date before generating regulatory filings.

---

### 3.5 Scheduling & Drift Detection

Navigate to **Schedules** in the sidebar. This page has two tabs: **Schedules** and **Drift Alerts**.

#### Creating Verification Schedules

1. Click **New Schedule** to open the creation modal.
2. Fill in the form:

| Field | Description |
|-------|-------------|
| **Schedule Name** | A descriptive name (e.g., "Monthly Credit Portfolio Review"). |
| **Module** | Select "Private Credit" or "AI-IP Valuation". |
| **Frequency** | Choose from Daily, Weekly, Monthly, or Quarterly. |
| **Drift Threshold (%)** | The percentage change that triggers a drift alert (e.g., 5%). |
| **Input Data (JSON)** | JSON object with parameters for the verification (e.g., portfolio ID). |

3. Click **Create Schedule**.

#### Managing Schedules

Each schedule card displays:
- Schedule name, module badge, and frequency.
- **Active/Paused** status toggle (click to switch).
- Next scheduled run date and time.
- Total number of completed runs.
- Configured drift threshold.

Available actions:
- **Run Now**: Trigger an immediate verification run outside the schedule.
- **Pause/Resume**: Toggle the schedule on or off.
- **Delete**: Permanently remove the schedule (with confirmation).

#### Drift Threshold Configuration

The drift threshold defines the percentage change in a key metric (e.g., NAV) between consecutive verification runs that will trigger an alert. For example, a 5% threshold means an alert is generated if NAV changes by more than 5% between runs.

#### Understanding Drift Alerts

Switch to the **Drift Alerts** tab to view all alerts. The table includes:

| Column | Description |
|--------|-------------|
| **Severity** | Critical (red), Warning (amber), or Info (blue). |
| **Alert Type** | The category of drift detected (e.g., nav_drift, rate_drift). |
| **Message** | Human-readable description of what changed. |
| **Drift** | The actual percentage change that triggered the alert. |
| **Status** | New, Acknowledged, or Resolved. |
| **Timestamp** | When the alert was generated. |

**Severity levels:**

| Level | Meaning |
|-------|---------|
| **Critical** | Significant drift requiring immediate attention. |
| **Warning** | Notable change that should be investigated. |
| **Info** | Minor drift within acceptable ranges but worth noting. |

#### Acknowledging and Resolving Alerts

- **Acknowledge**: Click the "Acknowledge" button on any "New" alert to indicate you are aware of it. The status changes to "Acknowledged".
- **Resolve**: Click "Resolve" on any non-resolved alert to mark it as addressed. The status changes to "Resolved".

Use the severity and status filter dropdowns to focus on specific alert categories.

---

### 3.6 Natural Language Query

Navigate to **NL Query** in the sidebar.

#### Asking Questions in Plain English

1. Type a question in the text area (e.g., "What is the total NAV of loans with LTV above 80%?").
2. Click **Ask** or press **Ctrl+Enter** to submit.
3. The system translates your question into SQL, executes it against your portfolio data, and returns results.

#### Using Suggested Queries

When no results are displayed, a **Suggested Questions** section shows pre-built query templates. Click any suggestion to populate the text area, then submit it.

#### Understanding SQL Translation and Results

Results are displayed in three sections:

1. **Answer**: A plain-English response to your question.
2. **Generated SQL**: An expandable code block showing the SQL query that was generated and executed. Click to expand/collapse.
3. **Results Table**: A data table with column headers and rows. If the query returns more rows than can be displayed, a summary note indicates the total count.

> **Tip:** Start with simple questions and progressively refine. The system understands terms like "total NAV", "average LTV", "loans above X%", "portfolios created this month", etc.

---

### 3.7 Model Registry & Data Lineage

Navigate to **Model Registry** in the sidebar. This page has two tabs: **Model Usage Stats** and **Verification Lineage**.

#### Tracking LLM Usage

The **Model Usage Stats** tab shows how your organization consumes LLM resources.

Select a time period using the segmented control: **7d**, **30d**, **90d**, or **1y**.

Four summary cards display:

| Card | Description |
|------|-------------|
| **Total Calls** | Number of LLM API calls made. |
| **Total Tokens** | Cumulative tokens consumed across all calls. |
| **Total Cost (USD)** | Aggregate cost of LLM usage. |
| **Avg Latency** | Average response time in milliseconds. |

Below the summary cards, a **Usage by Model** table breaks down metrics per model, showing Model Name, Provider, Calls, Tokens, Cost (USD), and Avg Latency.

#### Viewing Data Lineage for Verifications

Switch to the **Verification Lineage** tab:

1. Enter a verification ID in the search field.
2. Click **Load Lineage** (or press Enter).

The lineage view displays:

- **Data Pipeline**: A step-by-step timeline of data transformation events, each showing:
  - Step number (in a numbered circle).
  - Event type (e.g., "data ingestion", "normalization", "proof generation").
  - Transformation description.
  - Input hash and output hash (showing data integrity at each stage).
  - Processing duration.

- **LLM Calls**: A table listing every LLM call made during the verification, with Provider, Model, Operation, Tokens, Cost, Latency, and Success/Failed status.

- **Summary**: Aggregate statistics -- Total Events, LLM Calls, Total Tokens, and Total Cost.

#### Understanding the Data Pipeline

The data pipeline represents the complete chain of transformations applied to your data during a verification. Each step produces a cryptographic hash of its output, which becomes the input hash of the next step. This chain of hashes ensures that any tampering at any stage would be detectable, providing full data integrity from raw input to final proof.

---

## 4. Analytics & Reporting

Navigate to **Analytics** in the sidebar.

The Analytics page provides a comprehensive view of your organization's activity across six dashboard sections:

### Verification Trends

A stacked bar chart showing monthly verification counts, split into Completed (green) and Failed (red). Use this to monitor verification volume and success rates over time.

### Portfolio Performance Metrics

A full-width card displaying five key portfolio metrics:

| Metric | Description |
|--------|-------------|
| **Total NAV** | Sum of all portfolio Net Asset Values. |
| **Total Principal** | Sum of all outstanding principal balances. |
| **NAV / Principal** | Ratio indicating overall portfolio health. |
| **Avg Rate** | Weighted average interest rate. |
| **Avg LTV** | Average loan-to-value ratio. |

### AI Asset Performance Metrics

Displays Total Value, Average Confidence score, and compliance progress bars for IAS 38 and ASC 350 standards.

### Asset Type Breakdown

A donut chart and bar visualization showing the distribution of AI assets by type (Training Data, Model Weights, Inference Infra, Deployed App), including count, total value, and average confidence per type.

### Alert Summary

Shows the total number of alerts, how many are active, and a breakdown by severity (Critical, Warning, Info).

### Processing Performance

Per-module statistics showing:
- **Private Credit**: Total completed verifications and average processing time.
- **AI-IP Valuation**: Total completed verifications and average processing time.

---

## 5. Administration

### 5.1 Organization Settings

Navigate to **Settings** in the sidebar.

#### General Settings

- **Organization Name**: Update your organization's display name and click **Save Changes**.
- **Organization Slug**: A read-only URL-safe identifier for your organization.
- **Current Plan**: Displays your current subscription tier with a link to the Billing page for upgrades.

#### LLM Provider Configuration

Switch to the **LLM Configuration** tab in Settings.

ZKValue uses large language models for AI-powered analysis, document parsing, narrative generation, and natural language queries. You can choose from three providers:

| Provider | Available Models |
|----------|-----------------|
| **DeepSeek** (default) | deepseek-chat (fast, non-thinking), deepseek-reasoner (thinking/chain-of-thought) |
| **OpenAI** | gpt-4o, gpt-4o-mini, o1, o1-mini |
| **Anthropic** | claude-opus-4-6, claude-sonnet-4-6, claude-haiku-4-5-20251001 |

To change the provider:

1. Click the provider card to select it.
2. Choose a specific model from the dropdown.
3. Click **Save LLM Config**.

> **Note:** Non-default providers require you to supply your own API key. API keys are encrypted and stored securely.

#### Security Settings

The **Security** tab provides:

- **Two-Factor Authentication**: Enable 2FA for additional account security.
- **SSO / SAML**: Enterprise single sign-on (available on Enterprise plan only).
- **IP Allowlist**: Restrict platform access to specific IP addresses.

#### API Keys

The **API Keys** tab explains that API keys are managed via server-side environment variables for security. Contact your system administrator for API key configuration.

---

### 5.2 Team Management

Navigate to **Settings > Team Members** tab (or click **Team** in the sidebar).

#### Inviting Users

1. Click **Invite Member**.
2. Enter the invitee's email address.
3. Select a role:

| Role | Access Level |
|------|-------------|
| **Admin** | Full management access (settings, team, anchors), plus all Analyst capabilities. |
| **Analyst** | Can create and manage verifications, run analyses, and generate reports. |
| **Viewer** | Read-only access to all data and reports. |

4. Click **Send Invitation**. The invitee will receive an email with a link to join the organization.

#### Managing Team Members

The team member list shows each member's name, email, role badge, and last login date.

- To remove a member, click the trash icon next to their name. Owner accounts cannot be removed.
- Role changes can be managed by Admins and Owners.

---

### 5.3 Billing

Navigate to **Billing** in the sidebar.

#### Plans Overview

| Feature | Starter ($499/mo) | Professional ($1,999/mo) | Enterprise (Custom) |
|---------|-------------------|--------------------------|---------------------|
| Verifications/month | 10 | 50 | Unlimited |
| Proof certificates | PDF | PDF | PDF |
| Support | Email | Priority | Dedicated |
| Modules | 1 | Both | Both |
| Team members | 5 | 25 | Unlimited |
| API access | -- | Yes (+ webhooks) | Yes |
| White-label reports | -- | Yes | Yes |
| Custom LLM provider | -- | Yes | Yes |
| On-premise deployment | -- | -- | Yes |
| Custom ZK circuits | -- | -- | Yes |
| SSO / SAML | -- | -- | Yes |
| SLA guarantee | -- | -- | Yes |

Your current plan is highlighted with a "Current Plan" badge.

#### Upgrading or Downgrading

Click the **Upgrade** button on any plan card to initiate a checkout session. For Enterprise, the button reads **Contact Sales** and connects you with the sales team.

#### Payment Management

The **Payment Method** section displays your card on file (brand, last four digits, expiration). Click **Update** to open the billing portal and change your payment method. If no card is on file, click **Add** to enter payment details.

#### Invoice History

The Invoice History section lists all past invoices with:
- Billing month and year
- Payment status (e.g., "paid")
- Amount
- Download link (click the download icon to get a PDF invoice)

---

### 5.4 Audit Trail

Navigate to **Audit Log** in the sidebar.

#### Viewing Audit Logs

The audit log provides a complete record of all actions in your organization. Each entry includes:

| Column | Description |
|--------|-------------|
| **Timestamp** | Date and time of the action. |
| **User** | Name of the user who performed the action. |
| **Action** | Type of action performed, with a descriptive icon. |
| **Details** | Additional context about the action. |
| **IP Address** | The IP address from which the action was performed. |

**Tracked action types:**

| Action | Description |
|--------|-------------|
| Verification Created | A new verification request was submitted. |
| Verification Completed | A verification finished processing. |
| User Login | A user signed into the platform. |
| Settings Updated | Organization settings were modified. |
| Report Viewed | A report or verification detail was accessed. |
| Loan Tape Uploaded | A new loan tape file was uploaded. |
| Member Invited | A new team member was invited. |

#### Filtering and Searching

- **Search box**: Filter logs by user ID or keyword.
- **Action filter**: Select a specific action type or "All Actions".

#### Exporting to CSV

Click the **Export CSV** button in the header to download the full audit log as a CSV file. The file is named with the current date (e.g., `audit-log-2026-03-13.csv`).

---

## 6. Security & Compliance

### Zero-Knowledge Proof Technology

ZKValue uses zero-knowledge proofs (ZKPs) to verify data properties without revealing the underlying data. When a loan portfolio or AI asset is verified:

1. The raw data is processed locally.
2. A cryptographic proof is generated that attests to specific computed properties (e.g., "the portfolio NAV is $X" or "the average LTV is Y%").
3. This proof can be verified by any third party without access to the original loan-level data.

This approach enables transparent verification while preserving data confidentiality.

### Data Privacy

- Raw loan data and asset details are processed server-side and are never shared with external parties.
- Only cryptographic proofs and aggregated metrics leave the secure processing environment.
- LLM API calls to external providers (when configured) send only the minimum data necessary for analysis.

### SOC 2 Readiness

ZKValue is designed with SOC 2 compliance controls in mind:

- Complete audit trail of all user actions.
- Role-based access control with the principle of least privilege.
- Encrypted data storage and transmission (TLS in transit, AES-256 at rest).
- IP allowlisting and optional two-factor authentication.

### On-Chain Attestation

By anchoring proof hashes on public blockchains (Polygon, Ethereum, Base), ZKValue provides:

- **Immutability**: Once anchored, proofs cannot be altered or deleted.
- **Timestamping**: Each anchor transaction has a block timestamp, providing cryptographic proof of when the verification occurred.
- **Independent Verifiability**: Anyone can verify proof integrity using the blockchain transaction hash and the Proof Verification tool.

---

## 7. Notifications

### Notification Types

ZKValue generates notifications for the following events:

| Event | Description |
|-------|-------------|
| Verification completed | A verification has finished processing successfully. |
| Verification failed | A verification encountered an error during processing. |
| Drift alert triggered | A scheduled verification detected drift exceeding the configured threshold. |
| Team member joined | An invited user has accepted the invitation and created their account. |
| Plan usage warning | Monthly verification usage is approaching the plan limit. |
| Blockchain anchor confirmed | An on-chain anchor transaction has been confirmed. |

### Managing Preferences

Notification preferences can be configured from the Settings page. You can enable or disable specific notification types based on your role and responsibilities.

### Channel Configuration

Notifications are delivered through the following channels:

| Channel | Description |
|---------|-------------|
| **In-App** | Toast notifications that appear in the bottom-right corner of the application. These are always enabled. |
| **Email** | Email notifications for critical events (verification completions, drift alerts, security events). |
| **Webhooks** | HTTP POST notifications to a configured endpoint (Professional and Enterprise plans). Useful for integrating ZKValue events into your existing monitoring and alerting systems. |

---

*This guide covers all features available in ZKValue as of version 1.0. For additional support, contact your organization administrator or reach out to the ZKValue support team.*
