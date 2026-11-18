"""Synthetic enterprise dataset for "Northbridge Financial" — a FICTIONAL organisation.

Every person, team, project, URL and identifier in this file is invented. URLs use the
reserved `.example` top-level domain so they can never resolve to a real system.

Structure
---------
INITIATIVES : the Initiative Index (correlated catalogue of known initiatives).
RECORDS     : records as they would appear in each source system. Records are linked to
              each other through *source-native* references only — labels/components/topics,
              explicit links (e.g. a Jira epic linking a repo) and textual mentions — exactly as
              in real systems. Records carry no hidden "project id"; the pipeline correlates them.
SEED_IDEAS  : ideas previously registered in the Idea Registry.

Dates are expressed as "days ago" and converted to absolute timestamps at seed time so that
the lifecycle logic (active / stale / abandoned) behaves consistently whenever you seed.

Planted evaluation cases
------------------------
A  Strong duplicate        - SecureGuard AI (AppSec) vs "AI cybersecurity checker".
B  Partial overlap         - CaseLens fraud *investigation* assistant vs real-time fraud *detection*.
C  No significant match    - e.g. carbon footprint of business travel (nothing in the dataset).
D  Abandoned project       - DocuMind contract clause extractor (inactive > 1 year, archived).
E  Deployed solution       - AccessFlow access-request automation (ServiceNow catalogue, live).
F  Different names, same objective - Pipeline Sentinel (Data Analytics) vs Trustworthy Data
                             Initiative (Operations) both address data quality.
G  Similar names / keywords, different function - Pipeline Sentinel vs API Sentinel;
                             ReviewPilot (AI code review) vs Secure Code Review Board (governance).
"""
from __future__ import annotations

ORG = "Northbridge Financial (fictional)"
DOMAIN = "northbridge.example"


def email(name: str) -> str:
    local = name.lower().replace("'", "").replace("é", "e").replace("ö", "o").replace("ä", "a")
    local = ".".join(p for p in local.replace("-", " ").split())
    return f"{local}@{DOMAIN}"


# ---------------------------------------------------------------------------------------------
# Initiative Index
# ---------------------------------------------------------------------------------------------
INITIATIVES: list[dict] = [
    {
        "id": "INIT-001", "name": "SecureGuard AI",
        "aliases": ["SecureGuard", "secureguard-scanner", "Application Security Automation PoC", "Automated Vulnerability Scanner"],
        "correlation_keys": ["secureguard", "SEC-284", "northbridge-appsec/secureguard-scanner"],
        "department": "Cybersecurity Engineering", "team": "Application Security Engineering",
        "owner": "Priya Raman",
        "description": "AI-assisted application security scanner that runs static analysis (SAST), dependency (SCA) and secret scanning across internal GitHub Enterprise repositories and posts LLM-generated remediation suggestions on pull requests.",
        "business_objective": "Reduce the number of exploitable vulnerabilities reaching production by automatically scanning internal code repositories and recommending fixes to developers early in the development lifecycle.",
        "core_features": ["Static application security testing (SAST) of internal repositories", "Dependency / software composition analysis (SCA)", "Hardcoded secret detection", "LLM-generated fix suggestions posted as pull request comments", "Severity triage dashboard for the AppSec team"],
        "target_users": ["Software developers", "Application security engineers"],
        "technologies": ["Python", "Semgrep", "CodeQL", "GitHub Actions", "Internal LLM gateway", "PostgreSQL"],
        "status": "active_development", "created_days_ago": 300, "last_activity_days_ago": 3,
        "reusable_components": ["Semgrep rule pack for Northbridge internal frameworks", "GitHub App that posts review comments on pull requests", "Remediation prompt library (Java, Python, TypeScript)", "Vulnerability triage REST API"],
        "notes": "Pilot covers 140 repositories in Payments and Lending. Team is actively looking for additional pilot business units.",
    },
    {
        "id": "INIT-002", "name": "Cloud Watchtower",
        "aliases": ["Cloud Configuration Security Monitor", "watchtower-rules"],
        "correlation_keys": ["cloud-watchtower", "CLDSEC-88", "cloud-platform/watchtower-rules"],
        "department": "Cloud Infrastructure", "team": "Cloud Platform Security", "owner": "Daniel Okafor",
        "description": "Continuously evaluates AWS and Azure accounts for misconfigurations such as public storage buckets, overly permissive IAM roles, open security groups and unencrypted volumes, and notifies resource owners.",
        "business_objective": "Detect and reduce cloud misconfigurations across AWS and Azure accounts before they can be exploited.",
        "core_features": ["Cloud security posture checks across AWS and Azure", "Policy-as-code rules for IAM, storage and network configuration", "Owner notification and escalation", "Terraform drift detection"],
        "target_users": ["Cloud engineers", "Security operations"],
        "technologies": ["Terraform", "Open Policy Agent", "AWS Config", "Azure Policy", "Python"],
        "status": "active_development", "created_days_ago": 210, "last_activity_days_ago": 11,
        "reusable_components": ["OPA policy library for AWS/Azure", "Resource-owner lookup service"],
        "notes": None,
    },
    {
        "id": "INIT-003", "name": "CaseLens Fraud Investigation Assistant",
        "aliases": ["CaseLens", "Fraud Investigation Assistant"],
        "correlation_keys": ["caselens", "FRD-142"],
        "department": "Fraud & Risk", "team": "Fraud Operations Analytics", "owner": "Elena Vasquez-Hart",
        "description": "Generative AI assistant for fraud investigators that summarises case evidence, prioritises the alert queue and drafts suspicious activity report (SAR) narratives. It consumes alerts produced by the existing transaction monitoring rules; it does not score or block transactions in real time.",
        "business_objective": "Reduce the time fraud investigators spend triaging alerts and assembling case files so that investigation backlogs shrink.",
        "core_features": ["Case evidence summarisation", "Alert queue prioritisation for investigators", "SAR narrative drafting", "Investigator Q&A over case history"],
        "target_users": ["Fraud investigators", "Fraud operations managers"],
        "technologies": ["Internal LLM gateway", "Python", "Case management system API"],
        "status": "proof_of_concept", "created_days_ago": 150, "last_activity_days_ago": 8,
        "reusable_components": ["Case summarisation prompt set", "Connector to the case management system", "PII redaction pre-processor"],
        "notes": "Explicitly out of scope: real-time transaction scoring or blocking.",
    },
    {
        "id": "INIT-004", "name": "MuleNet Network Analytics",
        "aliases": ["MuleNet", "Mule Account Network Analytics"],
        "correlation_keys": ["mulenet", "FCA-38"],
        "department": "Fraud & Risk", "team": "Financial Crime Analytics", "owner": "Oluwaseun Adeyemi",
        "description": "Research into graph analytics that identify networks of money-mule accounts from historical transfer data using weekly batch link analysis.",
        "business_objective": "Identify organised money-mule networks that individual alerts miss by analysing relationships between accounts.",
        "core_features": ["Weekly batch graph construction from transfer history", "Community detection for mule networks", "Investigator network visualisation"],
        "target_users": ["Financial crime analysts"],
        "technologies": ["Neo4j", "PySpark", "Python"],
        "status": "research", "created_days_ago": 120, "last_activity_days_ago": 26,
        "reusable_components": ["Account-relationship graph schema"],
        "notes": "Batch only; no real-time component planned.",
    },
    {
        "id": "INIT-005", "name": "DocuMind Contract Clause Extractor",
        "aliases": ["DocuMind"],
        "correlation_keys": ["documind", "LGL-57", "legaltech/documind"],
        "department": "Enterprise Technology", "team": "Legal Technology", "owner": "Samuel Achterberg",
        "description": "Proof of concept that used OCR and NLP to extract key clauses — termination rights, indemnities, renewal dates and obligations — from vendor contracts into a searchable register.",
        "business_objective": "Reduce manual legal review effort by automatically extracting key terms and renewal dates from vendor contracts.",
        "core_features": ["OCR of scanned contracts", "Clause extraction (termination, indemnity, renewal)", "Renewal date register with reminders"],
        "target_users": ["Legal team", "Procurement"],
        "technologies": ["Python", "Tesseract OCR", "spaCy", "Azure Form Recognizer"],
        "status": "abandoned", "created_days_ago": 720, "last_activity_days_ago": 430,
        "reusable_components": ["Annotated contract clause dataset (420 contracts)", "OCR pre-processing pipeline"],
        "notes": "Stopped after the PoC: clause extraction accuracy on scanned contracts was 71% against a 90% target and funding was not renewed.",
    },
    {
        "id": "INIT-006", "name": "AccessFlow",
        "aliases": ["AccessFlow Access Request Automation", "Request Application Access"],
        "correlation_keys": ["accessflow", "APP0004417"],
        "department": "Enterprise Technology", "team": "Identity & Access Management", "owner": "Grace Liu",
        "description": "Deployed self-service access request service in the ServiceNow catalogue. Employees request application access; requests are routed to the line manager and application owner for approval and provisioned automatically for 300+ integrated applications.",
        "business_objective": "Let employees request system access through self-service with automatic approval routing and provisioning instead of emailing IT.",
        "core_features": ["Self-service access request catalogue item", "Automatic manager and application-owner approval routing", "Automated provisioning for 300+ applications", "Auto-approval for low-risk roles", "Quarterly access reviews"],
        "target_users": ["All employees", "Line managers", "Application owners"],
        "technologies": ["ServiceNow", "SailPoint", "Active Directory"],
        "status": "deployed", "created_days_ago": 900, "last_activity_days_ago": 6,
        "reusable_components": ["ServiceNow access request workflow", "Provisioning connectors for 300+ applications"],
        "notes": "Approximately 18,000 requests per month.",
    },
    {
        "id": "INIT-007", "name": "Pipeline Sentinel",
        "aliases": ["pipeline-sentinel", "Data Observability Platform"],
        "correlation_keys": ["pipeline-sentinel", "DATA-412", "data-platform/pipeline-sentinel"],
        "department": "Data Analytics", "team": "Data Platform Engineering", "owner": "Tomasz Wierzbicki",
        "description": "Data observability service for the enterprise data warehouse: automated freshness, volume, schema-drift and null-rate checks on dbt/Airflow pipelines with alerts routed to data owners before downstream reports are published.",
        "business_objective": "Catch data quality issues in warehouse pipelines before they reach downstream reports and dashboards.",
        "core_features": ["Freshness and late-arrival checks on data feeds", "Volume and completeness anomaly detection", "Schema drift detection", "Alerting to data owners", "Data quality scorecards"],
        "target_users": ["Data engineers", "Data stewards", "Reporting teams"],
        "technologies": ["dbt", "Airflow", "Snowflake", "Great Expectations", "Python"],
        "status": "active_development", "created_days_ago": 260, "last_activity_days_ago": 5,
        "reusable_components": ["Great Expectations check library", "Airflow alerting plugin", "Data quality scorecard dashboards"],
        "notes": None,
    },
    {
        "id": "INIT-008", "name": "Trustworthy Data Initiative",
        "aliases": ["Trustworthy Data"],
        "correlation_keys": ["trustworthy-data"],
        "department": "Operations", "team": "Operations Control & Reporting", "owner": "Aisha Bello",
        "description": "Operations-led initiative to make sure the figures in daily operational and regulatory reports can be trusted: detect late or incomplete upstream feeds and reconcile totals between source systems before reports are published.",
        "business_objective": "Ensure the numbers in daily operations and regulatory reports can be trusted by catching late or incomplete feeds and reconciling totals before publication.",
        "core_features": ["Late / incomplete feed detection", "Cross-system total reconciliation", "Pre-publication report sign-off checks"],
        "target_users": ["Operations analysts", "Reporting team"],
        "technologies": ["Excel", "SQL", "Power BI"],
        "status": "research", "created_days_ago": 90, "last_activity_days_ago": 14,
        "reusable_components": [],
        "notes": "Uses operations terminology ('feeds', 'figures', 'reconciliation') rather than data-engineering terminology.",
    },
    {
        "id": "INIT-009", "name": "ReviewPilot",
        "aliases": ["Developer Code Review Assistant", "reviewpilot"],
        "correlation_keys": ["reviewpilot", "DEVX-219", "devex/reviewpilot"],
        "department": "Developer Productivity", "team": "Developer Experience", "owner": "Hannah Kowalczyk",
        "description": "AI pull request reviewer that summarises changes and suggests improvements for readability, maintainability, likely bugs and missing tests.",
        "business_objective": "Shorten pull request review cycle time and improve code quality by giving developers an automated first-pass review.",
        "core_features": ["Pull request summaries", "Readability and maintainability suggestions", "Likely-bug detection", "Missing-test hints"],
        "target_users": ["Software developers", "Tech leads"],
        "technologies": ["Internal LLM gateway", "TypeScript", "GitHub App"],
        "status": "proof_of_concept", "created_days_ago": 140, "last_activity_days_ago": 12,
        "reusable_components": ["PR diff chunking library"],
        "notes": "Does not perform security scanning; defers security findings to the AppSec team.",
    },
    {
        "id": "INIT-010", "name": "Secure Code Review Board",
        "aliases": ["SCRB"],
        "correlation_keys": ["scrb", "KB0019034"],
        "department": "Compliance", "team": "Technology Risk & Controls", "owner": "Victor Hallström",
        "description": "Governance process: a review board that manually signs off high-risk application changes against a security checklist and keeps attestation records for audit.",
        "business_objective": "Provide documented governance sign-off and audit attestation for high-risk technology changes.",
        "core_features": ["Board review sessions for high-risk changes", "Security checklist and attestation", "Policy exception records"],
        "target_users": ["Compliance officers", "Change owners"],
        "technologies": ["ServiceNow", "Confluence"],
        "status": "deployed", "created_days_ago": 1100, "last_activity_days_ago": 20,
        "reusable_components": ["Secure change checklist"],
        "notes": "A manual governance process, not a software tool.",
    },
    {
        "id": "INIT-011", "name": "GenBI Insights",
        "aliases": ["Generative BI Analytics Platform", "GenBI"],
        "correlation_keys": ["genbi", "AIL-77", "ai-lab/genbi-insights"],
        "department": "AI Innovation", "team": "AI Innovation Lab", "owner": "Rafael Mendes",
        "description": "Generative BI assistant that answers business questions in natural language by generating SQL against the governed warehouse semantic layer and producing charts.",
        "business_objective": "Give business users self-service analytics through natural language questions instead of waiting for report requests.",
        "core_features": ["Natural language to SQL", "Automatic chart generation", "Governed semantic layer", "Query explanation"],
        "target_users": ["Business analysts", "Business leaders"],
        "technologies": ["Internal LLM gateway", "Snowflake", "Python", "React"],
        "status": "proof_of_concept", "created_days_ago": 170, "last_activity_days_ago": 9,
        "reusable_components": ["Semantic-layer metadata API", "Text-to-SQL evaluation set"],
        "notes": None,
    },
    {
        "id": "INIT-012", "name": "Onboarding Buddy",
        "aliases": ["Automated Employee Onboarding Agent", "Onboarding Buddy Agent"],
        "correlation_keys": ["onboarding-buddy", "HRT-130"],
        "department": "Human Resources Technology", "team": "People Technology", "owner": "Nadia Rahman",
        "description": "Conversational agent that guides new hires through their first 30 days: answers HR policy questions, tracks onboarding tasks and triggers equipment and account provisioning requests.",
        "business_objective": "Give new joiners a consistent onboarding experience and reduce manual HR coordination effort.",
        "core_features": ["New hire Q&A on HR policies", "Onboarding task checklist tracking", "Equipment and account provisioning triggers", "Manager nudges"],
        "target_users": ["New hires", "Hiring managers", "HR partners"],
        "technologies": ["Microsoft Teams bot", "Internal LLM gateway", "Workday API", "ServiceNow"],
        "status": "active_development", "created_days_ago": 200, "last_activity_days_ago": 7,
        "reusable_components": ["HR policy retrieval index", "Teams bot framework template"],
        "notes": None,
    },
    {
        "id": "INIT-013", "name": "OpsSleuth Incident Investigation Agent",
        "aliases": ["OpsSleuth", "Incident Investigation Agent"],
        "correlation_keys": ["opssleuth", "SRE-501", "sre/opssleuth"],
        "department": "Operations", "team": "Site Reliability Engineering", "owner": "Kenji Watanabe",
        "description": "During major incidents, correlates alerts, logs and recent change records to suggest probable root causes and drafts incident timelines and postmortems.",
        "business_objective": "Reduce mean time to resolution (MTTR) for production incidents.",
        "core_features": ["Alert and log correlation", "Recent change correlation (ServiceNow CHG)", "Probable root cause suggestions", "Timeline and postmortem drafting"],
        "target_users": ["Site reliability engineers", "On-call engineers"],
        "technologies": ["Python", "Splunk", "ServiceNow", "Internal LLM gateway"],
        "status": "proof_of_concept", "created_days_ago": 160, "last_activity_days_ago": 16,
        "reusable_components": ["Change-record correlation service"],
        "notes": None,
    },
    {
        "id": "INIT-014", "name": "AskNorthbridge Knowledge Assistant",
        "aliases": ["AskNorthbridge", "Enterprise Knowledge Assistant"],
        "correlation_keys": ["asknorthbridge", "APP0005120"],
        "department": "Enterprise Technology", "team": "Digital Workplace", "owner": "Olivia Brennan",
        "description": "Retrieval-augmented assistant that answers employee questions using intranet policies, Confluence and SharePoint content, with citations.",
        "business_objective": "Help employees find answers in internal documentation quickly without raising service desk tickets.",
        "core_features": ["Retrieval-augmented Q&A with citations", "Intranet, Confluence and SharePoint indexing", "Permission-aware retrieval"],
        "target_users": ["All employees"],
        "technologies": ["Internal LLM gateway", "Elasticsearch", "Python"],
        "status": "deployed", "created_days_ago": 400, "last_activity_days_ago": 10,
        "reusable_components": ["Permission-aware retrieval service", "Document chunking pipeline"],
        "notes": None,
    },
    {
        "id": "INIT-015", "name": "ControlScribe",
        "aliases": ["Compliance Documentation Automation"],
        "correlation_keys": ["controlscribe", "CMP-66"],
        "department": "Compliance", "team": "Compliance Engineering", "owner": "Marta Silva",
        "description": "Generates control narratives and assembles audit evidence packs by pulling evidence from tickets, change records and system reports.",
        "business_objective": "Reduce the manual effort of producing control documentation and audit evidence packs.",
        "core_features": ["Control narrative drafting", "Automated evidence collection", "Audit evidence pack assembly"],
        "target_users": ["Control owners", "Compliance analysts", "Auditors"],
        "technologies": ["Internal LLM gateway", "Python", "ServiceNow API", "Jira API"],
        "status": "active_development", "created_days_ago": 180, "last_activity_days_ago": 13,
        "reusable_components": ["Evidence collector connectors (Jira, ServiceNow)"],
        "notes": None,
    },
    {
        "id": "INIT-016", "name": "API Sentinel",
        "aliases": ["API Health Monitor", "Automated API Monitoring", "api-sentinel"],
        "correlation_keys": ["api-sentinel", "APP0003301", "platform/api-sentinel"],
        "department": "Cloud Infrastructure", "team": "API Platform", "owner": "Benedikt Krause",
        "description": "Synthetic monitoring for internal and partner APIs: scheduled synthetic checks, latency and error-rate tracking, SLA dashboards and alerting.",
        "business_objective": "Detect API degradation and SLA breaches before customers and partner integrations are affected.",
        "core_features": ["Synthetic API checks", "Latency and error-rate monitoring", "SLA dashboards", "On-call alerting"],
        "target_users": ["Platform engineers", "On-call engineers"],
        "technologies": ["Go", "Prometheus", "Grafana", "Kubernetes"],
        "status": "deployed", "created_days_ago": 500, "last_activity_days_ago": 4,
        "reusable_components": ["Synthetic check runner", "SLA dashboard templates"],
        "notes": "Shares the word 'Sentinel' with Pipeline Sentinel but monitors APIs, not data.",
    },
    {
        "id": "INIT-017", "name": "SmartRoute",
        "aliases": ["Customer Service Routing Assistant"],
        "correlation_keys": ["smartroute", "CX-310", "cx-tech/smartroute"],
        "department": "Customer Experience", "team": "Contact Centre Technology", "owner": "Isabel Ferreira",
        "description": "Classifies the intent of incoming customer emails and chats and routes them to the right contact-centre queue and agent skill group.",
        "business_objective": "Reduce customer wait times and transfers by routing inquiries to the right team the first time.",
        "core_features": ["Intent classification for email and chat", "Skill-based queue routing", "Urgency detection"],
        "target_users": ["Contact centre agents", "Customers"],
        "technologies": ["Python", "Fine-tuned classifier", "Genesys API"],
        "status": "active_development", "created_days_ago": 230, "last_activity_days_ago": 6,
        "reusable_components": ["Customer intent taxonomy", "Intent classifier"],
        "notes": None,
    },
    {
        "id": "INIT-018", "name": "LabelSmart Document Classification",
        "aliases": ["LabelSmart", "Document Classification Assistant"],
        "correlation_keys": ["labelsmart", "RIM-24"],
        "department": "Compliance", "team": "Records & Information Management", "owner": "Thandiwe Mokoena",
        "description": "Automatically classifies unstructured documents in SharePoint and file shares by document type and applies retention and sensitivity labels.",
        "business_objective": "Apply consistent retention and sensitivity labels to unstructured documents to meet records-management obligations.",
        "core_features": ["Document type classification", "Retention label assignment", "Sensitivity label assignment", "Human review queue for low-confidence items"],
        "target_users": ["Records managers", "Compliance officers"],
        "technologies": ["Python", "Microsoft Purview", "Fine-tuned classifier"],
        "status": "proof_of_concept", "created_days_ago": 130, "last_activity_days_ago": 21,
        "reusable_components": ["Document type taxonomy"],
        "notes": None,
    },
    {
        "id": "INIT-019", "name": "TestForge",
        "aliases": ["Automated Software Testing Platform"],
        "correlation_keys": ["testforge", "QE-145", "qe/testforge"],
        "department": "Developer Productivity", "team": "Quality Engineering", "owner": "Arjun Mehta",
        "description": "Platform that generates unit and regression tests with AI, detects flaky tests and reports test coverage across services.",
        "business_objective": "Increase automated test coverage and reduce escaped defects without slowing delivery.",
        "core_features": ["AI-generated unit tests", "Regression test generation", "Flaky test detection", "Coverage reporting"],
        "target_users": ["Software developers", "QA engineers"],
        "technologies": ["Java", "Python", "Internal LLM gateway", "Jenkins"],
        "status": "active_development", "created_days_ago": 240, "last_activity_days_ago": 5,
        "reusable_components": ["Test generation service", "Flaky test detector"],
        "notes": None,
    },
    {
        "id": "INIT-020", "name": "ModelHub Model Inventory",
        "aliases": ["ModelHub"],
        "correlation_keys": ["modelhub", "APP0006022"],
        "department": "Fraud & Risk", "team": "Model Risk Management", "owner": "Chloé Dubois",
        "description": "Inventory and governance workflow for analytical and AI models, tracking validation status, owners and model drift monitoring results.",
        "business_objective": "Maintain a complete model inventory and evidence of model validation for regulatory model risk requirements.",
        "core_features": ["Model inventory", "Validation workflow", "Drift monitoring results"],
        "target_users": ["Model risk officers", "Data scientists"],
        "technologies": ["ServiceNow", "Python"],
        "status": "deployed", "created_days_ago": 800, "last_activity_days_ago": 30,
        "reusable_components": ["Model inventory API"],
        "notes": None,
    },
    {
        "id": "INIT-021", "name": "Vendor Risk Questionnaire Automation",
        "aliases": ["VRQ Automation"],
        "correlation_keys": ["vrq-automation", "TPR-19"],
        "department": "Compliance", "team": "Third-Party Risk", "owner": "Liam O'Connell",
        "description": "Pre-fills third-party vendor risk questionnaires from previous assessments and flags gaps for analysts.",
        "business_objective": "Reduce the cycle time of third-party vendor risk assessments.",
        "core_features": ["Questionnaire pre-fill from prior answers", "Gap flagging"],
        "target_users": ["Third-party risk analysts"],
        "technologies": ["Python", "Internal LLM gateway"],
        "status": "paused", "created_days_ago": 380, "last_activity_days_ago": 205,
        "reusable_components": [],
        "notes": "Paused pending the procurement platform replacement.",
    },
    {
        "id": "INIT-022", "name": "Interview Scheduling Bot",
        "aliases": ["InterviewBot"],
        "correlation_keys": ["interview-bot", "APP0002210"],
        "department": "Human Resources Technology", "team": "Talent Acquisition Technology", "owner": "Ji-woo Park",
        "description": "Bot that scheduled candidate interviews by matching interviewer calendars. Retired after the recruiting platform introduced native scheduling.",
        "business_objective": "Reduce recruiter time spent scheduling interviews.",
        "core_features": ["Calendar matching", "Candidate self-scheduling links"],
        "target_users": ["Recruiters", "Candidates"],
        "technologies": ["Microsoft Graph API", "Python"],
        "status": "retired", "created_days_ago": 1200, "last_activity_days_ago": 290,
        "reusable_components": [],
        "notes": None,
    },
    {
        "id": "INIT-023", "name": "SpendScope Cloud Cost Advisor",
        "aliases": ["SpendScope"],
        "correlation_keys": ["spendscope", "FINOPS-58", "finops/spendscope"],
        "department": "Cloud Infrastructure", "team": "Cloud FinOps", "owner": "Mateo Rossi",
        "description": "Analyses cloud billing data to recommend rightsizing, reserved-instance purchases and idle resource clean-up.",
        "business_objective": "Reduce cloud spend through actionable cost optimisation recommendations.",
        "core_features": ["Rightsizing recommendations", "Idle resource detection", "Showback reports per business unit"],
        "target_users": ["Cloud engineers", "FinOps analysts"],
        "technologies": ["Python", "AWS Cost Explorer", "Azure Cost Management", "Power BI"],
        "status": "active_development", "created_days_ago": 190, "last_activity_days_ago": 10,
        "reusable_components": ["Billing data normaliser"],
        "notes": None,
    },
    {
        "id": "INIT-024", "name": "KeyKeeper Secrets Rotation",
        "aliases": ["KeyKeeper"],
        "correlation_keys": ["keykeeper", "APP0003876"],
        "department": "Cybersecurity Engineering", "team": "Identity & Cryptography", "owner": "Yusuf Demir",
        "description": "Central secrets vault service that stores application credentials and rotates database passwords and API keys automatically.",
        "business_objective": "Eliminate long-lived static credentials by centralising and automatically rotating secrets.",
        "core_features": ["Central secrets vault", "Automatic credential rotation", "Application SDKs"],
        "target_users": ["Software developers", "Platform engineers"],
        "technologies": ["HashiCorp Vault", "Kubernetes"],
        "status": "deployed", "created_days_ago": 950, "last_activity_days_ago": 15,
        "reusable_components": ["Vault SDK wrappers"],
        "notes": None,
    },
    {
        "id": "INIT-025", "name": "PhishGuard Awareness Programme",
        "aliases": ["PhishGuard"],
        "correlation_keys": ["phishguard", "APP0001988"],
        "department": "Cybersecurity Engineering", "team": "Security Awareness", "owner": "Fatima Zahra El Idrissi",
        "description": "Phishing simulation campaigns, a report-phish button and awareness training for all employees.",
        "business_objective": "Reduce successful phishing attacks by training employees to recognise and report phishing.",
        "core_features": ["Phishing simulation campaigns", "Report-phish button", "Targeted training"],
        "target_users": ["All employees"],
        "technologies": ["Vendor SaaS", "Microsoft 365"],
        "status": "deployed", "created_days_ago": 1000, "last_activity_days_ago": 18,
        "reusable_components": [],
        "notes": None,
    },
    {
        "id": "INIT-026", "name": "Complaint Insights",
        "aliases": ["Customer Complaint Insights"],
        "correlation_keys": ["complaint-insights", "CX-344"],
        "department": "Customer Experience", "team": "Customer Insights", "owner": "Henrik Sørensen",
        "description": "Uses NLP topic modelling on customer complaints to surface emerging themes and root causes in a weekly insights dashboard.",
        "business_objective": "Identify emerging customer complaint themes early so product teams can fix root causes.",
        "core_features": ["Complaint topic modelling", "Emerging theme alerts", "Weekly insights dashboard"],
        "target_users": ["Customer experience analysts", "Product owners"],
        "technologies": ["Python", "BERTopic", "Power BI"],
        "status": "active_development", "created_days_ago": 110, "last_activity_days_ago": 9,
        "reusable_components": ["Complaint taxonomy"],
        "notes": None,
    },
    {
        "id": "INIT-027", "name": "Branch Capacity Planner",
        "aliases": ["Branch Staffing Forecast"],
        "correlation_keys": ["branch-capacity", "OPS-77"],
        "department": "Operations", "team": "Retail Operations Planning", "owner": "Grace Achebe",
        "description": "Forecasts branch footfall to plan staffing rosters across the retail branch network.",
        "business_objective": "Match branch staffing to forecast customer demand.",
        "core_features": ["Footfall forecasting", "Roster recommendations"],
        "target_users": ["Branch managers", "Operations planners"],
        "technologies": ["Python", "Prophet", "Power BI"],
        "status": "proof_of_concept", "created_days_ago": 95, "last_activity_days_ago": 19,
        "reusable_components": [],
        "notes": None,
    },
]

# ---------------------------------------------------------------------------------------------
# Source records
# ---------------------------------------------------------------------------------------------
PUBLIC = {"visibility": "internal", "groups": ["all-employees"], "classification": "internal"}


def _acl(**kw) -> dict:
    return {**PUBLIC, **kw}


def conf(key, space, title, content, *, owner, status=None, days=10, created=None, labels=(), links=(), rtype="technical_proposal", acl=None):
    return {
        "id": f"confluence:{key}", "source": "confluence", "record_type": rtype, "external_key": key,
        "title": title, "content": content, "url": f"https://confluence.{DOMAIN}/display/{space}/{key}",
        "author": owner, "owner": owner, "source_status": status, "updated_days_ago": days,
        "created_days_ago": created or days + 40, "labels": list(labels), "links": list(links),
        "extra": {"space": space}, "acl": acl or _acl(),
    }


def jira(key, title, content, *, owner, status, days=5, created=None, labels=(), links=(), rtype="epic", extra=None):
    return {
        "id": f"jira:{key}", "source": "jira", "record_type": rtype, "external_key": key,
        "title": f"{key} — {title}", "content": content, "url": f"https://jira.{DOMAIN}/browse/{key}",
        "author": owner, "owner": owner, "source_status": status, "updated_days_ago": days,
        "created_days_ago": created or days + 60, "labels": list(labels), "links": list(links),
        "extra": {"issue_type": rtype.replace("_", " ").title(), "project": key.split("-")[0], **(extra or {})}, "acl": _acl(),
    }


def gh(repo, title, content, *, owner, days=5, created=None, labels=(), links=(), rtype="repository", archived=False, extra=None, number=None):
    key = repo if number is None else f"{repo}#{number}"
    url = f"https://github.{DOMAIN}/{repo}" + ("" if number is None else f"/pull/{number}")
    status = "archived" if archived else ("merged" if rtype == "pull_request" else "active")
    return {
        "id": f"github:{key}", "source": "github", "record_type": rtype, "external_key": key,
        "title": title, "content": content, "url": url, "author": owner, "owner": owner,
        "source_status": status, "updated_days_ago": days, "created_days_ago": created or days + 90,
        "labels": list(labels), "links": list(links), "extra": {"archived": archived, **(extra or {})}, "acl": _acl(),
    }


def sp(key, site, title, content, *, owner, days=30, created=None, labels=(), links=(), rtype="presentation", status=None):
    return {
        "id": f"sharepoint:{key}", "source": "sharepoint", "record_type": rtype, "external_key": key,
        "title": title, "content": content,
        "url": f"https://northbridge.sharepoint.{DOMAIN.split('.')[-1]}/sites/{site}/Shared%20Documents/{key}",
        "author": owner, "owner": owner, "source_status": status, "updated_days_ago": days,
        "created_days_ago": created or days + 20, "labels": list(labels), "links": list(links),
        "extra": {"site": site}, "acl": _acl(),
    }


def teams(key, channel, title, content, *, author, days=7, labels=(), links=()):
    return {
        "id": f"teams:{key}", "source": "teams", "record_type": "channel_post", "external_key": key,
        "title": title, "content": content, "url": f"https://teams.{DOMAIN}/l/channel/{channel}/post/{key}",
        "author": author, "owner": None, "source_status": None, "updated_days_ago": days, "created_days_ago": days,
        "labels": list(labels), "links": list(links), "extra": {"channel": channel, "channel_type": "standard-project-channel"},
        "acl": _acl(visibility="channel-members", groups=[f"channel:{channel}"], authorized_for_indexing=True),
    }


def snow(key, title, content, *, owner, status, days=10, created=None, labels=(), links=(), rtype="catalog_item", extra=None):
    table = {"catalog_item": "sc_cat_item", "application": "cmdb_ci_appl", "kb_article": "kb_knowledge", "change_record": "change_request"}[rtype]
    return {
        "id": f"servicenow:{key}", "source": "servicenow", "record_type": rtype, "external_key": key,
        "title": title, "content": content, "url": f"https://northbridge.service-now.example/{table}.do?number={key}",
        "author": owner, "owner": owner, "source_status": status, "updated_days_ago": days,
        "created_days_ago": created or days + 200, "labels": list(labels), "links": list(links),
        "extra": extra or {}, "acl": _acl(),
    }


PR = "Priya Raman"
MO = "Marcus Oyelaran"

RECORDS: list[dict] = [
    # ============================================================ INIT-001 SecureGuard AI (Case A)
    conf("APPSEC-1042", "APPSEC", "SecureGuard AI — Architecture Proposal",
         "Status: Approved. SecureGuard AI is an AI-assisted application security scanner for internal GitHub Enterprise repositories. "
         "It runs static application security testing (Semgrep and CodeQL), software composition analysis of dependencies and hardcoded secret detection "
         "in CI via GitHub Actions. Findings are de-duplicated, triaged by severity and enriched by the internal LLM gateway, which proposes a concrete fix "
         "that is posted as a pull request comment for developers. Development is tracked in Jira epic SEC-284; code lives in northbridge-appsec/secureguard-scanner. "
         "Target users: software developers and the application security team.",
         owner=PR, status="Approved", days=20, created=290, labels=["secureguard", "appsec", "architecture"], links=["SEC-284", "northbridge-appsec/secureguard-scanner"], rtype="architecture_doc"),
    conf("APPSEC-1077", "APPSEC", "SecureGuard AI — Pilot Findings (Payments & Lending repositories)",
         "Status: Pilot in progress. Over 10 weeks SecureGuard scanned 140 repositories and raised 2,318 findings; 61% of LLM-suggested fixes were accepted by developers "
         "without modification. False-positive rate for SAST findings after triage rules: 14%. Next: expand to Wealth and Corporate Banking repositories. "
         "Reusable components: Semgrep rule pack for internal frameworks, remediation prompt library, PR comment GitHub App.",
         owner=PR, status="Pilot", days=35, created=60, labels=["secureguard", "poc-findings"], links=["CONF:APPSEC-1042"], rtype="poc_findings"),
    jira("SEC-284", "Automated Vulnerability Scanner (SecureGuard AI)",
         "Epic: build an automated vulnerability scanner for internal repositories with SAST, dependency scanning, secret detection and AI-generated remediation recommendations "
         "delivered as PR comments. Architecture: APPSEC-1042. Repo: northbridge-appsec/secureguard-scanner.",
         owner=PR, status="In Progress", days=4, created=280, labels=["secureguard"], links=["APPSEC-1042", "northbridge-appsec/secureguard-scanner"],
         extra={"children": ["SEC-301", "SEC-317", "SEC-322"], "story_points_done": 89, "story_points_total": 140, "assignee": PR}),
    jira("SEC-317", "LLM-generated fix suggestions as pull request comments",
         "Story: use the internal LLM gateway to generate a suggested fix for each high or critical finding and post it as a review comment on the pull request.",
         owner=MO, status="In Progress", days=4, created=70, labels=["secureguard"], links=["SEC-284"], rtype="story", extra={"parent": "SEC-284", "assignee": MO}),
    jira("SEC-322", "Dependency (SCA) scanning for Maven and npm",
         "Story: add software composition analysis to flag vulnerable open source packages (CVE matching) for Maven and npm projects.",
         owner=MO, status="Done", days=18, created=90, labels=["secureguard"], links=["SEC-284"], rtype="story", extra={"parent": "SEC-284", "assignee": MO}),
    gh("northbridge-appsec/secureguard-scanner", "secureguard-scanner",
       "README: SecureGuard AI scanner. Scans repositories for vulnerabilities using Semgrep, CodeQL and dependency (SCA) checks, detects hardcoded secrets, "
       "and uses the internal LLM gateway to recommend fixes as pull request comments. Runs as a GitHub Action. Jira: SEC-284. Maintainers: Priya Raman, Marcus Oyelaran.",
       owner=PR, days=3, created=270, labels=["secureguard", "sast", "appsec", "python"], links=["SEC-284"],
       extra={"language": "Python", "stars": 41, "open_pull_requests": 6, "contributors": 9, "commits_last_30_days": 57, "maintainers": [PR, MO]}),
    gh("northbridge-appsec/secureguard-scanner", "Add remediation prompt templates for Java Spring",
       "Pull request: adds remediation prompt templates so the LLM recommends idiomatic fixes for Spring SQL injection and deserialization findings.",
       owner=MO, days=6, rtype="pull_request", number=212, labels=["secureguard"], links=["SEC-317"], extra={"state": "merged"}),
    sp("SP-SECENG-031", "SecurityEngineering", "Application Security Automation PoC — Steering Committee Update",
       "Slides: Business case for automated application security scanning. Problem: manual code security reviews do not scale to 2,000 developers. "
       "Solution: SecureGuard AI (Jira SEC-284) scans every pull request and recommends fixes. Pilot results and roadmap for firm-wide rollout.",
       owner=PR, days=60, rtype="business_case"),
    teams("appsec-guild-0091", "appsec-guild", "SecureGuard AI is now scanning 140 repositories",
          "Announcement from Priya Raman: SecureGuard AI is live for the Payments and Lending pilot. If your team wants automated vulnerability scanning and fix "
          "suggestions on your repos, reach out — onboarding guide is in the secureguard-scanner repo.",
          author=PR, days=9),
    # Unlinked: hackathon chatter that may indicate further related work (not correlated to any initiative)
    teams("ai-community-0412", "ai-community", "Hackathon: scanning repos for vulnerable dependencies",
          "Our hackathon team hacked together a script that checks repositories for vulnerable npm dependencies and opens a ticket. Not sure if anyone else is doing this?",
          author="Leo Martins", days=48),

    # ============================================================ INIT-002 Cloud Watchtower (Case G distractor)
    jira("CLDSEC-88", "Cloud Configuration Security Monitor",
         "Epic: continuously check AWS accounts and Azure subscriptions for misconfigurations — public storage buckets, overly permissive IAM roles, open security groups, "
         "unencrypted volumes — and notify resource owners. Policy-as-code with Open Policy Agent. Repo cloud-platform/watchtower-rules.",
         owner="Daniel Okafor", status="In Progress", days=11, created=200, labels=["cloud-watchtower"], links=["cloud-platform/watchtower-rules"]),
    gh("cloud-platform/watchtower-rules", "watchtower-rules",
       "README: Cloud Watchtower policy-as-code rules for cloud security posture management (CSPM) across AWS and Azure. Detects misconfiguration and Terraform drift. Jira CLDSEC-88.",
       owner="Daniel Okafor", days=11, created=190, labels=["cloud-watchtower", "cspm", "terraform"], links=["CLDSEC-88"],
       extra={"language": "Rego", "stars": 17, "commits_last_30_days": 22, "maintainers": ["Daniel Okafor"]}),
    conf("CLOUD-310", "CLOUD", "Cloud Watchtower — Design",
         "Status: In development. Cloud security posture monitoring for the AWS landing zone and Azure subscriptions. Out of scope: application code scanning (see AppSec).",
         owner="Daniel Okafor", status="In development", days=40, labels=["cloud-watchtower"], links=["CLDSEC-88"]),

    # ============================================================ INIT-003 CaseLens (Case B)
    conf("FRAUD-221", "FRAUDOPS", "CaseLens — Fraud Investigation Assistant PoC Scope",
         "Status: Proof of concept. CaseLens is a generative AI assistant for fraud investigators. It summarises case evidence, prioritises the alert queue and drafts "
         "suspicious activity report (SAR) narratives. Input: alerts already generated by the transaction monitoring rules engine. "
         "Out of scope: real-time transaction scoring, blocking or declining payments — CaseLens works after an alert is raised, during investigation. Jira: FRD-142.",
         owner="Elena Vasquez-Hart", status="Proof of concept", days=15, created=140, labels=["caselens", "fraud"], links=["FRD-142"]),
    jira("FRD-142", "Fraud Investigation Assistant (CaseLens) PoC",
         "Epic: deliver a PoC of an investigator assistant for case triage, case summarisation and SAR narrative drafting for the Card Fraud investigations team.",
         owner="Elena Vasquez-Hart", status="In Progress", days=8, created=130, labels=["caselens", "poc"], links=["FRAUD-221"],
         extra={"assignee": "Elena Vasquez-Hart", "story_points_done": 34, "story_points_total": 60}),
    sp("SP-FRAUD-014", "FraudRisk", "CaseLens Business Case — Investigator Productivity",
       "Business case: investigators spend 45% of their time assembling case files. CaseLens (FRD-142) targets a 30% reduction in average handling time per case.",
       owner="Elena Vasquez-Hart", days=70, rtype="business_case"),
    teams("fraud-ops-0233", "fraud-ops-analytics", "CaseLens pilot with Card Fraud investigators",
          "CaseLens pilot starts next sprint with 12 Card Fraud investigators — focus is case triage and summaries. Contact Elena Vasquez-Hart to join.",
          author="Elena Vasquez-Hart", days=8),

    # ============================================================ INIT-004 MuleNet
    conf("FCA-12", "FINCRIME", "MuleNet — Research Plan: Mule Account Network Analytics",
         "Status: Research. Weekly batch graph analytics on historical transfers to identify money mule account networks using community detection in Neo4j. "
         "No real-time component. Jira FCA-38.",
         owner="Oluwaseun Adeyemi", status="Research", days=26, labels=["mulenet"], links=["FCA-38"], rtype="research_report"),
    jira("FCA-38", "Mule account network analytics research",
         "Epic: research graph-based detection of mule account networks from historical transfer data (batch).",
         owner="Oluwaseun Adeyemi", status="Research", days=30, labels=["mulenet"], links=["FCA-12"]),

    # ============================================================ INIT-005 DocuMind (Case D — abandoned)
    conf("LEGALTECH-88", "LEGALTECH", "DocuMind — PoC Findings and Decision to Stop",
         "Status: Stopped. DocuMind extracted termination, indemnity and renewal date clauses from vendor contracts using OCR and NLP. "
         "Accuracy on scanned contracts reached 71% against a 90% target. The steering group decided not to fund production. "
         "Reusable: annotated dataset of 420 vendor contracts and the OCR pre-processing pipeline (legaltech/documind). Jira LGL-57.",
         owner="Samuel Achterberg", status="Stopped", days=430, created=700, labels=["documind", "contracts"], links=["LGL-57", "legaltech/documind"], rtype="poc_findings"),
    jira("LGL-57", "Contract clause extraction PoC (DocuMind)",
         "Epic: extract key clauses and renewal dates from vendor contracts into a contract register.",
         owner="Samuel Achterberg", status="Won't Do", days=432, created=690, labels=["documind"], links=["legaltech/documind"]),
    gh("legaltech/documind", "documind",
       "README (archived): DocuMind contract clause extractor. OCR + spaCy pipeline to extract clauses and obligations from vendor agreements. This repository is archived.",
       owner="Samuel Achterberg", days=440, created=680, labels=["documind", "nlp", "contracts"], links=["LGL-57"], archived=True,
       extra={"language": "Python", "stars": 6, "commits_last_30_days": 0, "maintainers": ["Samuel Achterberg"]}),

    # ============================================================ INIT-006 AccessFlow (Case E — deployed)
    snow("APP0004417", "AccessFlow — Request Application Access",
         "Service catalogue item (Operational). Employees request access to applications and roles. Requests are routed automatically to the line manager and the "
         "application owner for approval and provisioned automatically for 300+ integrated applications. Low-risk roles are auto-approved. ~18,000 requests per month.",
         owner="Grace Liu", status="Operational", days=6, created=880, labels=["accessflow"], rtype="catalog_item",
         extra={"service_owner": "Grace Liu", "support_group": "IAM Operations", "monthly_requests": 18000, "lifecycle": "Operational"}),
    snow("KB0012873", "How to request system access using AccessFlow",
         "Knowledge article: To request access to an application, open the AccessFlow catalogue item, select the application and role, and submit. "
         "Your manager approves automatically via email or Teams. Do not email the service desk for access requests.",
         owner="Grace Liu", status="Published", days=45, labels=["accessflow"], links=["APP0004417"], rtype="kb_article"),
    snow("CHG0039921", "AccessFlow release 3.4 — auto-approval for low-risk roles",
         "Change record (Closed - Successful): deploy AccessFlow 3.4 adding automatic approval for low-risk roles and provisioning connectors for 25 additional applications.",
         owner="Grace Liu", status="Closed - Successful", days=12, labels=["accessflow"], links=["APP0004417"], rtype="change_record"),
    conf("IAM-501", "IAM", "AccessFlow Service Overview",
         "Status: Live. AccessFlow is the firm-wide self-service access request and provisioning service built on ServiceNow and SailPoint. Owner: Grace Liu (IAM).",
         owner="Grace Liu", status="Live", days=80, labels=["accessflow"], links=["APP0004417"]),
    conf("MA-INTEG-7", "MA-INTEGRATION", "Identity platform consolidation — integration plan (Restricted)",
         "Restricted: identity and access request platform consolidation plan for a confidential integration programme.",
         owner="Grace Liu", status="Draft", days=25, labels=["restricted"], rtype="technical_proposal",
         acl={"visibility": "restricted", "groups": ["ma-integration-core"], "classification": "restricted"}),

    # ============================================================ INIT-007 Pipeline Sentinel (Case F/G)
    jira("DATA-412", "Pipeline Sentinel — data observability for warehouse pipelines",
         "Epic: automated data quality checks (freshness, volume, schema drift, null rate) on dbt and Airflow pipelines feeding the Snowflake warehouse; alert data owners "
         "before downstream reports are refreshed.",
         owner="Tomasz Wierzbicki", status="In Progress", days=5, created=250, labels=["pipeline-sentinel"], links=["data-platform/pipeline-sentinel"]),
    gh("data-platform/pipeline-sentinel", "pipeline-sentinel",
       "README: Pipeline Sentinel — data observability. Great Expectations checks, freshness/late-arrival detection, volume anomaly detection and schema drift alerts for "
       "warehouse feeds. Jira DATA-412.",
       owner="Tomasz Wierzbicki", days=5, created=240, labels=["pipeline-sentinel", "data-quality", "dbt"], links=["DATA-412"],
       extra={"language": "Python", "stars": 23, "commits_last_30_days": 31, "maintainers": ["Tomasz Wierzbicki"]}),
    conf("DATAPLAT-77", "DATAPLAT", "Pipeline Sentinel — Data Quality Check Catalogue",
         "Status: In development. Catalogue of data quality rules: freshness SLAs per feed, completeness and row-count checks, null spikes, schema change detection.",
         owner="Tomasz Wierzbicki", status="In development", days=22, labels=["pipeline-sentinel"], links=["DATA-412"]),

    # ============================================================ INIT-008 Trustworthy Data Initiative (Case F)
    sp("SP-OPS-102", "OperationsControl", "Trustworthy Data Initiative — Problem Statement",
       "Operations reporting repeatedly publishes figures that later turn out to be wrong because an upstream feed arrived late or incomplete. "
       "We want to make sure the numbers in our daily operations and regulatory reports can be trusted: check that every feed has arrived and is complete, "
       "reconcile totals between systems and stop publication when figures do not tie out.",
       owner="Aisha Bello", days=14, created=90, labels=["trustworthy-data"], rtype="innovation_proposal", status="Research"),
    teams("ops-control-0057", "ops-control-reporting", "Trustworthy Data Initiative — looking for volunteers",
          "Aisha Bello: we are scoping the Trustworthy Data Initiative to stop late feeds and reconciliation breaks reaching our morning reports. Join the working group.",
          author="Aisha Bello", days=16, labels=["trustworthy-data"]),

    # ============================================================ INIT-009 ReviewPilot (Case G)
    gh("devex/reviewpilot", "reviewpilot",
       "README: ReviewPilot — AI pull request reviewer. Summarises pull requests and suggests improvements for readability, maintainability, likely bugs and missing tests. "
       "Security scanning is out of scope (see SecureGuard). Jira DEVX-219.",
       owner="Hannah Kowalczyk", days=12, created=130, labels=["reviewpilot", "code-review"], links=["DEVX-219"],
       extra={"language": "TypeScript", "stars": 28, "commits_last_30_days": 14, "maintainers": ["Hannah Kowalczyk"]}),
    jira("DEVX-219", "ReviewPilot AI code review PoC",
         "Epic: PoC of an AI code review assistant that gives developers a first-pass review on every pull request to shorten review cycle time.",
         owner="Hannah Kowalczyk", status="In Progress", days=12, labels=["reviewpilot"], links=["devex/reviewpilot"]),
    conf("DEVX-40", "DEVX", "ReviewPilot — PoC Proposal",
         "Status: Proof of concept. Developer productivity: reduce pull request review wait time with an AI first-pass code reviewer.",
         owner="Hannah Kowalczyk", status="Proof of concept", days=50, labels=["reviewpilot"], links=["DEVX-219"]),

    # ============================================================ INIT-010 Secure Code Review Board (Case G)
    conf("TRC-15", "TECHRISK", "Secure Code Review Board — Charter and Checklist",
         "Status: Active process. The Secure Code Review Board is a governance committee that manually reviews high-risk application changes, signs off against the "
         "secure change checklist and records attestations and policy exceptions for audit. Book via ServiceNow KB0019034.",
         owner="Victor Hallström", status="Active", days=20, created=1100, labels=["scrb", "governance"], links=["KB0019034"]),
    snow("KB0019034", "How to book a Secure Code Review Board session",
         "Knowledge article: high-risk changes require a Secure Code Review Board sign-off. Submit the checklist and attestation form at least 5 days before the change advisory meeting.",
         owner="Victor Hallström", status="Published", days=60, labels=["scrb"], rtype="kb_article"),

    # ============================================================ INIT-011 GenBI
    conf("AILAB-120", "AILAB", "GenBI Insights — Generative BI Analytics Platform",
         "Status: Proof of concept. Business users ask questions in natural language; the assistant generates SQL against the governed semantic layer and returns charts. Jira AIL-77.",
         owner="Rafael Mendes", status="Proof of concept", days=9, labels=["genbi"], links=["AIL-77", "ai-lab/genbi-insights"]),
    jira("AIL-77", "GenBI text-to-SQL PoC", "Epic: natural language to SQL assistant with chart generation for self-service analytics.",
         owner="Rafael Mendes", status="In Progress", days=9, labels=["genbi"], links=["ai-lab/genbi-insights"]),
    gh("ai-lab/genbi-insights", "genbi-insights", "README: GenBI Insights — text-to-SQL and automatic chart generation over Snowflake. Jira AIL-77.",
       owner="Rafael Mendes", days=9, labels=["genbi", "text-to-sql"], links=["AIL-77"], extra={"language": "Python", "stars": 19, "commits_last_30_days": 18}),
    sp("SP-AILAB-009", "AIInnovation", "GenBI — Executive Demo Deck", "Slides: conversational analytics for business leaders; roadmap to production via the data platform.",
       owner="Rafael Mendes", days=40, labels=["genbi"]),

    # ============================================================ INIT-012 Onboarding Buddy
    jira("HRT-130", "Onboarding Buddy — new hire onboarding agent",
         "Epic: Teams-based agent that answers new hire HR policy questions, tracks onboarding tasks for the first 30 days and triggers laptop and account provisioning requests.",
         owner="Nadia Rahman", status="In Progress", days=7, labels=["onboarding-buddy"]),
    conf("PEOPLETECH-31", "PEOPLETECH", "Onboarding Buddy — Solution Design",
         "Status: In development. Conversational onboarding assistant for new joiners and hiring managers. Integrates with Workday and ServiceNow. Jira HRT-130.",
         owner="Nadia Rahman", status="In development", days=30, labels=["onboarding-buddy"], links=["HRT-130"]),
    teams("people-tech-0140", "people-technology", "Onboarding Buddy beta for October joiners",
          "Nadia Rahman: Onboarding Buddy beta will support all October new hires in Technology. Feedback welcome.", author="Nadia Rahman", days=7, labels=["onboarding-buddy"]),

    # ============================================================ INIT-013 OpsSleuth
    gh("sre/opssleuth", "opssleuth",
       "README: OpsSleuth incident investigation agent. Correlates alerts, logs and recent ServiceNow change records to suggest probable root cause and drafts incident timelines. Jira SRE-501.",
       owner="Kenji Watanabe", days=16, labels=["opssleuth", "incident"], links=["SRE-501"], extra={"language": "Python", "stars": 15, "commits_last_30_days": 9}),
    jira("SRE-501", "OpsSleuth incident investigation PoC", "Epic: reduce MTTR by automating root cause analysis and postmortem drafting.",
         owner="Kenji Watanabe", status="In Progress", days=16, labels=["opssleuth"], links=["sre/opssleuth"]),
    conf("SRE-88", "SRE", "OpsSleuth — PoC Results", "Status: Proof of concept. In 14 replayed major incidents OpsSleuth ranked the true root cause in its top 3 suggestions 9 times.",
         owner="Kenji Watanabe", status="Proof of concept", days=24, labels=["opssleuth"], links=["SRE-501"], rtype="poc_findings"),
    teams("sre-0301", "sre-community", "OpsSleuth demo on Thursday", "Kenji Watanabe: demo of OpsSleuth incident root cause suggestions on Thursday's SRE call.",
          author="Kenji Watanabe", days=18, labels=["opssleuth"]),

    # ============================================================ INIT-014 AskNorthbridge
    snow("APP0005120", "AskNorthbridge Knowledge Assistant",
         "Application (Operational): retrieval-augmented assistant answering employee questions from intranet policies, Confluence and SharePoint with citations.",
         owner="Olivia Brennan", status="Operational", days=10, labels=["asknorthbridge"], rtype="application",
         extra={"service_owner": "Olivia Brennan", "lifecycle": "Operational", "users": 21000}),
    conf("DW-210", "DIGITALWORKPLACE", "AskNorthbridge — Architecture", "Status: Live. Permission-aware retrieval over the intranet; LLM answers with citations.",
         owner="Olivia Brennan", status="Live", days=55, labels=["asknorthbridge"], links=["APP0005120"], rtype="architecture_doc"),
    sp("SP-DW-044", "DigitalWorkplace", "AskNorthbridge Adoption Report", "Adoption: 21,000 monthly users; 38% fewer policy-related service desk tickets.",
       owner="Olivia Brennan", days=25, labels=["asknorthbridge"], rtype="research_findings"),

    # ============================================================ INIT-015 ControlScribe
    jira("CMP-66", "ControlScribe — compliance documentation automation",
         "Epic: draft control narratives and assemble audit evidence packs automatically from Jira, ServiceNow change records and system reports.",
         owner="Marta Silva", status="In Progress", days=13, labels=["controlscribe"]),
    conf("COMPENG-19", "COMPENG", "ControlScribe — Proposal", "Status: In development. Automates control documentation and audit evidence collection for SOX controls. Jira CMP-66.",
         owner="Marta Silva", status="In development", days=45, labels=["controlscribe"], links=["CMP-66"]),
    sp("SP-COMP-071", "Compliance", "ControlScribe — Audit Readiness Pilot", "Pilot with 40 SOX controls; evidence pack preparation time reduced from 6 hours to 1.5 hours.",
       owner="Marta Silva", days=33, labels=["controlscribe"], rtype="research_findings"),

    # ============================================================ INIT-016 API Sentinel (Case G name clash)
    snow("APP0003301", "API Sentinel — API Health Monitoring",
         "Application (Operational): synthetic monitoring for internal and partner APIs; latency and error-rate tracking, SLA dashboards and on-call alerting.",
         owner="Benedikt Krause", status="Operational", days=4, labels=["api-sentinel"], rtype="application", extra={"service_owner": "Benedikt Krause", "lifecycle": "Operational"}),
    gh("platform/api-sentinel", "api-sentinel", "README: API Sentinel synthetic check runner. Monitors API endpoints, latency, 5xx error rate and SLA breaches.",
       owner="Benedikt Krause", days=4, labels=["api-sentinel", "monitoring"], links=["APP0003301"], extra={"language": "Go", "stars": 33, "commits_last_30_days": 12}),
    conf("APIPLAT-12", "APIPLAT", "API Sentinel — Runbook", "Status: Live. How to add synthetic checks for a new API and configure SLA alerts.",
         owner="Benedikt Krause", status="Live", days=70, labels=["api-sentinel"], links=["APP0003301"], rtype="project_documentation"),

    # ============================================================ INIT-017 SmartRoute
    jira("CX-310", "SmartRoute — intelligent contact routing",
         "Epic: classify customer email and chat intent and route to the right contact-centre queue and agent skill group.",
         owner="Isabel Ferreira", status="In Progress", days=6, labels=["smartroute"], links=["cx-tech/smartroute"]),
    gh("cx-tech/smartroute", "smartroute", "README: SmartRoute intent classifier and skill-based routing service for customer inquiries. Jira CX-310.",
       owner="Isabel Ferreira", days=6, labels=["smartroute"], links=["CX-310"], extra={"language": "Python", "stars": 12, "commits_last_30_days": 20}),
    conf("CXT-55", "CXTECH", "SmartRoute — Customer Service Routing Assistant Design", "Status: In development. Intent taxonomy, routing rules and agent assignment.",
         owner="Isabel Ferreira", status="In development", days=28, labels=["smartroute"], links=["CX-310"]),

    # ============================================================ INIT-018 LabelSmart
    sp("SP-RIM-005", "RecordsManagement", "LabelSmart — Document Classification PoC Proposal",
       "Innovation proposal: automatically classify unstructured documents and apply retention and sensitivity labels in SharePoint. Jira RIM-24.",
       owner="Thandiwe Mokoena", days=21, labels=["labelsmart"], links=["RIM-24"], rtype="innovation_proposal", status="Proof of concept"),
    jira("RIM-24", "LabelSmart document classification PoC", "Epic: document type classification with retention label assignment and human review queue.",
         owner="Thandiwe Mokoena", status="In Progress", days=21, labels=["labelsmart"]),

    # ============================================================ INIT-019 TestForge
    gh("qe/testforge", "testforge", "README: TestForge — AI unit and regression test generation, flaky test detection and coverage reporting. Jira QE-145.",
       owner="Arjun Mehta", days=5, labels=["testforge", "testing"], links=["QE-145"], extra={"language": "Java", "stars": 37, "commits_last_30_days": 44}),
    jira("QE-145", "TestForge automated testing platform", "Epic: generate unit tests with AI and detect flaky tests across CI pipelines.",
         owner="Arjun Mehta", status="In Progress", days=5, labels=["testforge"], links=["qe/testforge"]),
    conf("QE-20", "QE", "TestForge — Roadmap", "Status: In development. Roadmap for AI test generation and regression test selection.",
         owner="Arjun Mehta", status="In development", days=35, labels=["testforge"], links=["QE-145"], rtype="roadmap"),
    teams("qe-guild-0210", "quality-engineering", "TestForge now generates JUnit tests", "Arjun Mehta: TestForge can now generate JUnit tests for Spring services. Try it!",
          author="Arjun Mehta", days=6, labels=["testforge"]),

    # ============================================================ INIT-020 ModelHub
    snow("APP0006022", "ModelHub — Model Inventory", "Application (Operational): inventory of analytical and AI models with validation workflow and drift monitoring results.",
         owner="Chloé Dubois", status="Operational", days=30, labels=["modelhub"], rtype="application", extra={"service_owner": "Chloé Dubois", "lifecycle": "Operational"}),
    conf("MRM-5", "MRM", "ModelHub — Model Risk Inventory Guide", "Status: Live. How to register a model and submit it for validation.",
         owner="Chloé Dubois", status="Live", days=90, labels=["modelhub"], links=["APP0006022"], rtype="project_documentation"),

    # ============================================================ INIT-021 Vendor risk (paused)
    jira("TPR-19", "Vendor risk questionnaire automation", "Epic: pre-fill third-party risk questionnaires from prior assessments. On hold pending procurement platform replacement.",
         owner="Liam O'Connell", status="On Hold", days=205, labels=["vrq-automation"]),
    sp("SP-TPR-003", "ThirdPartyRisk", "Vendor Risk Questionnaire Automation — Business Case", "Business case for automating third-party vendor risk assessments.",
       owner="Liam O'Connell", days=260, labels=["vrq-automation"], rtype="business_case"),

    # ============================================================ INIT-022 Interview bot (retired)
    snow("APP0002210", "Interview Scheduling Bot", "Application (Retired): scheduled candidate interviews. Retired after the recruiting platform introduced native scheduling.",
         owner="Ji-woo Park", status="Retired", days=290, labels=["interview-bot"], rtype="application", extra={"lifecycle": "Retired"}),

    # ============================================================ INIT-023 SpendScope
    gh("finops/spendscope", "spendscope", "README: SpendScope cloud cost advisor — rightsizing and idle resource recommendations from billing data. Jira FINOPS-58.",
       owner="Mateo Rossi", days=10, labels=["spendscope", "finops"], links=["FINOPS-58"], extra={"language": "Python", "stars": 9, "commits_last_30_days": 15}),
    jira("FINOPS-58", "SpendScope cloud cost optimisation", "Epic: cost optimisation recommendations and showback reports per business unit.",
         owner="Mateo Rossi", status="In Progress", days=10, labels=["spendscope"], links=["finops/spendscope"]),

    # ============================================================ INIT-024 KeyKeeper
    snow("APP0003876", "KeyKeeper Secrets Vault", "Application (Operational): central secrets vault with automatic rotation of database passwords and API keys.",
         owner="Yusuf Demir", status="Operational", days=15, labels=["keykeeper"], rtype="application", extra={"service_owner": "Yusuf Demir", "lifecycle": "Operational"}),
    conf("CRYPTO-8", "CRYPTO", "KeyKeeper — Onboarding Guide", "Status: Live. How applications retrieve secrets from KeyKeeper and enable automatic rotation.",
         owner="Yusuf Demir", status="Live", days=100, labels=["keykeeper"], links=["APP0003876"], rtype="project_documentation"),

    # ============================================================ INIT-025 PhishGuard
    snow("APP0001988", "PhishGuard Awareness Programme", "Application (Operational): phishing simulation campaigns, report-phish button and awareness training for all employees.",
         owner="Fatima Zahra El Idrissi", status="Operational", days=18, labels=["phishguard"], rtype="application", extra={"lifecycle": "Operational"}),
    sp("SP-SECAW-021", "SecurityAwareness", "PhishGuard — Annual Results", "Click rate on simulated phishing fell from 11% to 4%; reporting rate rose to 63%.",
       owner="Fatima Zahra El Idrissi", days=50, labels=["phishguard"], rtype="research_findings"),

    # ============================================================ INIT-026 Complaint Insights
    conf("CXI-14", "CXINSIGHTS", "Complaint Insights — Approach", "Status: In development. Topic modelling of customer complaints with BERTopic; weekly emerging-theme dashboard. Jira CX-344.",
         owner="Henrik Sørensen", status="In development", days=9, labels=["complaint-insights"], links=["CX-344"]),
    jira("CX-344", "Complaint Insights topic modelling", "Epic: surface emerging complaint themes for product teams.",
         owner="Henrik Sørensen", status="In Progress", days=9, labels=["complaint-insights"]),

    # ============================================================ INIT-027 Branch capacity
    jira("OPS-77", "Branch capacity planner PoC", "Epic: forecast branch footfall to recommend staffing rosters.",
         owner="Grace Achebe", status="In Progress", days=19, labels=["branch-capacity"]),
]

# ---------------------------------------------------------------------------------------------
# Ideas previously registered through the application (Idea Registry)
# ---------------------------------------------------------------------------------------------
SEED_IDEAS: list[dict] = [
    {"id": "IDEA-0001", "title": "LLM pull request security reviewer",
     "description": "Use an LLM to review pull requests for security issues such as injection flaws and insecure configuration, and suggest fixes before merge.",
     "department": "Developer Productivity", "team": "Platform Tooling", "submitted_by": "Ravi Shankar", "status": "under_review",
     "related_initiative_ids": ["INIT-001", "INIT-009"], "days_ago": 25},
    {"id": "IDEA-0002", "title": "Service desk password reset chatbot",
     "description": "Chatbot in Teams that lets employees reset their own passwords and unlock accounts without calling the service desk.",
     "department": "Operations", "team": "IT Service Desk", "submitted_by": "Clara Nwosu", "status": "registered",
     "related_initiative_ids": [], "days_ago": 40},
    {"id": "IDEA-0003", "title": "Automated meeting notes for steering committees",
     "description": "Generate minutes and action items from steering committee meeting transcripts and file them in Confluence.",
     "department": "AI Innovation", "team": "AI Innovation Lab", "submitted_by": "Rafael Mendes", "status": "registered",
     "related_initiative_ids": [], "days_ago": 15},
    {"id": "IDEA-0004", "title": "Synthetic test data generator",
     "description": "Generate realistic synthetic test data for non-production environments so teams stop copying production data into test.",
     "department": "Developer Productivity", "team": "Quality Engineering", "submitted_by": "Arjun Mehta", "status": "registered",
     "related_initiative_ids": ["INIT-019"], "days_ago": 33},
]

# ---------------------------------------------------------------------------------------------
# Demo scenarios (used by the Demo page; results are produced live by the real pipeline)
# ---------------------------------------------------------------------------------------------
DEMO_SCENARIOS: list[dict] = [
    {"id": "strong-duplicate", "case": "A", "title": "Strong duplicate detection",
     "summary": "An AI cybersecurity checker turns out to overlap with SecureGuard AI, already in active development.",
     "idea": {"title": "AI cybersecurity checker",
              "description": "We want to build an AI-powered cybersecurity checker that scans internal repositories for vulnerabilities and recommends fixes.",
              "department": "Enterprise Technology"},
     "expected": {"top_match": "SecureGuard AI", "category": "strong_overlap_or_higher"}},
    {"id": "partial-overlap", "case": "B", "title": "Partial overlap",
     "summary": "Real-time fraud detection vs an existing fraud investigation assistant focused on case triage.",
     "idea": {"title": "Real-time AI fraud detection",
              "description": "Build an AI fraud detection system that scores card transactions in real time and blocks suspicious payments before they settle.",
              "target_users": "Fraud operations, card customers", "technologies": "Machine learning, Kafka"},
     "expected": {"matches_include": ["CaseLens Fraud Investigation Assistant"], "category": "partial_overlap", "not_duplicate": ["CaseLens Fraud Investigation Assistant"]}},
    {"id": "no-match", "case": "C", "title": "No significant match",
     "summary": "A sustainability idea that isn't in any connected source, so the agent offers registration.",
     "idea": {"title": "Business travel carbon tracker",
              "description": "An app that calculates the carbon footprint of employee business travel and suggests lower-emission alternatives when people book flights and hotels.",
              "department": "Operations"},
     "expected": {"top_match": None, "category": "no_significant_match"}},
    {"id": "abandoned", "case": "D", "title": "Abandoned initiative",
     "summary": "Contract clause extraction was tried before (DocuMind) and stopped more than a year ago.",
     "idea": {"title": "Contract clause extraction",
              "description": "An AI tool that reads our vendor contracts and pulls out renewal dates, termination clauses and key obligations into a register for the legal team."},
     "expected": {"top_match": "DocuMind Contract Clause Extractor", "category": "strong_overlap_or_higher", "lifecycle": "abandoned"}},
    {"id": "deployed", "case": "E", "title": "Already deployed solution",
     "summary": "Access request automation already exists as AccessFlow in the ServiceNow catalogue.",
     "idea": {"title": "Automated access requests",
              "description": "Automate internal access requests so employees can request system access themselves and get manager approval automatically instead of emailing IT."},
     "expected": {"top_match": "AccessFlow", "category": "strong_overlap_or_higher", "lifecycle": "deployed"}},
    {"id": "different-terminology", "case": "F", "title": "Different names, same objective",
     "summary": "An idea written in operations language still matches the data-engineering team's Pipeline Sentinel.",
     "idea": {"title": "Morning report checks",
              "description": "Our operations team keeps discovering too late that numbers in the morning reports are wrong because a source file arrived late or half empty. We want something that automatically checks the feeds and warns us before the reports go out."},
     "expected": {"top_match": "Pipeline Sentinel", "matches_include": ["Trustworthy Data Initiative"], "category": "strong_overlap_or_higher"}},
    {"id": "similar-keywords", "case": "G", "title": "Similar keywords, different problem",
     "summary": "An AI code review idea shares keywords with the Secure Code Review Board, but the board is a governance process and should not be flagged as a duplicate.",
     "idea": {"title": "AI code review assistant",
              "description": "An AI assistant that reviews pull requests and suggests improvements to readability, maintainability and likely bugs so developers get faster code review feedback."},
     "expected": {"top_match": "ReviewPilot", "category": "strong_overlap_or_higher", "not_duplicate": ["Secure Code Review Board", "SecureGuard AI"]}},
]
