# C.O.V.E.R.T — System Specification

> Canonical reference for tiers, roles, privileges, token logic, and reputation effects.

---

## 1. Reputation (Rep)

- Every wallet starts with `Rep = 0`
- Rep is updated **after a report is finalized** (off-chain, by the automation worker)
- Stored in the `user_reputation` table in the backend database

---

## 2. Tiers (Based on Rep)

| Tier   | Rep Range  | Badge Token    | Meaning          |
|--------|-----------|----------------|------------------|
| Tier 0 | Rep < 20  | TIER_0_NEW     | Low trust        |
| Tier 1 | 20 – 79   | TIER_1_REGULAR | Stable user      |
| Tier 2 | 80 – 199  | TIER_2_TRUSTED | High credibility |
| Tier 3 | ≥ 200     | TIER_3_POWER   | Senior community |

Tier SBT badges are activated/deactivated automatically by the automation worker when Rep crosses a threshold.

---

## 3. Roles

### Basic User (all wallets)

Privileges:
- Submit report (stake 10 COV public / 6 COV private)
- Support a report (stake 1 COV)
- Challenge a report (stake 3 COV)
- Appeal a reviewer decision (bond 8 COV)
- View public reports

### Reviewer

**Activation requires (all three):**
```
Rep ≥ 80
Account age ≥ 30 days
No slashing in the last 30 days
```

**Additional privileges:**
- Set reviewer decision (NEEDS_EVIDENCE / REVIEW_PASSED / REJECT_SPAM)
- Move a report from UNREVIEWED → decision state

**Deactivation triggers (any one):**
```
Rep < 80
OR slashed in the last 30 days
OR marked malicious
OR 3 strikes within 30 days
```

### Moderator

**Manual assignment only** (no automatic promotion).

**Additional privileges:**
- Finalize report (sets FinalLabel, settles all stakes)
- Mark actors as malicious
- Decide appeal outcome
- Override reviewer decision

---

## 4. Actions, Token Locks & Rep Effects

### Submit Report

| Visibility | Stake |
|------------|-------|
| PUBLIC     | 10 COV |
| PRIVATE    | 6 COV |

Rep effect (applied to **reporter** at finalization):

| FinalLabel            | Rep Δ |
|-----------------------|-------|
| CORROBORATED          | +8    |
| NEEDS_EVIDENCE        | 0     |
| DISPUTED              | −2    |
| FALSE_OR_MANIPULATED  | −10   |
| Malicious flag        | −5 (additional) |

---

### Support Report

Stake: **1 COV**

Rep effect (applied to **supporter** at finalization):

| FinalLabel            | Rep Δ |
|-----------------------|-------|
| CORROBORATED          | +1    |
| FALSE_OR_MANIPULATED  | −2    |
| Others                | 0     |
| Malicious flag        | −5 (additional) |

---

### Challenge Report

Stake: **3 COV**

Rep effect (applied to **challenger** at finalization):

| FinalLabel            | Rep Δ |
|-----------------------|-------|
| FALSE_OR_MANIPULATED  | +2    |
| DISPUTED              | +2    |
| NEEDS_EVIDENCE        | +1    |
| CORROBORATED          | −2    |
| Malicious flag        | −5 (additional) |

---

### Appeal (Reporter Only)

Bond: **8 COV**

| Appeal Outcome | Rep Δ | Token Settlement |
|----------------|-------|-----------------|
| APPEAL_WON     | +2    | 8 COV returned  |
| APPEAL_LOST    | 0     | 4 returned, 4 slashed |
| APPEAL_ABUSIVE | −5    | 8 slashed       |

---

## 5. Slashing Rules

Slashing occurs when:
- Report finalized as FALSE_OR_MANIPULATED (reporter + supporters)
- Appeal marked APPEAL_ABUSIVE (reporter bond)
- User explicitly marked malicious by a moderator

Each slashing event:
```
Rep −5 (additional, on top of label-based change)
```

Slashed tokens are minted to the treasury.

---

## 6. Strike Rule

A strike is issued for:
- Being marked malicious by a moderator
- Appeal ruled APPEAL_ABUSIVE
- Coordinated spam (moderator discretion)

Rule:
```
3 strikes within any rolling 30-day window → Reviewer deactivated
```

Strikes expire after 30 days.

---

## 7. Token Summary

| Event                  | Amount |
|------------------------|--------|
| Welcome grant (once)   | 30 COV |
| Report stake (public)  | 10 COV locked |
| Report stake (private) | 6 COV locked  |
| Support stake          | 1 COV locked  |
| Challenge stake        | 3 COV locked  |
| Appeal bond            | 8 COV locked  |

- COV is **non-transferable**
- Tokens are **burned** when locked
- Minted **back** when returned after finalization
- Slashed tokens are **minted to treasury**

---

## 8. Privilege Summary by Tier/Role

| Action                | Tier 0 | Tier 1+ | Reviewer | Moderator |
|-----------------------|:------:|:-------:|:--------:|:---------:|
| Submit report         | ✓      | ✓       | ✓        | ✓         |
| Support               | ✓      | ✓       | ✓        | ✓         |
| Challenge             | ✓      | ✓       | ✓        | ✓         |
| Appeal                | ✓      | ✓       | ✓        | ✓         |
| Set review decision   | ✗      | ✗       | ✓        | ✓ (override) |
| Finalize report       | ✗      | ✗       | ✗        | ✓         |
| Mark malicious        | ✗      | ✗       | ✗        | ✓         |

> Reviewers and Moderators follow role-exclusivity: a wallet holds **one or the other, never both**.
> Reviewers and Moderators **cannot review/finalize their own reports**.

---

## 9. Rep Change Flow (automation worker)

```
Report finalized on-chain
        │
        ▼
backend listens to Finalized(reportId, moderator, finalLabel, appealOutcome) event
        │
        ▼
backend calls getSupporters(reportId) + getChallengers(reportId) on chain
        │
        ▼
for each participant (reporter, supporters, challengers):
    ├─ Apply label-based rep delta (see tables above)
    ├─ Apply malicious penalty if marked
    └─ Update tier + activate/deactivate tier SBT badge
        │
        ▼
If supporter/challenger rep change crosses Reviewer threshold (≥80):
    └─ Check account age & slash history → activate/deactivate REVIEWER_ROLE
```
