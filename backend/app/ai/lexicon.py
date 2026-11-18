"""Domain concept lexicon.

This is the knowledge that powers the *deterministic* semantic layer used when no embedding
model / LLM is configured. Each concept groups alternative enterprise terminology (e.g.
"SAST", "static analysis" and "secure code analysis") so that ideas phrased with different
vocabulary map to the same concept.

Facets:
  domain      - the problem space / business objective
  capability  - functional capabilities
  user        - target user groups
  tech        - technologies

Weights express specificity: generic concepts ("security", "automation") contribute little;
specific ones ("software composition analysis") contribute a lot.

The lexicon is an approximation of semantic understanding, not a learned model. When an
OpenAI-compatible embedding model and LLM are configured they complement it.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from functools import lru_cache

from app.ai.text import stem, tokens


@dataclass(frozen=True)
class Concept:
    id: str
    label: str
    facet: str
    weight: float
    terms: tuple[str, ...]
    related: tuple[str, ...] = field(default_factory=tuple)


def _c(id: str, label: str, facet: str, weight: float, terms: str, related: str = "") -> Concept:
    return Concept(
        id=id,
        label=label,
        facet=facet,
        weight=weight,
        terms=tuple(t.strip() for t in terms.split("|") if t.strip()),
        related=tuple(r.strip() for r in related.split("|") if r.strip()),
    )


CONCEPTS: list[Concept] = [
    # ------------------------------------------------------------------ domains
    _c("appsec", "Application security", "domain", 0.9,
       "application security|appsec|secure code|secure coding|devsecops|secure sdlc|software security|code security|secure software"),
    _c("vulnerability", "Vulnerability detection", "domain", 1.0,
       "vulnerability|vulnerabilities|vuln|vulns|cve|security flaw|security weakness|security bug|security issue|insecure|sql injection|injection flaw|xss|owasp|exploitable|security defect",
       "static application security testing|dependency vulnerability scanning|secure code analysis|application security scanning"),
    _c("cybersecurity", "Cybersecurity (general)", "domain", 0.35,
       "security|cybersecurity|cyber|threat|attack"),
    _c("cloud_posture", "Cloud security posture", "domain", 1.0,
       "cloud configuration|misconfiguration|misconfigured|cloud posture|cspm|security posture|public bucket|storage bucket|s3 bucket|iam role|iam policy|overly permissive|permissive|cloud account|aws account|azure subscription|security group|open port|encryption setting",
       "cloud security posture management|configuration drift detection"),
    _c("cloud", "Cloud infrastructure", "domain", 0.5,
       "cloud|aws|azure|gcp|landing zone|infrastructure as code|iac|cloud resource|cloud infrastructure"),
    _c("fraud", "Fraud & financial crime", "domain", 1.0,
       "fraud|fraudulent|scam|money mule|mule account|account takeover|chargeback|financial crime|suspicious activity|suspicious payment|suspicious transaction|aml|anti money laundering",
       "financial crime detection|fraud analytics"),
    _c("payments", "Payments & transactions", "domain", 0.7,
       "transaction|payment|card|wire transfer|money movement|authorization|authorisation|merchant|settlement|transfer"),
    _c("data_quality", "Data quality & reliability", "domain", 1.0,
       "data quality|data validation|data integrity|trustworthy data|trusted data|data trust|data reliability|data observability|data freshness|stale data|stale table|schema drift|schema change|null value|duplicate row|broken feed|broken pipeline|data accuracy|reconciliation|reconcile|data incident|bad data|data check|data contract|wrong number|inconsistent figure|late feed|incomplete feed|missing data|figure can be trusted|number can be trusted|data defect|data issue|completeness check|arrive late|arrived late|file arrived late|late file|half empty|empty file|incomplete file|partial file|missing file|check the feed|check feed|feed check|numbers are wrong|number are wrong|figures are wrong|data is wrong|late data|wrong data|tie out|break in reconciliation|reconciliation break",
       "data observability|data validation rules|pipeline health monitoring"),
    _c("data_pipeline", "Data pipelines & warehousing", "domain", 0.6,
       "etl|elt|ingestion|feed|source file|file transfer|data feed|upstream feed|upstream system|airflow|dbt|data warehouse|warehouse|snowflake|data lake|batch job|data pipeline|data platform|downstream report|lineage"),
    _c("bi_analytics", "Analytics & business intelligence", "domain", 0.9,
       "business intelligence|bi|dashboard|kpi|text to sql|natural language query|self service analytics|ad hoc analysis|ad hoc query|chart|visualization|visualisation|power bi|tableau|analytics|insight",
       "conversational analytics|generative bi"),
    _c("onboarding", "Employee onboarding", "domain", 1.0,
       "onboarding|onboard|new hire|new joiner|new starter|first day|joiner|day one|orientation|welcome pack|induction",
       "new hire experience|employee onboarding automation"),
    _c("hr", "HR & workforce", "domain", 0.45,
       "hr|human resource|workforce|people team|talent|payroll|benefit|leave request"),
    _c("access_mgmt", "Access & entitlement management", "domain", 1.0,
       "access request|request access|entitlement|permission request|role request|access provisioning|provision access|grant access|privileged access|access approval|access review|deprovision|joiner mover leaver|iam request|identity governance|least privilege|application access|system access|access to application|application permission|system permission|request permission|access right|user access|request system access",
       "identity and access management workflow|entitlement provisioning"),
    _c("incident", "Incident management", "domain", 1.0,
       "incident|outage|root cause|rca|postmortem|post mortem|on call|sev1|major incident|alert storm|service disruption|mttr|runbook|production issue",
       "incident response automation|aiops"),
    _c("reporting", "Operational & regulatory reporting", "domain", 0.5,
       "report|morning report|daily report|regulatory report|management information|mi report|published report|report go out|reports go out|reporting pack"),
    _c("observability", "Monitoring & observability", "domain", 0.55,
       "monitor|monitoring|observability|telemetry|log|trace|uptime|availability|health check|latency|error rate|sla"),
    _c("api", "APIs & integration", "domain", 0.5,
       "api|apis|endpoint|rest|api gateway|openapi|microservice|integration"),
    _c("api_monitoring", "API monitoring", "domain", 1.0,
       "api monitoring|api health|endpoint monitoring|api latency|api error rate|synthetic check|synthetic monitoring|synthetic test|api uptime|api sla|api availability|5xx|contract test",
       "synthetic API monitoring|API observability"),
    _c("knowledge", "Enterprise knowledge search & Q&A", "domain", 1.0,
       "knowledge base|knowledge assistant|knowledge management|enterprise search|question answering|answer question|internal documentation|find information|policy question|intranet|rag|retrieval augmented|semantic search|chat with document|faq|find answer|search document|citation|with citation|internal policy|policy answer|answer from the intranet",
       "retrieval augmented generation|enterprise Q&A assistant"),
    _c("compliance", "Compliance & regulatory (general)", "domain", 0.5,
       "compliance|regulatory|regulation|regulator|audit|auditor|policy|control"),
    _c("compliance_docs", "Compliance documentation", "domain", 1.0,
       "compliance documentation|regulatory documentation|control evidence|audit evidence|control narrative|evidence collection|policy document|sox|regulatory filing|control testing|compliance report|audit pack|evidence pack|control description",
       "control documentation automation|audit evidence generation"),
    _c("customer_service", "Customer service & contact routing", "domain", 1.0,
       "customer service|contact center|contact centre|call center|call centre|call routing|ticket routing|route inquiry|route enquiry|customer inquiry|customer enquiry|customer request|chat routing|intent classification|intent detection|agent assignment|skill based routing|customer complaint|customer message|customer email|right agent|right team",
       "intelligent contact routing"),
    _c("doc_classification", "Document classification", "domain", 1.0,
       "document classification|classify document|document tagging|auto tag|records management|retention label|retention schedule|sensitivity label|document type|taxonomy|categorize document|categorise document|metadata tagging|unstructured document",
       "records classification|automated document labelling"),
    _c("contract", "Contract analysis", "domain", 1.0,
       "contract|clause|legal document|contractual obligation|key obligation|vendor agreement|extract term|legal review|renewal date|indemnity|termination right|nda",
       "contract intelligence|clause extraction"),
    _c("testing", "Software testing & QA", "domain", 1.0,
       "test automation|automated testing|automated test|test generation|generate test|unit test|regression test|test case|qa|quality assurance|test coverage|flaky test|end to end test|e2e test|selenium|playwright|test suite|testing",
       "AI test generation|continuous testing"),
    _c("code_review", "Code review", "domain", 0.9,
       "code review|review pull request|pull request review|pr review|review comment|reviewer|code quality|maintainability|code smell|style issue|readability|refactor suggestion|review code|reviews code",
       "AI pull request reviewer"),
    _c("governance_process", "Governance & review-board process", "domain", 1.0,
       "review board|governance|committee|sign off|manual review|checklist|attestation|approval gate|change advisory|architecture review|policy exception|exception request|risk acceptance",
       "governance workflow"),
    _c("source_code", "Source code & repositories", "domain", 0.6,
       "repository|repositories|repo|codebase|source code|github|git|pull request|merge request|commit|ci cd|continuous integration|build pipeline"),
    _c("dev_productivity", "Developer productivity", "domain", 0.6,
       "developer productivity|engineering productivity|developer experience|cycle time|lead time|engineering velocity|toil"),
    _c("customer_experience", "Customer experience", "domain", 0.5,
       "customer experience|customer satisfaction|nps|wait time|first contact resolution"),
    _c("sustainability", "Sustainability & ESG", "domain", 1.0,
       "sustainability|carbon|emission|co2|esg|net zero|climate|footprint|green"),
    _c("travel_expense", "Travel & expenses", "domain", 0.9,
       "business travel|travel booking|expense|expense report|flight|hotel|mileage"),
    _c("facilities", "Facilities & workplace", "domain", 0.9,
       "office space|desk booking|workspace booking|meeting room|facilities management|office building|hot desk|floor plan|office occupancy"),
    _c("vendor_risk", "Third-party / vendor risk", "domain", 1.0,
       "vendor risk|third party risk|supplier risk|vendor assessment|supplier due diligence|tprm|vendor questionnaire"),
    _c("model_risk", "Model risk management", "domain", 1.0,
       "model risk|model validation|model inventory|model governance|sr 11 7|model monitoring|model drift"),
    # --------------------------------------------------------------- capabilities
    _c("code_scanning", "Automated code scanning", "capability", 1.0,
       "static analysis|sast|static application security testing|code scanning|code scanner|scan code|semgrep|codeql|secure code analysis|source code analysis|analyze code|analyse code|scan repositories|scan repository|scan repo|repository scanning|scan source code|scan internal repositories|scans repositories"),
    _c("secret_detection", "Secret / credential leak detection", "capability", 0.9,
       "secret scanning|secret detection|hardcoded secret|leaked credential|credential leak|exposed api key|leaked secret"),
    _c("scanning", "Scanning (general)", "capability", 0.4, "scan|scanner|scanning|sweep"),
    _c("dependency_scanning", "Dependency / open-source risk scanning", "capability", 1.0,
       "dependency|dependencies|sca|software composition analysis|open source library|third party library|package vulnerability|sbom|transitive|outdated library|vulnerable package"),
    _c("remediation", "Fix / remediation recommendations", "capability", 1.0,
       "remediation|remediate|recommend fix|recommends fix|suggest fix|suggests fix|fix suggestion|suggested fix|auto fix|autofix|patch suggestion|fix recommendation|how to fix|recommended fix|propose fix|proposed fix|generate fix|fix pull request"),
    _c("realtime_detection", "Real-time transaction detection & scoring", "capability", 1.0,
       "real time|realtime|in flight|transaction scoring|score transaction|scoring transaction|block transaction|block payment|payment screening|authorization decision|before it settle|before settlement|millisecond|low latency|decline transaction|real time scoring|stop fraudulent"),
    _c("case_investigation", "Case investigation & triage", "capability", 1.0,
       "case triage|investigation|investigator|case management|case summary|case summarization|case file|alert queue|alert backlog|prioritize alert|prioritise alert|investigation note|sar narrative|suspicious activity report|case prioritization|case prioritisation|evidence gathering"),
    _c("triage", "Triage & prioritisation", "capability", 0.5, "triage|prioritize|prioritise|prioritization|prioritisation|rank by severity"),
    _c("anomaly_detection", "Anomaly / pattern detection", "capability", 0.7,
       "anomaly|anomalies|anomalous|outlier|unusual pattern|unusual behavior|unusual behaviour|deviation|detect unusual"),
    _c("ml_scoring", "Predictive ML scoring", "capability", 0.7,
       "machine learning model|ml model|classifier|risk score|risk scoring|propensity|predictive model|gradient boosting|xgboost|model scoring|fraud score|predict"),
    _c("summarization", "Summarisation", "capability", 0.6,
       "summarize|summarise|summary|summarization|summarisation|digest|condense"),
    _c("conversational", "Conversational / chat interface", "capability", 0.5,
       "chatbot|chat|conversational|virtual assistant|chat assistant|natural language interface|ask question|answer question|q and a|question and answer|answer employee question|answers employee question"),
    _c("document_extraction", "Document extraction / IDP", "capability", 0.7,
       "extract|extraction|ocr|parse document|pdf|document processing|intelligent document processing|idp|field extraction"),
    _c("workflow_automation", "Workflow & approval automation", "capability", 0.55,
       "approval|approve|workflow|manager approval|self service|ticket|form|request fulfilment|request fulfillment|auto approve|routing rule"),
    _c("provisioning", "Account & access provisioning", "capability", 0.8,
       "provisioning|provision|account creation|create account|laptop|equipment|hardware request|deprovision"),
    _c("alerting", "Alerting & notification", "capability", 0.4,
       "alert|alerting|notify|notification|warn|warning|pager|email alert|slack|escalate|escalation"),
    _c("automation", "Automation (general)", "capability", 0.25,
       "automate|automation|automated|automatic|automatically|rpa|bot|auto"),
    _c("routing", "Routing & assignment", "capability", 0.7,
       "route|routing|assign|assignment|dispatch|queue"),
    _c("text_generation", "Content generation / drafting", "capability", 0.6,
       "draft|drafting|generate document|generate narrative|write documentation|generated documentation|auto generate|template filling|narrative generation"),
    _c("search_retrieval", "Search & retrieval", "capability", 0.5,
       "search|retrieve|retrieval|lookup|look up|find"),
    _c("classification", "Classification", "capability", 0.6,
       "classify|classification|categorize|categorise|categorization|label|tagging|tag"),
    _c("drift_detection", "Drift / change detection", "capability", 0.7,
       "drift|change detection|detect change|configuration change|deviation from baseline|baseline"),
    _c("validation_checks", "Automated checks & validation", "capability", 0.7,
       "check|checks the|validate|validation|verify|verification|reconcile|reconciliation|completeness|freshness|catch|catching|quality gate|sanity check|tie out"),
    _c("root_cause", "Root-cause analysis", "capability", 0.9,
       "root cause|correlate alert|correlate log|correlation of event|probable cause|causal analysis|timeline reconstruction"),
    _c("tracking", "Tracking & reporting", "capability", 0.4,
       "track|tracking|calculate|calculation|measure|measurement|report on|reporting"),
    # ---------------------------------------------------------------------- users
    _c("u_developers", "Software developers", "user", 1.0,
       "developer|software engineer|engineering team|dev team|programmer|development team|application team|application developer|engineer"),
    _c("u_security", "Security engineers / analysts", "user", 1.0,
       "security engineer|security analyst|security team|appsec team|soc|security operation|ciso|red team|security champion"),
    _c("u_fraud", "Fraud investigators / analysts", "user", 1.0,
       "fraud investigator|fraud analyst|investigator|fraud operation|financial crime analyst|aml analyst|fraud team"),
    _c("u_customers", "Customers", "user", 1.0, "customer|cardholder|client|account holder|retail banking customer"),
    _c("u_agents", "Contact-centre agents", "user", 1.0,
       "contact center agent|contact centre agent|service agent|customer service agent|advisor|call center agent|support agent|frontline staff"),
    _c("u_employees", "All employees", "user", 0.8, "employee|staff|colleague|all staff|workforce|new hire"),
    _c("u_hr", "HR teams", "user", 1.0, "hr team|hr partner|recruiter|people team|hr operation|hiring manager"),
    _c("u_managers", "Line managers / approvers", "user", 0.8, "line manager|people manager|approver|manager"),
    _c("u_data", "Data & analytics professionals", "user", 1.0,
       "data analyst|data engineer|data steward|data scientist|business analyst|finance analyst|reporting team|analyst"),
    _c("u_ops", "Operations / SRE", "user", 1.0,
       "operations team|sre|site reliability|platform engineer|on call engineer|it operation|noc|operations analyst|ops team"),
    _c("u_compliance", "Compliance, risk & legal", "user", 1.0,
       "compliance officer|compliance team|auditor|risk officer|control owner|legal team|lawyer|counsel|compliance analyst|risk team"),
    _c("u_qa", "QA / test engineers", "user", 1.0, "qa engineer|tester|test engineer|quality engineer|sdet"),
    _c("u_cloud", "Cloud / platform engineers", "user", 1.0, "cloud engineer|platform team|infrastructure team|devops|cloud team"),
    _c("u_leadership", "Executives & business leaders", "user", 0.7, "executive|leadership|business stakeholder|business leader|senior management"),
    _c("u_travellers", "Business travellers", "user", 0.8, "traveller|traveler|travel coordinator"),
    # ----------------------------------------------------------------------- tech
    _c("t_llm", "LLM / generative AI", "tech", 0.8,
       "llm|large language model|generative ai|genai|gpt|copilot|prompt|foundation model|azure openai|gen ai"),
    _c("t_ai", "AI / ML (general)", "tech", 0.3, "ai|artificial intelligence|machine learning|ml|intelligent|smart|ai powered"),
    _c("t_python", "Python", "tech", 0.5, "python|fastapi|django|flask|pandas"),
    _c("t_java", "Java / JVM", "tech", 0.5, "java|spring|kotlin|scala"),
    _c("t_js", "TypeScript / JavaScript", "tech", 0.5, "typescript|javascript|react|node|nextjs"),
    _c("t_k8s", "Kubernetes / containers", "tech", 0.6, "kubernetes|k8s|docker|container|helm|openshift"),
    _c("t_terraform", "Terraform / IaC", "tech", 0.7, "terraform|cloudformation|bicep|pulumi"),
    _c("t_streaming", "Event streaming", "tech", 0.8, "kafka|flink|stream processing|event stream|kinesis|streaming"),
    _c("t_spark", "Spark / big data", "tech", 0.7, "spark|databricks|hadoop|pyspark"),
    _c("t_warehouse", "Cloud data warehouse", "tech", 0.6, "snowflake|bigquery|redshift|synapse"),
    _c("t_vector", "Vector search", "tech", 0.7, "vector database|vector store|pgvector|embedding|embeddings|faiss|elasticsearch|opensearch"),
    _c("t_servicenow", "ServiceNow", "tech", 0.7, "servicenow|service now|snow"),
    _c("t_github_actions", "CI / GitHub Actions", "tech", 0.6, "github action|jenkins|gitlab ci|ci pipeline"),
    _c("t_graph", "Graph analytics", "tech", 0.7, "graph|neo4j|network analysis|link analysis"),
    _c("t_ocr", "OCR / document AI", "tech", 0.7, "ocr|textract|form recognizer|document ai"),
    _c("t_rpa", "RPA", "tech", 0.7, "rpa|uipath|blue prism|power automate"),
]

CONCEPT_BY_ID: dict[str, Concept] = {c.id: c for c in CONCEPTS}
FACETS = ("domain", "capability", "user", "tech")


def _term_key(term: str) -> tuple[str, ...]:
    return tuple(stem(t) for t in tokens(term))


@lru_cache(maxsize=1)
def _phrase_index() -> dict[tuple[str, ...], list[str]]:
    index: dict[tuple[str, ...], list[str]] = {}
    for concept in CONCEPTS:
        for term in concept.terms:
            key = _term_key(term)
            if key and concept.id not in index.get(key, []):
                index.setdefault(key, []).append(concept.id)
    return index


@lru_cache(maxsize=1)
def _max_phrase_len() -> int:
    return max(len(k) for k in _phrase_index())


def extract_concepts(text: str) -> dict[str, int]:
    """Return {concept_id: occurrence_count} found in `text` (longest-phrase-first matching)."""
    toks = [stem(t) for t in tokens(text)]
    index = _phrase_index()
    max_len = _max_phrase_len()
    found: dict[str, int] = {}
    i = 0
    n = len(toks)
    while i < n:
        matched = False
        for length in range(min(max_len, n - i), 0, -1):
            key = tuple(toks[i : i + length])
            ids = index.get(key)
            if ids:
                for cid in ids:
                    found[cid] = found.get(cid, 0) + 1
                # Multi-word matches also count the *domain* concepts of their shorter
                # sub-phrases (e.g. "fraud investigator" -> fraud user + fraud domain).
                if length > 1:
                    for sub_len in range(length - 1, 0, -1):
                        for start in range(0, length - sub_len + 1):
                            sub = tuple(toks[i + start : i + start + sub_len])
                            for cid in index.get(sub, []):
                                if CONCEPT_BY_ID[cid].facet == "domain":
                                    found.setdefault(cid, 1)
                i += length
                matched = True
                break
        if not matched:
            i += 1
    return found


def concept_set(text: str) -> set[str]:
    return set(extract_concepts(text))


def concepts_by_facet(concept_ids: set[str] | dict[str, int]) -> dict[str, set[str]]:
    out: dict[str, set[str]] = {f: set() for f in FACETS}
    for cid in concept_ids:
        concept = CONCEPT_BY_ID.get(cid)
        if concept:
            out[concept.facet].add(cid)
    return out


def labels(concept_ids) -> list[str]:
    return [CONCEPT_BY_ID[c].label for c in sorted(concept_ids, key=lambda c: -CONCEPT_BY_ID[c].weight) if c in CONCEPT_BY_ID]


def alternative_terms(concept_ids, limit: int = 12) -> list[str]:
    """Alternative enterprise terminology for the concepts in an idea (used for query expansion)."""
    seen: list[str] = []
    ranked = sorted((CONCEPT_BY_ID[c] for c in concept_ids if c in CONCEPT_BY_ID), key=lambda c: -c.weight)
    for concept in ranked:
        if concept.facet not in ("domain", "capability") or concept.weight < 0.6:
            continue
        candidates = list(concept.related) + [t for t in concept.terms if len(t.split()) >= 2]
        for term in candidates[:3]:
            if term not in seen:
                seen.append(term)
        if len(seen) >= limit:
            break
    return seen[:limit]


def expansion_terms(concept_ids) -> list[str]:
    """All lexical variants for a set of concepts (used to expand keyword queries)."""
    out: list[str] = []
    for cid in concept_ids:
        concept = CONCEPT_BY_ID.get(cid)
        if concept and concept.weight >= 0.6:
            out.extend(concept.terms)
    return out
