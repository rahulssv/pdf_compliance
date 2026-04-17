# API v2 Specification - PDF Accessibility Compliance Engine

## Overview

API v2 provides comprehensive REST endpoints for PDF accessibility compliance analysis with enhanced features including PII detection, page-level processing, automated remediation, and multi-format reporting.

**Base URL:** `/api/v2`  
**Version:** 2.0.0  
**Protocol:** HTTPS  
**Authentication:** API Key (Header: `X-API-Key`)

---

## Table of Contents

1. [Compliance Analysis Endpoints](#compliance-analysis-endpoints)
2. [PII Detection Endpoints](#pii-detection-endpoints)
3. [Page-Level Processing Endpoints](#page-level-processing-endpoints)
4. [Remediation Endpoints](#remediation-endpoints)
5. [Report Generation Endpoints](#report-generation-endpoints)
6. [AI Validation Endpoints](#ai-validation-endpoints)
7. [Prompt Management Endpoints](#prompt-management-endpoints)
8. [Data Models](#data-models)
9. [Error Handling](#error-handling)
10. [Rate Limiting](#rate-limiting)

---

## Compliance Analysis Endpoints

### POST /api/v2/analyze

Comprehensive PDF accessibility compliance analysis with all enhanced features.

**Request:**

```json
{
  "fileUrl": "string (required)",
  "options": {
    "detectPII": boolean (default: true),
    "piiSensitivity": "low|medium|high" (default: "medium"),
    "pageLevel": boolean (default: false),
    "autoRemediate": boolean (default: false),
    "validateAI": boolean (default: true),
    "generateReport": boolean (default: false),
    "reportFormat": "html|json|pdf|csv|markdown" (default: "json")
  }
}
```

**Response (200 OK):**

```json
{
  "success": true,
  "documentName": "example.pdf",
  "analysisDate": "2026-04-17T01:00:00Z",
  "complianceScore": 85.5,
  "complianceLevel": "partial",
  "wcagLevel": "AA",
  "totalPages": 10,
  "totalIssues": 15,
  "criticalIssues": 2,
  "highIssues": 5,
  "mediumIssues": 6,
  "lowIssues": 2,
  "autoFixable": 5,
  "manualFixesRequired": 10,
  "issues": [
    {
      "id": "ISSUE-001",
      "category": "alt_text",
      "severity": "high",
      "wcagCriterion": "1.1.1",
      "description": "Image missing alternative text",
      "location": "Page 3",
      "impact": "Screen reader users cannot access image content",
      "remediationComplexity": "easy",
      "estimatedTime": "5 minutes",
      "autoFixable": false
    }
  ],
  "recommendations": [
    {
      "priority": "high",
      "action": "Add alternative text to all images",
      "benefit": "Improves accessibility for screen reader users"
    }
  ],
  "piiDetected": {
    "totalInstances": 3,
    "types": ["email", "phone", "ssn"],
    "byPage": {
      "1": ["email"],
      "3": ["phone", "ssn"]
    }
  },
  "pageAnalyses": [
    {
      "pageNumber": 1,
      "pageScore": 90.0,
      "issues": 1,
      "piiDetected": ["email"]
    }
  ],
  "remediationResults": {
    "totalIssues": 15,
    "fixedIssues": 5,
    "manualIssues": 10,
    "actions": [
      {
        "issueType": "missing_language",
        "actionType": "automated",
        "status": "completed",
        "description": "Added document language metadata"
      }
    ]
  },
  "validationMetrics": {
    "overallConfidence": 92.5,
    "confidenceLevel": "very_high",
    "layerScores": {
      "rule_based": 95.0,
      "pattern_matching": 90.0,
      "consistency": 92.0,
      "knowledge_base": 91.0,
      "ensemble": 94.0
    },
    "recommendation": "Results are highly reliable"
  }
}
```

**Error Responses:**

- `400 Bad Request`: Invalid request parameters
- `404 Not Found`: File URL not accessible
- `500 Internal Server Error`: Processing error

---

### POST /api/v2/analyze/batch

Batch analysis of multiple PDF documents.

**Request:**

```json
{
  "fileUrls": ["string"],
  "options": {
    "detectPII": boolean,
    "pageLevel": boolean,
    "autoRemediate": boolean,
    "validateAI": boolean
  }
}
```

**Response (200 OK):**

```json
{
  "success": true,
  "totalDocuments": 5,
  "completedSuccessfully": 4,
  "failed": 1,
  "results": [
    {
      "fileUrl": "https://example.com/doc1.pdf",
      "success": true,
      "complianceScore": 85.5,
      "totalIssues": 15
    }
  ],
  "summary": {
    "averageComplianceScore": 82.3,
    "totalIssues": 75,
    "criticalIssues": 10,
    "piiDetected": 15
  }
}
```

---

## PII Detection Endpoints

### POST /api/v2/pii/detect

Detect Personally Identifiable Information in document content.

**Request:**

```json
{
  "fileUrl": "string (required)",
  "sensitivity": "low|medium|high" (default: "medium"),
  "redact": boolean (default: false),
  "returnDetails": boolean (default: false)
}
```

**Response (200 OK):**

```json
{
  "success": true,
  "totalInstances": 8,
  "types": ["email", "phone", "ssn", "credit_card"],
  "byCategory": {
    "financial": 2,
    "personal": 4,
    "medical": 0,
    "government": 2,
    "technical": 0
  },
  "byPage": {
    "1": ["email", "phone"],
    "3": ["ssn", "credit_card"]
  },
  "detections": [
    {
      "type": "email",
      "category": "personal",
      "severity": "medium",
      "original": "user@example.com",
      "masked": "u***@example.com",
      "location": "Page 1, Line 5",
      "confidence": 0.98
    }
  ],
  "redactedContent": "string (if redact=true)"
}
```

---

### POST /api/v2/pii/redact

Redact detected PII from document.

**Request:**

```json
{
  "fileUrl": "string (required)",
  "piiTypes": ["email", "phone", "ssn"],
  "redactionStyle": "mask|remove|replace" (default: "mask"),
  "outputFormat": "pdf|text" (default: "pdf")
}
```

**Response (200 OK):**

Returns redacted document as binary data or JSON with redacted text.

---

## Page-Level Processing Endpoints

### POST /api/v2/pages/analyze

Analyze PDF document page by page with granular insights.

**Request:**

```json
{
  "fileUrl": "string (required)",
  "pageRange": {
    "start": 1,
    "end": 10
  },
  "options": {
    "detectPII": boolean (default: true),
    "extractText": boolean (default: true),
    "analyzeImages": boolean (default: true)
  }
}
```

**Response (200 OK):**

```json
{
  "success": true,
  "totalPages": 10,
  "analyzedPages": 10,
  "pages": [
    {
      "pageNumber": 1,
      "pageScore": 90.0,
      "complianceLevel": "full",
      "issues": [
        {
          "type": "structure",
          "severity": "low",
          "description": "Minor heading hierarchy issue"
        }
      ],
      "metrics": {
        "readabilityScore": 85.0,
        "structureScore": 92.0,
        "accessibilityScore": 90.0
      },
      "piiDetected": ["email"],
      "textContent": "Page text content...",
      "imageCount": 2,
      "formFieldCount": 0
    }
  ],
  "summary": {
    "averagePageScore": 88.5,
    "totalIssues": 15,
    "pagesWithPII": 3,
    "pagesWithImages": 8
  }
}
```

---

### POST /api/v2/pages/extract

Extract specific page(s) from PDF document.

**Request:**

```json
{
  "fileUrl": "string (required)",
  "pageNumbers": [1, 3, 5],
  "outputFormat": "pdf|text|json" (default: "pdf"),
  "includeMetadata": boolean (default: true)
}
```

**Response (200 OK):**

Returns extracted pages as binary PDF or JSON with page content.

---

### GET /api/v2/pages/{pageNumber}/content

Get content of a specific page.

**Path Parameters:**
- `pageNumber`: Page number (1-indexed)

**Query Parameters:**
- `fileUrl`: URL of the PDF document
- `format`: `text|json` (default: `json`)

**Response (200 OK):**

```json
{
  "success": true,
  "pageNumber": 1,
  "content": {
    "text": "Page text content...",
    "images": 2,
    "forms": 0,
    "links": 3
  },
  "metadata": {
    "width": 612,
    "height": 792,
    "rotation": 0
  }
}
```

---

## Remediation Endpoints

### POST /api/v2/remediate/auto

Automatically remediate fixable accessibility issues.

**Request:**

```json
{
  "fileUrl": "string (required)",
  "issues": [
    {
      "id": "ISSUE-001",
      "type": "missing_language",
      "severity": "high"
    }
  ],
  "options": {
    "dryRun": boolean (default: false),
    "returnModifiedPDF": boolean (default: true)
  }
}
```

**Response (200 OK):**

```json
{
  "success": true,
  "totalIssues": 15,
  "fixedIssues": 5,
  "manualIssues": 10,
  "results": [
    {
      "issueId": "ISSUE-001",
      "issueType": "missing_language",
      "actionType": "automated",
      "status": "completed",
      "description": "Added document language metadata (en-US)",
      "timestamp": "2026-04-17T01:00:00Z"
    }
  ],
  "modifiedPDF": "base64_encoded_pdf (if returnModifiedPDF=true)",
  "summary": {
    "autoRemediationRate": 33.3,
    "estimatedTimeSaved": "25 minutes",
    "remainingManualWork": "50 minutes"
  }
}
```

---

### POST /api/v2/remediate/guidance

Get detailed step-by-step remediation guidance for manual fixes.

**Request:**

```json
{
  "issueType": "missing_alt_text",
  "issueDescription": "Image on page 3 missing alternative text",
  "userSkillLevel": "beginner|intermediate|advanced" (default: "intermediate"),
  "preferredTools": ["Adobe Acrobat Pro", "CommonLook"]
}
```

**Response (200 OK):**

```json
{
  "success": true,
  "issueType": "missing_alt_text",
  "complexity": "easy",
  "estimatedTime": "5 minutes per image",
  "difficulty": "easy",
  "priority": "high",
  "steps": [
    {
      "stepNumber": 1,
      "action": "Open PDF in Adobe Acrobat Pro",
      "details": "File > Open > Select your PDF",
      "tool": "Adobe Acrobat Pro",
      "screenshotAvailable": true
    },
    {
      "stepNumber": 2,
      "action": "Access the Tags panel",
      "details": "View > Show/Hide > Navigation Panes > Tags",
      "tool": "Adobe Acrobat Pro",
      "screenshotAvailable": true
    }
  ],
  "verification": {
    "method": "Use Accessibility Checker",
    "expectedResult": "No 'Figure' elements without alternative text",
    "validationTool": "Adobe Acrobat Pro Accessibility Checker"
  },
  "bestPractices": [
    "Describe the content and function of the image",
    "Keep alt text concise (under 150 characters)",
    "Don't start with 'Image of' or 'Picture of'"
  ],
  "commonMistakes": [
    "Using filename as alt text",
    "Leaving alt text empty",
    "Being too verbose"
  ],
  "resources": [
    {
      "title": "WebAIM: Alternative Text",
      "url": "https://webaim.org/techniques/alttext/",
      "type": "documentation"
    }
  ]
}
```

---

### GET /api/v2/remediate/status/{jobId}

Get status of a remediation job.

**Path Parameters:**
- `jobId`: Remediation job identifier

**Response (200 OK):**

```json
{
  "success": true,
  "jobId": "rem_abc123",
  "status": "in_progress|completed|failed",
  "progress": 65.5,
  "startedAt": "2026-04-17T01:00:00Z",
  "estimatedCompletion": "2026-04-17T01:05:00Z",
  "issuesProcessed": 10,
  "issuesRemaining": 5
}
```

---

## Report Generation Endpoints

### POST /api/v2/reports/generate

Generate comprehensive compliance report in specified format.

**Request:**

```json
{
  "analysisData": {
    "documentName": "example.pdf",
    "complianceScore": 85.5,
    "issues": [],
    "recommendations": []
  },
  "format": "pdf|html|json|csv|markdown" (default: "html"),
  "sections": [
    "executive_summary",
    "compliance_overview",
    "issue_details",
    "remediation_plan",
    "page_analysis",
    "recommendations"
  ],
  "options": {
    "includeCharts": boolean (default: true),
    "includePageDetails": boolean (default: true),
    "includePIIDetails": boolean (default: false),
    "branding": {
      "companyName": "Your Company",
      "logoUrl": "https://example.com/logo.png",
      "primaryColor": "#2563eb"
    },
    "customCSS": "string (optional)"
  }
}
```

**Response (200 OK):**

Returns generated report as binary data (PDF/HTML) or JSON/CSV.

**Content-Type:**
- PDF: `application/pdf`
- HTML: `text/html`
- JSON: `application/json`
- CSV: `text/csv`
- Markdown: `text/markdown`

---

### POST /api/v2/reports/executive-summary

Generate concise executive summary report.

**Request:**

```json
{
  "analysisData": {
    "documentName": "example.pdf",
    "complianceScore": 85.5,
    "totalIssues": 15,
    "criticalIssues": 2
  },
  "format": "json|pdf" (default: "json")
}
```

**Response (200 OK):**

```json
{
  "success": true,
  "summary": {
    "documentName": "example.pdf",
    "analysisDate": "2026-04-17T01:00:00Z",
    "complianceScore": 85.5,
    "complianceLevel": "partial",
    "wcagLevel": "AA",
    "totalIssues": 15,
    "criticalIssues": 2,
    "autoFixable": 5,
    "manualFixesRequired": 10,
    "topRecommendations": [
      "Add alternative text to images",
      "Fix document structure",
      "Add form field labels"
    ],
    "estimatedRemediationTime": "2 hours"
  }
}
```

---

## AI Validation Endpoints

### POST /api/v2/validation/check

Validate AI-generated analysis results with confidence scoring.

**Request:**

```json
{
  "analysisResult": {
    "complianceScore": 85.5,
    "issues": [],
    "recommendations": []
  },
  "context": {
    "fileUrl": "https://example.com/doc.pdf",
    "analysisType": "full"
  },
  "validationOptions": {
    "enableAllLayers": boolean (default: true),
    "confidenceThreshold": 60.0,
    "requireFallback": boolean (default: false)
  }
}
```

**Response (200 OK):**

```json
{
  "success": true,
  "overallConfidence": 92.5,
  "confidenceLevel": "very_high",
  "layerScores": {
    "rule_based": {
      "score": 95.0,
      "weight": 0.25,
      "details": "All WCAG criteria properly referenced"
    },
    "pattern_matching": {
      "score": 90.0,
      "weight": 0.20,
      "details": "Output format matches expected schema"
    },
    "consistency": {
      "score": 92.0,
      "weight": 0.25,
      "details": "Results consistent with fallback analysis"
    },
    "knowledge_base": {
      "score": 91.0,
      "weight": 0.15,
      "details": "Matches known patterns for similar documents"
    },
    "ensemble": {
      "score": 94.0,
      "weight": 0.15,
      "details": "High agreement across multiple generations"
    }
  },
  "recommendation": "Results are highly reliable - proceed with confidence",
  "fallbackRecommended": false,
  "issues": [],
  "metadata": {
    "validationTime": "1.2s",
    "layersUsed": 5
  }
}
```

---

### GET /api/v2/validation/metrics

Get validation performance metrics.

**Query Parameters:**
- `timeRange`: `day|week|month|all` (default: `week`)

**Response (200 OK):**

```json
{
  "success": true,
  "timeRange": "week",
  "metrics": {
    "totalValidations": 1250,
    "averageConfidence": 89.5,
    "highConfidenceRate": 85.2,
    "fallbackRate": 8.5,
    "averageValidationTime": "1.5s"
  },
  "confidenceDistribution": {
    "very_high": 65.0,
    "high": 20.2,
    "medium": 10.3,
    "low": 3.5,
    "very_low": 1.0
  }
}
```

---

## Prompt Management Endpoints

### GET /api/v2/prompts/performance

Get performance metrics for AI prompts.

**Query Parameters:**
- `promptName`: Specific prompt name (optional)
- `timeRange`: `day|week|month|all` (default: `week`)

**Response (200 OK):**

```json
{
  "success": true,
  "promptName": "compliance_analysis",
  "version": "1.3.0",
  "status": "active",
  "metrics": {
    "totalUses": 5000,
    "successfulUses": 4850,
    "failedUses": 150,
    "successRate": 97.0,
    "avgResponseTime": 3.2,
    "avgConfidenceScore": 91.5,
    "avgValidationScore": 89.0,
    "performanceTrend": "improving"
  },
  "recommendations": [
    "Performance is excellent - continue monitoring"
  ]
}
```

---

### GET /api/v2/prompts/versions

List all versions of a prompt.

**Query Parameters:**
- `promptName`: Prompt name (required)

**Response (200 OK):**

```json
{
  "success": true,
  "promptName": "compliance_analysis",
  "versions": [
    {
      "version": "1.3.0",
      "status": "active",
      "createdAt": "2026-04-17T00:00:00Z",
      "modifiedAt": "2026-04-17T00:00:00Z",
      "performance": {
        "successRate": 97.0,
        "avgConfidence": 91.5
      }
    },
    {
      "version": "1.2.0",
      "status": "deprecated",
      "createdAt": "2026-04-10T00:00:00Z",
      "performance": {
        "successRate": 94.0,
        "avgConfidence": 88.0
      }
    }
  ]
}
```

---

## Data Models

### ComplianceAnalysisResult

```typescript
interface ComplianceAnalysisResult {
  success: boolean;
  documentName: string;
  analysisDate: string; // ISO 8601
  complianceScore: number; // 0-100
  complianceLevel: "none" | "partial" | "full";
  wcagLevel: "A" | "AA" | "AAA" | "non-compliant";
  totalPages: number;
  totalIssues: number;
  criticalIssues: number;
  highIssues: number;
  mediumIssues: number;
  lowIssues: number;
  autoFixable: number;
  manualFixesRequired: number;
  issues: Issue[];
  recommendations: Recommendation[];
  piiDetected?: PIIDetectionResult;
  pageAnalyses?: PageAnalysis[];
  remediationResults?: RemediationResult;
  validationMetrics?: ValidationMetrics;
}
```

### Issue

```typescript
interface Issue {
  id: string;
  category: string;
  severity: "critical" | "high" | "medium" | "low";
  wcagCriterion: string;
  description: string;
  location: string;
  impact: string;
  remediationComplexity: "easy" | "medium" | "hard";
  estimatedTime: string;
  autoFixable: boolean;
}
```

### PIIDetectionResult

```typescript
interface PIIDetectionResult {
  totalInstances: number;
  types: string[];
  byCategory: Record<string, number>;
  byPage: Record<number, string[]>;
  detections?: PIIDetection[];
}
```

### ValidationMetrics

```typescript
interface ValidationMetrics {
  overallConfidence: number; // 0-100
  confidenceLevel: "very_high" | "high" | "medium" | "low" | "very_low";
  layerScores: Record<string, LayerScore>;
  recommendation: string;
  fallbackRecommended: boolean;
}
```

---

## Error Handling

All endpoints return consistent error responses:

```json
{
  "success": false,
  "error": {
    "code": "ERROR_CODE",
    "message": "Human-readable error message",
    "details": "Additional error details",
    "timestamp": "2026-04-17T01:00:00Z"
  }
}
```

### Error Codes

- `INVALID_REQUEST`: Invalid request parameters
- `FILE_NOT_FOUND`: File URL not accessible
- `PROCESSING_ERROR`: Error during document processing
- `PII_DETECTION_ERROR`: Error in PII detection
- `REMEDIATION_ERROR`: Error during remediation
- `REPORT_GENERATION_ERROR`: Error generating report
- `VALIDATION_ERROR`: Error during AI validation
- `RATE_LIMIT_EXCEEDED`: Too many requests
- `INTERNAL_ERROR`: Internal server error

---

## Rate Limiting

API v2 implements rate limiting to ensure fair usage:

- **Standard Tier:** 100 requests/minute
- **Premium Tier:** 500 requests/minute
- **Enterprise Tier:** Unlimited

Rate limit headers included in all responses:

```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1713312000
```

When rate limit is exceeded, returns `429 Too Many Requests`:

```json
{
  "success": false,
  "error": {
    "code": "RATE_LIMIT_EXCEEDED",
    "message": "Rate limit exceeded. Please try again later.",
    "retryAfter": 60
  }
}
```

---

## Authentication

All API requests require authentication via API key:

```
X-API-Key: your_api_key_here
```

Unauthorized requests return `401 Unauthorized`:

```json
{
  "success": false,
  "error": {
    "code": "UNAUTHORIZED",
    "message": "Invalid or missing API key"
  }
}
```

---

## Versioning

API versioning is handled via URL path:

- Current: `/api/v2`
- Legacy: `/api/v1` (deprecated)

Version deprecation notices are provided 6 months in advance via response headers:

```
X-API-Deprecation: true
X-API-Sunset: 2026-10-17T00:00:00Z
X-API-Replacement: /api/v2
```

---

## Support

For API support and questions:

- Documentation: https://docs.example.com/api/v2
- Support Email: api-support@example.com
- Status Page: https://status.example.com

---

*API Specification Version: 2.0.0*  
*Last Updated: April 17, 2026*