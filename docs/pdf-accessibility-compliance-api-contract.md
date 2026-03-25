# PDF Accessibility Compliance Engine — Problem Description and API Contract

## Purpose
To Solve a document-intelligence problem with code plus LLM-assisted reasoning.

The system receives **PDF files** from caller-provided locators and must:

1. scan each PDF for accessibility violations,
2. explain the violations in a structured way,
3. suggest remediations for each issue,
4. aggregate the whole batch into a compliance dashboard.

The content of the PDF is irrelevant.
Only the document's **accessibility characteristics** matter.

---

## Standards in Scope
A learner solution may use any internal implementation approach, but the API responses must reflect checks aligned to these standards:

- WCAG 2.1
- PDF/UA-1
- ADA
- Section 508
- European Accessibility Act (EAA)

---

## Expected API Style
Use **stateless POST endpoints**.
Each request contains the full input needed for the computation.

## What is in scope vs out of scope
This problem evaluates **document intelligence and locator handling**, not CRUD workflows.

### In scope
- opening PDF files directly from the locator supplied in the request,
- analysing PDF accessibility characteristics,
- mapping findings to real standards,
- generating remediation guidance,
- aggregating cross-file compliance intelligence.

### Out of scope
- upload APIs,
- persistence layers,
- document registration flows,
- resource IDs for previously stored files,
- any create/read/update/delete workflow unrelated to the analysis itself.

## PDF source handling requirement
The evaluator is testing document intelligence, but learner solutions must still be able to
**open PDF inputs directly from the locator string provided in the request**.

Accepted locator styles for `fileUrls[]` are:
- HTTPS URLs,
- `file://` URLs,
- absolute local filesystem paths such as `C:\data\docs\report.pdf`.

At evaluation time, the test server may inject fixture files at predetermined local paths.
A correct solution must therefore treat these values as **PDF source locators**, not as IDs for
previously uploaded resources.

For the evaluator setup used in this repository, the PDF fixture directory is mounted into the
learner container under:

```text
/evaluator/assets
```

So a correct learner solution should be able to read values such as:
- `/evaluator/assets/accessible_guide.pdf`
- `file:///evaluator/assets/untagged_report.pdf`
- `C:\data\docs\report.pdf`

### Required endpoints
- `POST /api/v1/scan`
- `POST /api/v1/remediate`
- `POST /api/v1/dashboard`

### Shared request contract
All three endpoints accept this request body shape:

```json
{
  "fileUrls": [
    "/evaluator/assets/doc1.pdf",
    "C:\\data\\docs\\doc2.pdf"
  ]
}
```

---

# 1) POST /api/v1/scan

## What this endpoint must do
For each PDF file:
- detect accessibility issues,
- compute a numeric non-compliance percentage,
- assign a compliance status,
- return issue details,
- identify the worst file in the batch.

## Required success response
HTTP `200`

```json
{
  "files": [
    {
      "fileName": "untagged_report.pdf",
      "nonCompliancePercent": 84,
      "complianceStatus": "non-compliant",
      "issues": [
        {
          "description": "Document does not contain a tag tree, so screen readers cannot interpret structural semantics.",
          "standard": "PDF/UA-1 §7.1",
          "category": "PDF/UA"
        },
        {
          "description": "Document language is not declared at the document level.",
          "standard": "WCAG 2.1 SC 3.1.1",
          "category": "WCAG"
        }
      ]
    },
    {
      "fileName": "accessible_guide.pdf",
      "nonCompliancePercent": 0,
      "complianceStatus": "compliant",
      "issues": []
    }
  ],
  "worstFile": {
    "fileName": "untagged_report.pdf",
    "nonCompliancePercent": 84
  }
}
```

## Field-level contract

### Top level
- `files`: required array
- `worstFile`: required object

### `files[]`
- `fileName`: required string
- `nonCompliancePercent`: required number in range `0..100`
- `complianceStatus`: required string
  - recommended values: `compliant`, `partially-compliant`, `non-compliant`
- `issues`: required array

### `files[].issues[]`
- `description`: required string
- `standard`: required string naming a real standard or clause
- `category`: required string naming a guideline family
  - recommended values include `WCAG`, `PDF/UA`, `ADA`, `Section 508`, `EAA`

### `worstFile`
- `fileName`: required string
- `nonCompliancePercent`: required number

## Behavioral rules
- A fully compliant PDF must return `issues.length == 0` and `nonCompliancePercent == 0`.
- `nonCompliancePercent` must be numeric, not formatted text.
- Each issue must map to a named accessibility standard and category.
- `worstFile` must identify the highest non-compliance file in the submitted batch.
- The endpoint must read PDF content directly from the supplied locator values, including absolute local file paths.

## Correct variations

### Correct: compliant file with no false positives
```json
{
  "files": [
    {
      "fileName": "accessible_guide.pdf",
      "nonCompliancePercent": 0,
      "complianceStatus": "compliant",
      "issues": []
    }
  ],
  "worstFile": {
    "fileName": "accessible_guide.pdf",
    "nonCompliancePercent": 0
  }
}
```

### Correct: mixed batch with grouped issue metadata
```json
{
  "files": [
    {
      "fileName": "missing_alttext.pdf",
      "nonCompliancePercent": 36,
      "complianceStatus": "partially-compliant",
      "issues": [
        {
          "description": "Figure elements are present but missing alternative text.",
          "standard": "WCAG 2.1 SC 1.1.1",
          "category": "WCAG"
        }
      ]
    }
  ],
  "worstFile": {
    "fileName": "missing_alttext.pdf",
    "nonCompliancePercent": 36
  }
}
```

## Incorrect variations

### Incorrect: missing `issues`
```json
{
  "files": [
    {
      "fileName": "untagged_report.pdf",
      "nonCompliancePercent": 84,
      "complianceStatus": "non-compliant"
    }
  ],
  "worstFile": {
    "fileName": "untagged_report.pdf",
    "nonCompliancePercent": 84
  }
}
```

Why incorrect:
- `issues` is mandatory.

### Incorrect: percentage is a string
```json
{
  "files": [
    {
      "fileName": "untagged_report.pdf",
      "nonCompliancePercent": "84%",
      "complianceStatus": "non-compliant",
      "issues": []
    }
  ],
  "worstFile": {
    "fileName": "untagged_report.pdf",
    "nonCompliancePercent": "84%"
  }
}
```

Why incorrect:
- `nonCompliancePercent` must be a number, not formatted text.

### Incorrect: issue does not name a real standard
```json
{
  "files": [
    {
      "fileName": "missing_alttext.pdf",
      "nonCompliancePercent": 36,
      "complianceStatus": "partially-compliant",
      "issues": [
        {
          "description": "Image issue found.",
          "standard": "Accessibility",
          "category": "General"
        }
      ]
    }
  ],
  "worstFile": {
    "fileName": "missing_alttext.pdf",
    "nonCompliancePercent": 36
  }
}
```

Why incorrect:
- `standard` is too vague.
- `category` is not mapped to a real guideline family.

---

# 2) POST /api/v1/remediate

## What this endpoint must do
For each file:
- return the issues found,
- provide a fix suggestion for each issue,
- avoid fabricating issues for compliant files.

## Required success response
HTTP `200`

```json
{
  "files": [
    {
      "fileName": "missing_alttext.pdf",
      "issues": [
        {
          "description": "Figure elements are missing alternative text.",
          "standard": "WCAG 2.1 SC 1.1.1",
          "fix": "Add meaningful Alt Text to each figure tag so a screen reader can announce the image purpose to non-visual users."
        }
      ]
    },
    {
      "fileName": "accessible_guide.pdf",
      "issues": []
    }
  ]
}
```

## Field-level contract

### Top level
- `files`: required array

### `files[]`
- `fileName`: required string
- `issues`: required array

### `files[].issues[]`
- `description`: required string
- `standard`: required string
- `fix`: required string with substantive remediation guidance

## Behavioral rules
- Fully compliant files must return an empty `issues` array.
- Every issue returned by `/remediate` must include a substantive `fix`.
- The endpoint must read PDF content directly from the supplied locator values, including absolute local file paths.

## Correct variations

### Correct: detailed remediation guidance
```json
{
  "files": [
    {
      "fileName": "partial_form.pdf",
      "issues": [
        {
          "description": "Form fields do not expose labels to assistive technology.",
          "standard": "Section 508 §1194.22(n)",
          "fix": "Add a programmatic label or tooltip to each form field and verify the field name is announced correctly through keyboard navigation."
        }
      ]
    }
  ]
}
```

### Correct: compliant file with empty issues array
```json
{
  "files": [
    {
      "fileName": "accessible_guide.pdf",
      "issues": []
    }
  ]
}
```

## Incorrect variations

### Incorrect: fix missing from an issue
```json
{
  "files": [
    {
      "fileName": "missing_alttext.pdf",
      "issues": [
        {
          "description": "Figure elements are missing alternative text.",
          "standard": "WCAG 2.1 SC 1.1.1"
        }
      ]
    }
  ]
}
```

Why incorrect:
- Every issue surfaced by `/remediate` must include `fix`.

### Incorrect: placeholder fix text
```json
{
  "files": [
    {
      "fileName": "missing_alttext.pdf",
      "issues": [
        {
          "description": "Figure elements are missing alternative text.",
          "standard": "WCAG 2.1 SC 1.1.1",
          "fix": "Fix this issue."
        }
      ]
    }
  ]
}
```

Why incorrect:
- `fix` is too generic and not actionable.

### Incorrect: compliant file still gets fabricated issue
```json
{
  "files": [
    {
      "fileName": "accessible_guide.pdf",
      "issues": [
        {
          "description": "Possible accessibility concern.",
          "standard": "Unknown",
          "fix": "Review manually."
        }
      ]
    }
  ]
}
```

Why incorrect:
- Clean file should not receive fabricated issues.

---

# 3) POST /api/v1/dashboard

## What this endpoint must do
Across the submitted batch:
- count total files scanned,
- count total issues,
- count total fixable issues,
- summarise file status distribution,
- show most common issue types,
- show most frequent standards violated.

## Required success response
HTTP `200`

```json
{
  "totalScanned": 5,
  "totalIssues": 27,
  "totalFixable": 23,
  "complianceBreakdown": [
    { "status": "compliant", "count": 1 },
    { "status": "partially-compliant", "count": 2 },
    { "status": "non-compliant", "count": 2 }
  ],
  "topIssueTypes": [
    { "type": "Missing Alt Text", "count": 8 },
    { "type": "No Tag Tree", "count": 5 },
    { "type": "Missing Document Language", "count": 4 }
  ],
  "standardViolationFrequency": [
    { "standard": "WCAG 2.1", "count": 14 },
    { "standard": "PDF/UA-1", "count": 9 },
    { "standard": "Section 508", "count": 4 }
  ]
}
```

## Field-level contract
- `totalScanned`: required number
- `totalIssues`: required number
- `totalFixable`: required number
- `complianceBreakdown`: required array of `{ status, count }`
- `topIssueTypes`: required array of `{ type, count }`
- `standardViolationFrequency`: required array of `{ standard, count }`

## Arithmetic rules
- `totalScanned` must equal submitted locator count.
- Sum of `complianceBreakdown[].count` must equal `totalScanned`.
- `totalFixable` must be less than or equal to `totalIssues`.
- If a compliant file is present, `complianceBreakdown` must include a `compliant` bucket.
- If issues exist, `topIssueTypes` should not be empty.
- The endpoint must read PDF content directly from the supplied locator values, including absolute local file paths.

## Correct variations

### Correct: clean batch dashboard
```json
{
  "totalScanned": 1,
  "totalIssues": 0,
  "totalFixable": 0,
  "complianceBreakdown": [
    { "status": "compliant", "count": 1 }
  ],
  "topIssueTypes": [],
  "standardViolationFrequency": []
}
```

### Correct: mixed batch dashboard
```json
{
  "totalScanned": 3,
  "totalIssues": 11,
  "totalFixable": 9,
  "complianceBreakdown": [
    { "status": "compliant", "count": 1 },
    { "status": "partially-compliant", "count": 1 },
    { "status": "non-compliant", "count": 1 }
  ],
  "topIssueTypes": [
    { "type": "Missing Alt Text", "count": 4 }
  ],
  "standardViolationFrequency": [
    { "standard": "WCAG 2.1", "count": 6 }
  ]
}
```

## Incorrect variations

### Incorrect: `totalScanned` does not match breakdown total
```json
{
  "totalScanned": 5,
  "totalIssues": 10,
  "totalFixable": 9,
  "complianceBreakdown": [
    { "status": "compliant", "count": 1 },
    { "status": "non-compliant", "count": 2 }
  ],
  "topIssueTypes": [
    { "type": "Missing Alt Text", "count": 3 }
  ],
  "standardViolationFrequency": [
    { "standard": "WCAG 2.1", "count": 4 }
  ]
}
```

Why incorrect:
- Breakdown total is `3`, but `totalScanned` says `5`.

### Incorrect: `totalFixable` exceeds `totalIssues`
```json
{
  "totalScanned": 2,
  "totalIssues": 6,
  "totalFixable": 8,
  "complianceBreakdown": [
    { "status": "partially-compliant", "count": 2 }
  ],
  "topIssueTypes": [
    { "type": "Missing Alt Text", "count": 3 }
  ],
  "standardViolationFrequency": [
    { "standard": "PDF/UA-1", "count": 2 }
  ]
}
```

Why incorrect:
- `totalFixable` cannot be larger than `totalIssues`.

### Incorrect: issue trends have no counts
```json
{
  "totalScanned": 3,
  "totalIssues": 11,
  "totalFixable": 9,
  "complianceBreakdown": [
    { "status": "compliant", "count": 1 },
    { "status": "partially-compliant", "count": 1 },
    { "status": "non-compliant", "count": 1 }
  ],
  "topIssueTypes": [
    { "type": "Missing Alt Text" }
  ],
  "standardViolationFrequency": [
    { "standard": "WCAG 2.1" }
  ]
}
```

Why incorrect:
- Trend entries must carry counts.

---

---

## Minimal Implementation Checklist for Learners
A learner solution is on the right track if it does all of the following:

- accepts a batch of PDF locators,
- reads PDF inputs directly from HTTPS URLs, `file://` URLs, or absolute local file paths,
- treats incoming locator values as actual file sources rather than previously uploaded resource IDs,
- fetches and inspects each file,
- returns per-file issue lists,
- maps issues to named standards and categories,
- computes numeric non-compliance percentages,
- proposes specific remediations,
- produces a batch dashboard with arithmetically consistent totals,
- avoids false positives on compliant files.
