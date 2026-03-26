# FraudLens API Contract

> **This is the single source of truth for all API communication.**
> Both Nisarg (backend) and Deep (frontend) must agree on any changes.
> Any modification requires a PR that updates this file FIRST.

**Base URL:** `http://localhost:8000/api/v1`
**Auth:** API key in header: `X-API-Key: <key>`
**Format:** All requests and responses are JSON
**Dates:** ISO 8601 format (e.g., `2026-03-23T14:30:00Z`)
**IDs:** UUID v4 format

---

## Common Types

```typescript
// Decision type — used across multiple endpoints
type Decision = "APPROVE" | "REVIEW" | "BLOCK";

// Pagination — standard across all list endpoints
interface PaginationParams {
  page: number;       // default: 1
  page_size: number;  // default: 50, max: 200
}

interface PaginatedResponse<T> {
  data: T[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

// SHAP feature — used in scoring and explanation endpoints
interface ShapFeature {
  feature: string;     // feature name (e.g., "geo_velocity")
  impact: number;      // positive = pushes toward fraud, negative = pushes away
  value: number;       // actual feature value for this transaction
}
```

---

## 1. Score Transaction

**`POST /transactions/score`**

Score a single transaction in real-time.

### Request

```json
{
  "user_id": "550e8400-e29b-41d4-a716-446655440000",
  "amount": 1249.99,
  "currency": "CAD",
  "merchant_name": "Best Buy",
  "merchant_category": "electronics",
  "card_type": "visa",
  "latitude": 43.7315,
  "longitude": -79.7624,
  "country_code": "CA",
  "is_online": false
}
```

### Response (200)

```json
{
  "transaction_id": "7c9e6679-7425-40de-944b-e07fc1f90ae7",
  "fraud_score": 0.8734,
  "decision": "BLOCK",
  "model_scores": {
    "lightgbm": 0.9102,
    "autoencoder": 0.8521,
    "isolation_forest": 0.7893
  },
  "top_shap_features": [
    { "feature": "geo_velocity", "impact": 0.28, "value": 9600.5 },
    { "feature": "amount_vs_avg_ratio", "impact": 0.19, "value": 12.3 },
    { "feature": "merchant_frequency", "impact": 0.12, "value": 0.0 },
    { "feature": "hour_deviation", "impact": 0.08, "value": 3.78 },
    { "feature": "unique_countries_24h", "impact": 0.07, "value": 3 }
  ],
  "scoring_latency_ms": 23,
  "model_version": "v1.0.0",
  "created_at": "2026-03-23T14:30:00Z"
}
```

### Error (422)

```json
{
  "detail": [
    {
      "loc": ["body", "amount"],
      "msg": "value is not a valid float",
      "type": "type_error.float"
    }
  ]
}
```

---

## 2. List Transactions

**`GET /transactions`**

### Query Parameters

| Param | Type | Default | Description |
|-------|------|---------|-------------|
| `page` | int | 1 | Page number |
| `page_size` | int | 50 | Items per page (max 200) |
| `decision` | string | null | Filter: APPROVE, REVIEW, BLOCK |
| `min_score` | float | null | Minimum fraud score |
| `max_score` | float | null | Maximum fraud score |
| `merchant_category` | string | null | Filter by category |
| `start_date` | string | null | ISO 8601 start date |
| `end_date` | string | null | ISO 8601 end date |
| `sort_by` | string | "created_at" | Sort field |
| `sort_order` | string | "desc" | "asc" or "desc" |

### Response (200)

```json
{
  "data": [
    {
      "transaction_id": "7c9e6679-7425-40de-944b-e07fc1f90ae7",
      "user_id": "550e8400-e29b-41d4-a716-446655440000",
      "user_name": "Sarah Chen",
      "amount": 1249.99,
      "currency": "CAD",
      "merchant_name": "Best Buy",
      "merchant_category": "electronics",
      "card_type": "visa",
      "latitude": 43.7315,
      "longitude": -79.7624,
      "country_code": "CA",
      "is_online": false,
      "fraud_score": 0.8734,
      "decision": "BLOCK",
      "is_fraud": null,
      "scoring_latency_ms": 23,
      "created_at": "2026-03-23T14:30:00Z"
    }
  ],
  "total": 15234,
  "page": 1,
  "page_size": 50,
  "total_pages": 305
}
```

---

## 3. Get Transaction Detail

**`GET /transactions/{transaction_id}`**

### Response (200)

```json
{
  "transaction_id": "7c9e6679-7425-40de-944b-e07fc1f90ae7",
  "user_id": "550e8400-e29b-41d4-a716-446655440000",
  "user_name": "Sarah Chen",
  "amount": 1249.99,
  "currency": "CAD",
  "merchant_name": "Best Buy",
  "merchant_category": "electronics",
  "card_type": "visa",
  "latitude": 43.7315,
  "longitude": -79.7624,
  "country_code": "CA",
  "is_online": false,
  "fraud_score": 0.8734,
  "decision": "BLOCK",
  "is_fraud": null,
  "model_scores": {
    "lightgbm": 0.9102,
    "autoencoder": 0.8521,
    "isolation_forest": 0.7893
  },
  "top_shap_features": [
    { "feature": "geo_velocity", "impact": 0.28, "value": 9600.5 },
    { "feature": "amount_vs_avg_ratio", "impact": 0.19, "value": 12.3 },
    { "feature": "merchant_frequency", "impact": 0.12, "value": 0.0 },
    { "feature": "hour_deviation", "impact": 0.08, "value": 3.78 },
    { "feature": "unique_countries_24h", "impact": 0.07, "value": 3 }
  ],
  "model_version": "v1.0.0",
  "scoring_latency_ms": 23,
  "created_at": "2026-03-23T14:30:00Z",
  "user_profile": {
    "home_city": "Brampton, ON",
    "account_age_days": 730,
    "avg_transaction_amount": 87.50,
    "risk_profile": "low"
  },
  "recent_transactions": [
    {
      "transaction_id": "abc123",
      "amount": 45.00,
      "merchant_name": "Tim Hortons",
      "fraud_score": 0.02,
      "decision": "APPROVE",
      "created_at": "2026-03-23T08:15:00Z"
    }
  ]
}
```

---

## 4. Get SHAP Explanation

**`GET /transactions/{transaction_id}/explain`**

### Response (200)

```json
{
  "transaction_id": "7c9e6679-7425-40de-944b-e07fc1f90ae7",
  "fraud_score": 0.8734,
  "base_score": 0.0043,
  "shap_features": [
    { "feature": "geo_velocity", "impact": 0.28, "value": 9600.5, "description": "Moved 2,400km in 15 minutes (impossible)" },
    { "feature": "amount_vs_avg_ratio", "impact": 0.19, "value": 12.3, "description": "Transaction is 12.3x the user average" },
    { "feature": "merchant_frequency", "impact": 0.12, "value": 0.0, "description": "First time at this merchant" },
    { "feature": "hour_deviation", "impact": 0.08, "value": 3.78, "description": "Transaction at 3:47 AM, user never transacts after midnight" },
    { "feature": "unique_countries_24h", "impact": 0.07, "value": 3, "description": "3 different countries in 24 hours" },
    { "feature": "txn_count_1h", "impact": 0.05, "value": 7, "description": "7 transactions in the last hour (avg: 1.2)" },
    { "feature": "amount_zscore", "impact": 0.04, "value": 4.2, "description": "Amount is 4.2 standard deviations above mean" },
    { "feature": "card_age_days", "impact": -0.02, "value": 365, "description": "Card is 1 year old (established)" },
    { "feature": "account_age_days", "impact": -0.03, "value": 730, "description": "Account is 2 years old (trusted)" }
  ],
  "model_version": "v1.0.0"
}
```

---

## 5. Submit Analyst Feedback

**`POST /feedback`**

### Request

```json
{
  "transaction_id": "7c9e6679-7425-40de-944b-e07fc1f90ae7",
  "verdict": "confirmed_fraud",
  "notes": "Card cloning attack confirmed. User contacted and card replaced."
}
```

**Verdict options:** `confirmed_fraud` | `false_alarm` | `escalated`

### Response (201)

```json
{
  "feedback_id": "9b1deb4d-3b7d-4bad-9bdd-2b0d7b3dcb6d",
  "transaction_id": "7c9e6679-7425-40de-944b-e07fc1f90ae7",
  "verdict": "confirmed_fraud",
  "reviewed_at": "2026-03-23T15:00:00Z"
}
```

---

## 6. Analytics Summary

**`GET /analytics/summary`**

### Query Parameters

| Param | Type | Default | Description |
|-------|------|---------|-------------|
| `period` | string | "24h" | Time period: 1h, 24h, 7d, 30d |

### Response (200)

```json
{
  "period": "24h",
  "total_transactions": 245892,
  "total_flagged": 1234,
  "total_blocked": 567,
  "fraud_rate": 0.0023,
  "false_positive_rate": 0.12,
  "avg_scoring_latency_ms": 23,
  "p95_scoring_latency_ms": 41,
  "p99_scoring_latency_ms": 67,
  "transactions_per_second": 2845,
  "model_version": "v1.0.0",
  "decision_breakdown": {
    "approve": 244091,
    "review": 1234,
    "block": 567
  },
  "top_fraud_categories": [
    { "category": "electronics", "count": 189, "percentage": 0.334 },
    { "category": "travel", "count": 134, "percentage": 0.236 },
    { "category": "luxury", "count": 98, "percentage": 0.173 }
  ]
}
```

---

## 7. Analytics Trends

**`GET /analytics/trends`**

### Query Parameters

| Param | Type | Default | Description |
|-------|------|---------|-------------|
| `period` | string | "7d" | Time range: 24h, 7d, 30d |
| `interval` | string | "1h" | Data point interval: 15m, 1h, 1d |

### Response (200)

```json
{
  "period": "7d",
  "interval": "1h",
  "data_points": [
    {
      "timestamp": "2026-03-23T14:00:00Z",
      "total_transactions": 10234,
      "fraud_count": 23,
      "fraud_rate": 0.0022,
      "avg_score": 0.12,
      "avg_latency_ms": 22,
      "blocked_count": 12,
      "review_count": 34
    }
  ]
}
```

---

## 8. Geographic Fraud Data

**`GET /analytics/geo`**

### Query Parameters

| Param | Type | Default | Description |
|-------|------|---------|-------------|
| `period` | string | "24h" | Time range |
| `min_score` | float | 0.5 | Minimum fraud score to include |

### Response (200)

```json
{
  "period": "24h",
  "fraud_locations": [
    {
      "latitude": 43.7315,
      "longitude": -79.7624,
      "fraud_score": 0.87,
      "transaction_id": "7c9e6679-7425-40de-944b-e07fc1f90ae7",
      "amount": 1249.99,
      "merchant_name": "Best Buy",
      "decision": "BLOCK",
      "created_at": "2026-03-23T14:30:00Z"
    }
  ],
  "heatmap_data": [
    { "latitude": 43.65, "longitude": -79.38, "weight": 15 },
    { "latitude": 45.50, "longitude": -73.56, "weight": 8 }
  ]
}
```

---

## 9. Alerts

**`GET /alerts`**

### Query Parameters

| Param | Type | Default | Description |
|-------|------|---------|-------------|
| `status` | string | "pending" | pending, acknowledged, resolved |
| `page` | int | 1 | Page number |
| `page_size` | int | 20 | Items per page |

### Response (200)

```json
{
  "data": [
    {
      "alert_id": "alert-001",
      "transaction_id": "7c9e6679-7425-40de-944b-e07fc1f90ae7",
      "fraud_score": 0.8734,
      "decision": "BLOCK",
      "amount": 1249.99,
      "merchant_name": "Best Buy",
      "user_name": "Sarah Chen",
      "status": "pending",
      "priority": "critical",
      "created_at": "2026-03-23T14:30:00Z"
    }
  ],
  "total": 23,
  "page": 1,
  "page_size": 20,
  "total_pages": 2
}
```

**`PATCH /alerts/{alert_id}`**

### Request

```json
{
  "status": "acknowledged"
}
```

---

## 10. Model Health

**`GET /model/health`**

### Response (200)

```json
{
  "current_version": "v1.0.0",
  "deployed_at": "2026-03-20T10:00:00Z",
  "metrics": {
    "auroc": 0.9234,
    "precision": 0.8567,
    "recall": 0.7892,
    "f1_score": 0.8216,
    "false_positive_rate": 0.12
  },
  "training_data_size": 590540,
  "last_retrained": "2026-03-20T08:00:00Z",
  "inference_stats": {
    "avg_latency_ms": 23,
    "p95_latency_ms": 41,
    "p99_latency_ms": 67,
    "total_scored_today": 245892
  }
}
```

---

## 11. WebSocket: Live Transactions

**`WS /ws/transactions`**

Server pushes scored transactions in real-time.

### Message Format (Server → Client)

```json
{
  "type": "transaction",
  "data": {
    "transaction_id": "7c9e6679-7425-40de-944b-e07fc1f90ae7",
    "user_name": "Sarah Chen",
    "amount": 1249.99,
    "merchant_name": "Best Buy",
    "merchant_category": "electronics",
    "fraud_score": 0.8734,
    "decision": "BLOCK",
    "country_code": "CA",
    "created_at": "2026-03-23T14:30:00Z"
  }
}
```

---

## 12. WebSocket: Live Alerts

**`WS /ws/alerts`**

Server pushes new fraud alerts.

### Message Format (Server → Client)

```json
{
  "type": "alert",
  "data": {
    "alert_id": "alert-001",
    "transaction_id": "7c9e6679-7425-40de-944b-e07fc1f90ae7",
    "fraud_score": 0.8734,
    "decision": "BLOCK",
    "amount": 1249.99,
    "merchant_name": "Best Buy",
    "user_name": "Sarah Chen",
    "priority": "critical",
    "created_at": "2026-03-23T14:30:00Z"
  }
}
```

---

## 13. Health Check

**`GET /health`** (No auth required)

### Response (200)

```json
{
  "status": "healthy",
  "version": "1.0.0",
  "services": {
    "database": "connected",
    "redis": "connected",
    "ml_model": "loaded"
  },
  "uptime_seconds": 86400
}
```

---

## Changelog

| Date | Change | Author |
|------|--------|--------|
| 2026-03-23 | Initial API contract created | Nisarg & Deep |