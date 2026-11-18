# Demo Guide: Idea Discovery

A practical script for presenting Idea Discovery to an innovation team or an engineering manager. The core demo takes 5 minutes, and there are 3 extra minutes of optional scenarios.

---

## A. Demo preparation

**Docker is not required.** The app runs natively against a local PostgreSQL that has pgvector installed.

### First-time setup (about 5 minutes)

```bash
cd DiscoveryAgent
make setup        # Python venv + Node dependencies
make db           # createdb idea_discovery
```

No environment variables are required. Without an LLM key the app runs in **deterministic demo mode**, which gives the same results every time and is the safest choice for a live demo.

The following are optional:
- **Use Claude Sonnet 5.5:** put `ANTHROPIC_API_KEY=...` in `.env` before starting the API.
- **Demo a source outage:** start the API with `FAIL_SOURCES=sharepoint`, or tick a box in the full submission form.

### Before every presentation

```bash
make reset        # wipes previous searches and registered ideas, re-seeds the synthetic data
make test         # optional: 66 tests should pass
make dev          # API :8000 + web app :3000 (or run `make backend` and `make frontend` in two terminals)
```

### URLs to open

- App: **http://localhost:3000**
- API docs (for technical audiences): http://localhost:8000/docs

### Pre-flight check (1 minute)

1. Open http://localhost:3000. The top bar shows a **Mock data** badge and **Demo AI mode** (or `claude-sonnet-5-5` if a key is set). A red "API offline" badge means the API isn't running.
2. The bottom of the **Home** page reads *Index: 27 initiatives · 80 source records · 11 departments · 7 connected sources (mock)*.
3. Open **Source Explorer**. All 7 systems should show **Healthy**.
4. Optionally run `make scenarios` in a terminal. All 7 scenarios should print the categories listed in the table at the end of this guide.

---

## B. Five-minute demo script

| Time | Do this | Say this |
|---|---|---|
| 0:00 | Open **Home**. | "Teams regularly spend months building something another team already built. Idea Discovery makes checking for existing work the first step, before any development starts." Point at the stats: 27 initiatives across 11 departments, in 7 systems. "All of this is synthetic, so we can demo safely." |
| 0:30 | Paste the **main scenario** (section C) into the box and click **Check for existing work**. | "I'm writing this the way an engineer would, in plain English, without project names." |
| 0:40 | Watch the **live progress** screen. | "These steps are real backend progress: it understands the idea, generates alternative terms, then searches each system at the same time." Point at the alternative-terms chips: *static application security testing, secure code analysis, dependency vulnerability scanning*. "Nobody typed 'SAST'. The agent expanded the terminology itself." |
| 1:00 | Results load. Read the **navy verdict banner** and the **Recommended next step** panel on the right. | "**Near-duplicate: SecureGuard AI already covers most of this idea.** Recommended action: contact Priya Raman before starting." |
| 1:20 | Point at the summary row: **7 of 7 sources, 33 records, 15 candidate initiatives, 2 relevant**. Note the three tabs: *Matches*, *How we searched*, *Limitations*. | "It read 33 records and narrowed them to 2 that matter." |
| 1:40 | The top match (SecureGuard AI) opens automatically. Show the **5 source icons** in its header, then click **Show all 9 records** under *Source evidence*. Other matches open when you click their row. | "Five systems: Confluence architecture doc, Jira epic SEC-284, the GitHub repo, a SharePoint steering deck and a Teams announcement. They're grouped into **one** initiative, not shown as five separate results." |
| 2:10 | Click the **SharePoint** record to open the drawer. | "This deck has no project label. It was linked because it mentions Jira SEC-284." Point at **Why this record is here** and the **Retrieved fact** label. |
| 2:40 | Show the **Owner** and **Lifecycle** sections. | "The owner comes from the Jira epic, and the source is shown. The stage is **Active development**: the Jira epic is *In Progress* and there were 57 commits in the last 30 days. Nothing is invented. If evidence were missing, it would say Unknown." |
| 3:00 | Click **Compare side by side**. | "Shared: SAST of internal repositories and LLM fix suggestions on pull requests. SecureGuard also has dependency scanning and secret detection. Your idea adds nothing they don't already cover." Point at the dimension bars and the info tooltip: "This score ranks the matches. It isn't a probability." Point at **Reusable components**: the Semgrep rule pack, the PR-comment GitHub App, and the prompt library. |
| 3:40 | Go back. Click **Register this idea**. | "If the team still wants their own initiative, they have to acknowledge the overlap first. That's how we stop accidental duplicates." Cancel the dialog. |
| 4:00 | Open **Demo scenarios** and run **No significant match**. | "When nothing matches, it doesn't claim the idea is new. It says nothing was found **in the sources searched**, and suggests registering the idea." |
| 4:30 | Close with business value (section F). | "Two minutes of checking instead of months of duplicated work, and the right people end up talking to each other." |

---

## C. Main scenario: strong duplicate (SecureGuard AI)

**Idea to enter:**

> We want to build an AI-powered cybersecurity checker that scans internal repositories for vulnerabilities and recommends fixes.

**Expected result:**
- **Verdict:** Near-duplicate. "SecureGuard AI already covers most of this idea."
- **Recommended action:** "Contact Priya Raman (Application Security Engineering) before starting."
- **SecureGuard AI** (Cybersecurity Engineering · Application Security Engineering), overlap score about 95/100, **Active development**.
- **Owner:** Priya Raman, Jira epic owner. Source: Jira SEC-284. Email priya.raman@northbridge.example.
- **Evidence (9 records):**
  - Confluence **APPSEC-1042** "SecureGuard AI — Architecture Proposal" (Approved)
  - Confluence **APPSEC-1077** "Pilot Findings" (140 repos, 61% of fixes accepted)
  - Jira **SEC-284** epic "Automated Vulnerability Scanner (SecureGuard AI)" (In Progress), plus stories **SEC-317** (In Progress) and **SEC-322** (Done)
  - GitHub **northbridge-appsec/secureguard-scanner** (57 commits in the last 30 days) and PR **#212**
  - SharePoint **SP-SECENG-031** steering-committee deck, linked because it mentions SEC-284
  - Teams **#appsec-guild** announcement
- **Similarities:** SAST of internal repositories; LLM-generated fix suggestions on pull requests.
- **Differences:** SecureGuard also includes SCA dependency scanning, secret detection and a severity triage dashboard. The idea has nothing SecureGuard lacks.
- **Second match:** *LLM pull request security reviewer* (IDEA-0001), registered by Ravi Shankar. Partial overlap. "Someone else has proposed something similar, too."
- **Unlinked evidence:** a Teams hackathon post about scanning dependencies. It's shown separately because it has no cross-reference to any initiative. "We don't merge records on guesswork."

**Why contact the team instead of building:** the team is actively developing it, is looking for more pilot business units, and offers reusable components.

---

## D. Second scenario: partial overlap (fraud)

On the **Demo scenarios** page, click **Run scenario** on **Partial overlap**, or enter:

> Build an AI fraud detection system that scores card transactions in real time and blocks suspicious payments before they settle.

**Expected result:**
- **Verdict:** Partial overlap. Related work exists, but it doesn't fully cover the idea.
- **MuleNet Network Analytics** (Research): weekly *batch* graph analysis of mule-account networks.
- **CaseLens Fraud Investigation Assistant** (Proof of concept; owner Elena Vasquez-Hart; 4 sources): summarises cases, prioritises the alert queue and drafts SAR narratives.
- For both, "Only in your idea" shows **Real-time transaction detection & scoring**.

**What to point out:**
- The business domain is the same (objective score about 85–95), but the core capabilities don't match (capability score 0). "Same problem area, different job."
- CaseLens's Confluence page says *"Out of scope: real-time transaction scoring"*. The agent reads that as an exclusion. A naive keyword or embedding search would have called this a duplicate.
- The recommendation is a **scope discussion**, not "stop". CaseLens could take the real-time detector's alerts as input.

---

## E. Third scenario: no match, then registration and rediscovery

1. Run **No significant match** from the Demo page, or enter:
   > An app that calculates the carbon footprint of employee business travel and suggests lower-emission alternatives when people book flights and hotels.
2. **Expected:** "No significant overlap found in the sources searched", with 0 relevant initiatives and the recommendation *"Register your idea and proceed through normal approval"*. Open the **Limitations** tab: "No match does not prove that no similar work exists…"
3. Click **Register this idea**, enter a name (e.g. `alex.morgan@northbridge.example`), then click **Register idea**. A toast confirms `IDEA-0005` or similar. Click **Open in Idea Registry**. The new idea is highlighted with a blue outline, has status *registered* and links to its overlap report.
4. Go to **Check an idea** and enter a paraphrase with no shared title:
   > Tool to measure CO2 emissions from staff flights and hotel stays
5. **Expected:** the registered idea now appears as a **Strong overlap or Near-duplicate** match from the **Idea Registry** source, with you as the owner. "The next person with this idea finds you instead of starting over."

---

## Optional extras (if time allows)

| Scenario | Shows | Expected |
|---|---|---|
| **Abandoned initiative** | History awareness | **DocuMind Contract Clause Extractor**, Abandoned (high confidence): Confluence says *Stopped*, Jira says *Won't Do*, and the repo is archived; inactive for over a year. The action is "Find out why…", not "contact the active team". The findings record 71% accuracy against a 90% target, and the annotated dataset is reusable. |
| **Already deployed solution** | Avoiding rebuilds | **AccessFlow**, Deployed. ServiceNow APP0004417 is *Operational*; owner Grace Liu (service owner). The action is "Evaluate AccessFlow before building anything". |
| **Different names, same objective** | Semantic matching | An operations-language idea ("source file arrived late or half empty… numbers are wrong") finds **Pipeline Sentinel** (data-engineering wording: freshness, schema drift) as a Near-duplicate, and the Operations team's **Trustworthy Data Initiative** as a Partial overlap. "Two teams, two vocabularies, one problem. The agent connects them." |
| **Similar keywords, different problem** | False-positive prevention | AI code review → **ReviewPilot** is the match. **SecureGuard AI** shares "pull request", "code" and "review", but is only *Related*. The **Secure Code Review Board** (a governance process) is not flagged. |
| **Resilience** | Honest partial results | On **Check an idea**, open *Resilience demo*, tick *ServiceNow unavailable*, and run the access-request idea. The amber "Search not comprehensive" banner appears. AccessFlow is still found through Confluence, and no ServiceNow evidence is shown. |
| **Source Explorer** | How conclusions were reached | Indexed records show the *Linked initiative* and the correlation reason for every record. The restricted Confluence page shows only a lock. In the relationship graph, hover over SecureGuard to see its team, owner and records. |
| **Export** | Shareable output | Use **Export report (.md)** or **Print view**, then *Print / save as PDF*. |

---

## F. Business value talking points

- **The problem:** knowledge about initiatives is spread across Confluence, Jira, GitHub, SharePoint, Teams and ServiceNow. Nobody searches all six before starting, so teams duplicate research and engineering, and miss chances to collaborate.
- **Why searching each system separately fails:** every system uses different vocabulary and structure. A Jira epic, a repo and a slide deck about the same project look like three unrelated hits, and you still don't know the owner or whether the project is alive.
- **What the agent does:** one plain-English question searches every system at once. Evidence is grouped by initiative, and you get an explainable verdict: who owns it, what stage it's at, what overlaps, what's reusable, and what to do next.
- **Why semantic matching matters:** people describe the same idea differently ("cybersecurity checker" and "SAST pipeline"; "trustworthy figures" and "data observability"). Keyword search misses these. The agent matches on meaning, while guardrails stop shared words from creating false duplicates.
- **Less duplicated effort:** a two-minute check before funding can save months of engineering. Validation becomes a normal step, just like a design review.
- **More collaboration:** the result names a person to talk to and the components to reuse, so it leads to a conversation rather than just a document.
- **How it scales:** connectors share one read-only interface. More systems (SharePoint Online, Slack, Azure DevOps, internal wikis) plug in without changing the pipeline. The Idea Registry makes every future idea discoverable.

---

## G. Expected stakeholder questions

**How is this different from enterprise search?**
Enterprise search returns documents. This tool returns *initiatives*: it correlates records across systems into a single project, then judges whether that project overlaps with your idea, who owns it, whether it's still active, and what to do.

**Why do we need an AI agent?**
To translate free-text ideas into alternative terminology, to compare objectives and capabilities rather than words, and to write evidence-based explanations. The pipeline itself is deterministic and auditable. The LLM enriches it, and its output is validated against the rules and the retrieved evidence.

**How does it recognise similar ideas with different names?**
Concept-level matching (for example, SAST, static analysis and secure code analysis are one concept), embeddings, and LLM query expansion when configured. The Pipeline Sentinel and Trustworthy Data scenario shows this.

**How does it know whether a project is still active?**
From explicit source statuses, ranked by authority: the ServiceNow lifecycle, Jira "Won't Do" or "On Hold", archived repos, and stages declared on documents. Recent Jira and GitHub activity confirms them. Projects with no activity for over 6 or 12 months are flagged, and conflicts between sources are shown as uncertainty.

**How does it identify owners?**
From the records, in this order: ServiceNow service owner, Jira epic owner, repo maintainer, then page owner. The provenance is always shown ("Source: Jira SEC-284"). If no record names an owner, the result says *Unknown*. It never invents one.

**How accurate is duplicate detection?**
On the included evaluation set (24 free-form ideas, deliberately phrased differently from the demo prompts, including false-positive guards), 24 of 24 pass in deterministic mode. That is a small synthetic benchmark, not a production accuracy claim. Real deployment would need a labelled evaluation set built from internal history. Scores are ranking heuristics, not probabilities.

**What happens when it misses a project?**
The verdict is always qualified ("in the sources searched"), and coverage and limitations are listed. Unavailable sources trigger a "not comprehensive" warning. Registering ideas closes the gap over time, because each registered idea becomes searchable.

**How does it protect confidential information?**
Connectors are read-only. A permission filter applies per-record ACLs, so restricted records are hidden and counted rather than shown. Teams indexing is limited to authorised project channels, and private chats are never searched. Retrieved text is treated as untrusted in prompts, and every search is written to the audit log. *Caveat:* the PoC has no real SSO. Users are a placeholder identity.

**Can we connect it to real Confluence, Jira and GitHub?**
Yes. Each connector implements one interface (`search`, `fetch_related`, `health`). A real connector calls CQL, JQL or GitHub search with a read-only service account and security trimming. The pipeline doesn't change.

**What are the PoC's limitations?**
- The data is synthetic and the connectors are mocked.
- Without an embedding model, semantic matching relies on a hand-built concept lexicon.
- There's no authentication or real per-user permissions.
- The evaluation set is small.
- The Initiative Index is seeded rather than built by an indexing job.

**What would deployment need?**
- SSO and per-user permission trimming.
- Approved read-only API access, with incremental indexing.
- An enterprise LLM gateway and embedding model (both pluggable today).
- A scheduled correlation job, plus an owner curation UI.
- A labelled evaluation set.
- Security, privacy and model-risk reviews, plus monitoring and audit retention.

---

### Reference: expected outcome of every scenario (deterministic mode)

| Scenario | Verdict | Top match | Lifecycle |
|---|---|---|---|
| A Strong duplicate | Near-duplicate | SecureGuard AI | Active development |
| B Partial overlap | Partial overlap | MuleNet / CaseLens | Research / PoC |
| C No match | No significant match | — | — |
| D Abandoned | Near-duplicate | DocuMind Contract Clause Extractor | Abandoned |
| E Deployed | Near-duplicate | AccessFlow | Deployed |
| F Different terminology | Near-duplicate | Pipeline Sentinel (+ Trustworthy Data, partial) | Active development |
| G Similar keywords | Near-duplicate | ReviewPilot (SecureGuard only *related*) | Proof of concept |
