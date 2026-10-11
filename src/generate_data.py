"""
Generate a synthetic BPO quality dataset and load it into SQLite.

Tables:
    lines, agents, qa_analysts, form_items   -> dimensions (context)
    audits                                   -> fact table (one row per audit)
    audit_items                              -> fact detail (one row per item per audit)

Run from the project root:
    python src/generate_data.py
"""

import sqlite3
from pathlib import Path

import numpy as np
import pandas as pd
from faker import Faker

# ---------------------------------------------------------------------------
# 1. Settings: change these to make the dataset bigger or smaller
# ---------------------------------------------------------------------------
SEED = 42                  # same seed -> same data every time (reproducible)
N_AGENTS = 500
N_QA = 25
N_WEEKS = 12
AUDITS_PER_AGENT_WEEK = 15
START_DATE = "2026-06-01"  # a Monday

DB_PATH = Path("data/qa_lab.db")

rng = np.random.default_rng(SEED)
fake = Faker("es_CO")
Faker.seed(SEED)

# ---------------------------------------------------------------------------
# 2. Dimension tables
# ---------------------------------------------------------------------------
lines = pd.DataFrame({
    "line_id": range(1, 7),
    "line_name": ["Marketplace Safety", "Ads Review", "Live Streams",
                  "Customer Care", "Payments Support", "Trust & Safety Appeals"],
    "channel": ["Content", "Content", "Content", "Chat", "Voice", "Email"],
    # how hard the line is: higher = more errors (hidden, used only to simulate)
    "difficulty": [0.00, 0.02, 0.06, 0.03, 0.05, 0.04],
})

team_leaders = [fake.name() for _ in range(20)]
agents = pd.DataFrame({
    "agent_id": range(1001, 1001 + N_AGENTS),
    "agent_name": [fake.name() for _ in range(N_AGENTS)],
    "line_id": rng.integers(1, 7, N_AGENTS),
    "team_leader": rng.choice(team_leaders, N_AGENTS),
    "hire_date": pd.to_datetime(START_DATE)
                 - pd.to_timedelta(rng.integers(15, 1100, N_AGENTS), unit="D"),
})
# Each agent has a hidden "skill": their base chance of failing an item
agents["skill_error_rate"] = rng.beta(2, 30, N_AGENTS)

qa_analysts = pd.DataFrame({
    "qa_id": range(1, N_QA + 1),
    "qa_name": [fake.name() for _ in range(N_QA)],
    # some QAs are stricter than others -> a calibration problem to discover
    "strictness": rng.normal(1.0, 0.15, N_QA).clip(0.7, 1.4),
})

form_items = pd.DataFrame({
    "item_id": range(1, 11),
    "item_name": ["Correct policy applied", "Correct label / action",
                  "Evidence reviewed completely", "Escalation when required",
                  "Notes and documentation", "Handling time within target",
                  "Tone and empathy", "Process steps followed",
                  "Customer data protected", "Final resolution confirmed"],
    "category": ["Accuracy", "Accuracy", "Accuracy", "Compliance",
                 "Process", "Process", "Soft skills", "Process",
                 "Compliance", "Accuracy"],
    "weight": [20, 15, 10, 15, 5, 5, 10, 10, 0, 10],   # sums to 100
    "is_critical": [1, 0, 0, 1, 0, 0, 0, 0, 1, 0],    # critical fail -> score 0
    "base_fail_mult": [0.5, 1.4, 1.2, 0.35, 2.0, 1.6, 0.9, 1.3, 0.15, 0.8],
})

# ---------------------------------------------------------------------------
# 3. Audits (fact table)
# ---------------------------------------------------------------------------
n_audits = N_AGENTS * N_WEEKS * AUDITS_PER_AGENT_WEEK
audits = pd.DataFrame({
    "audit_id": range(1, n_audits + 1),
    "agent_id": np.repeat(agents["agent_id"].values,
                          N_WEEKS * AUDITS_PER_AGENT_WEEK),
    "week": np.tile(np.repeat(np.arange(N_WEEKS), AUDITS_PER_AGENT_WEEK),
                    N_AGENTS),
})
audits["audit_date"] = (pd.to_datetime(START_DATE)
                        + pd.to_timedelta(audits["week"] * 7
                                          + rng.integers(0, 6, n_audits), unit="D"))
audits["qa_id"] = rng.integers(1, N_QA + 1, n_audits)

# bring in the hidden factors we need to simulate errors
audits = (audits
          .merge(agents[["agent_id", "line_id", "hire_date", "skill_error_rate"]],
                 on="agent_id")
          .merge(lines[["line_id", "difficulty"]], on="line_id")
          .merge(qa_analysts[["qa_id", "strictness"]], on="qa_id"))

tenure_days = (audits["audit_date"] - audits["hire_date"]).dt.days
new_hire_penalty = np.where(tenure_days < 90, 0.04, 0.0)   # new hires err more
learning_trend = -0.002 * audits["week"]                   # team improves over time

audit_error_rate = ((audits["skill_error_rate"] + audits["difficulty"]
                     + new_hire_penalty + learning_trend)
                    * audits["strictness"]).clip(0.005, 0.6)

# ---------------------------------------------------------------------------
# 4. Audit items (one row per audit x form item)
# ---------------------------------------------------------------------------
n_items = len(form_items)
fail_prob = np.outer(audit_error_rate.values, form_items["base_fail_mult"].values)
failed = rng.random(fail_prob.shape) < fail_prob.clip(0, 0.95)

audit_items = pd.DataFrame({
    "audit_id": np.repeat(audits["audit_id"].values, n_items),
    "item_id": np.tile(form_items["item_id"].values, len(audits)),
    "passed": (~failed).ravel().astype(int),
})

# score = 100 - weights of failed items; any critical fail -> 0
weights = form_items["weight"].values
critical = form_items["is_critical"].values.astype(bool)
audits["has_critical_error"] = failed[:, critical].any(axis=1).astype(int)
audits["score"] = np.where(audits["has_critical_error"] == 1, 0,
                           100 - (failed * weights).sum(axis=1))

# ---------------------------------------------------------------------------
# 5. Save to SQLite (hidden simulation columns are dropped)
# ---------------------------------------------------------------------------
DB_PATH.parent.mkdir(exist_ok=True)
with sqlite3.connect(DB_PATH) as conn:
    lines.drop(columns="difficulty").to_sql("lines", conn, if_exists="replace", index=False)
    agents.drop(columns="skill_error_rate").assign(
        hire_date=agents["hire_date"].dt.date.astype(str)
    ).to_sql("agents", conn, if_exists="replace", index=False)
    qa_analysts.drop(columns="strictness").to_sql("qa_analysts", conn, if_exists="replace", index=False)
    form_items.drop(columns="base_fail_mult").to_sql("form_items", conn, if_exists="replace", index=False)
    audits[["audit_id", "audit_date", "agent_id", "qa_id", "score", "has_critical_error"]].assign(
        audit_date=audits["audit_date"].dt.date.astype(str)
    ).to_sql("audits", conn, if_exists="replace", index=False)
    audit_items.to_sql("audit_items", conn, if_exists="replace", index=False)

print(f"Database created: {DB_PATH}")
print(f"  agents:      {len(agents):>9,}")
print(f"  audits:      {len(audits):>9,}")
print(f"  audit_items: {len(audit_items):>9,}")
print(f"  avg score:   {audits['score'].mean():>9.1f}")
print(f"  critical %:  {audits['has_critical_error'].mean():>9.1%}")
