# Story 3.4: Confidence Scoring & Routing

**Epic:** 3. RAG Q&A Engine  
**Status:** drafted  
**Assigned to:** TBD  
**Blocked by:** 3-3-citation-generation

## Story

As a System,  
I want to calculate a confidence score for each answer,  
so that low-confidence answers route to HITL review.

## Acceptance Criteria

### Confidence Scoring

-   [ ] Confidence score is calculated for every AI answer (0-100%)
-   [ ] Score formula combines three factors:
    -   [ ] Retrieval confidence: Max similarity of retrieved chunks (40% weight)
    -   [ ] Generation confidence: LLM's self-reported confidence (30% weight)
    -   [ ] Context coverage: % of answer supported by context (30% weight)
-   [ ] Score is returned with every answer
-   [ ] Score is visible to agents in HITL queue

### High Confidence Routing

-   [ ] When confidence >= bot's threshold (default 80%):
    -   [ ] Answer can auto-send (if enabled in bot settings)
    -   [ ] Answer is sent directly to end-user
    -   [ ] Marked as "Auto-responded" in analytics

### Low Confidence Routing

-   [ ] When confidence < threshold:
    -   [ ] Answer routes to HITL queue
    -   [ ] End-user sees: "I'm checking with the team..."
    -   [ ] End-user receives notification when verified answer arrives
    -   [ ] Agent reviews answer before sending
    -   [ ] Agent can approve, edit, or reject

### Confidence Transparency

-   [ ] Score reflects actual confidence (not artificially high/low)
-   [ ] Score is calibrated: 80% = answer likely correct
-   [ ] Agents can override auto-send threshold if needed
-   [ ] Confidence is explained in agent UI: "Why this score?"

### Edge Cases

-   [ ] No context (empty search): confidence = 0%
-   [ ] Ambiguous context (conflicting chunks): confidence < 50%
-   [ ] Out-of-domain query: confidence = 0%
-   [ ] Verified KB match: confidence = 95% + (auto-send always)

## Technical Specifications

### Confidence Formula

```
confidence_score = (
  (retrieval_confidence * 0.4) +
  (generation_confidence * 0.3) +
  (context_coverage * 0.3)
) * 100
```

**Component 1: Retrieval Confidence (40% weight)**

```
retrieval_confidence = max(similarity_scores)

# Example:
# Top 5 chunks: [0.89, 0.82, 0.71, 0.55, 0.42]
# retrieval_confidence = 0.89
```

Rationale: If best matching chunk has high similarity, answer likely correct.

**Component 2: Generation Confidence (30% weight)**

Extract LLM's self-reported confidence via prompt:

```
After generating answer, ask LLM:
"On a scale of 0-100%, how confident are you in this answer?"
```

Or infer from response structure:

-   If answer starts with "Yes," / "Definitely,": 0.9
-   If answer starts with "Based on...", "According to...": 0.75
-   If answer includes "I'm not sure", "This is unclear": 0.3
-   If answer is "I don't have information": 0.0

Rationale: LLM can reflect on its own answer quality.

**Component 3: Context Coverage (30% weight)**

Measure % of answer supported by context:

```
context_coverage = (cited_sentences / total_sentences)

# Example:
# Answer has 5 sentences, 4 are cited
# context_coverage = 4/5 = 0.8
```

Rationale: Unsupported sentences indicate synthesis/hallucination.

### Confidence Thresholds

| Range   | Meaning    | Action                                           |
| ------- | ---------- | ------------------------------------------------ |
| 90-100% | Excellent  | Auto-send (if enabled)                           |
| 80-90%  | Good       | Auto-send or HITL (configurable)                 |
| 60-80%  | Fair       | HITL review                                      |
| 40-60%  | Uncertain  | HITL review                                      |
| 0-40%   | Poor       | HITL review + warning                            |
| 0%      | No context | Route to HITL, show "checking with team" message |

### Verified KB Handling

When answer comes from Verified KB:

-   Confidence = 95% (human-verified)
-   Always auto-send (no HITL needed)
-   Skip confidence calculation (assume high confidence)
-   Mark as "Verified" in response

### Database Schema

```sql
CREATE TABLE confidence_logs (
  id UUID PRIMARY KEY,
  bot_id UUID NOT NULL REFERENCES bots(id),
  tenant_id UUID NOT NULL REFERENCES tenants(id),
  query_id UUID NOT NULL,

  -- Components
  retrieval_confidence DECIMAL(3,2),  -- 0.00-1.00
  generation_confidence DECIMAL(3,2),
  context_coverage DECIMAL(3,2),

  -- Result
  overall_confidence DECIMAL(3,2),
  routing_decision VARCHAR(20),  -- 'auto_send' or 'hitl'

  -- Tracking
  created_at TIMESTAMP,
  response_id UUID REFERENCES responses(id),

  INDEX idx_routing ON (bot_id, routing_decision),
  INDEX idx_overall ON overall_confidence
);
```

## API Contract

### Endpoint

```
POST /api/bots/{bot_id}/query
```

### Request

```json
{
    "query": "What is the refund policy?",
    "calculate_confidence": true,
    "auto_send_threshold": 0.8
}
```

### Response

```json
{
    "answer": "The refund policy allows returns within 30 days.",
    "confidence": {
        "overall_score": 85,
        "components": {
            "retrieval_confidence": 0.89,
            "generation_confidence": 0.85,
            "context_coverage": 0.8
        },
        "reasoning": "Good retrieval match, well-cited answer, mostly from context"
    },
    "routing": {
        "decision": "auto_send",
        "reason": "Overall confidence (85%) exceeds threshold (80%)"
    },
    "source": "rag" // or "verified_kb"
}
```

### Confidence Response with Low Score

```json
{
    "answer": "I don't have specific information about that.",
    "confidence": {
        "overall_score": 35,
        "components": {
            "retrieval_confidence": 0.42,
            "generation_confidence": 0.3,
            "context_coverage": 0.25
        },
        "reasoning": "Poor retrieval match, weak context coverage, LLM uncertain"
    },
    "routing": {
        "decision": "hitl",
        "reason": "Low confidence (35%) below threshold (80%)",
        "end_user_message": "I'm checking with the team for the best answer. You'll hear from us shortly."
    },
    "source": "rag"
}
```

## Implementation Tasks

### Backend (FastAPI)

1. **Confidence Calculator Service:**

    - Extract retrieval confidence (max similarity from chunks)
    - Extract generation confidence (parse LLM response or prompt LLM)
    - Calculate context coverage (citation analysis)
    - Combine components with weighting
    - Store in confidence_logs table

2. **Confidence Calculation:**

    ```python
    def calculate_confidence(
        context_chunks,
        generated_answer,
        citations
    ) -> ConfidenceResult:
        # Retrieval: max similarity
        retrieval_conf = max([c.similarity for c in context_chunks]) if context_chunks else 0

        # Generation: ask LLM or infer from response
        gen_conf = infer_generation_confidence(generated_answer)

        # Coverage: cited sentences / total sentences
        total_sents = count_sentences(generated_answer)
        cited_sents = len(set(c.sentence_id for c in citations))
        coverage = cited_sents / total_sents if total_sents > 0 else 0

        # Combine
        overall = (retrieval_conf * 0.4 + gen_conf * 0.3 + coverage * 0.3)

        return ConfidenceResult(
            overall=overall,
            retrieval=retrieval_conf,
            generation=gen_conf,
            coverage=coverage
        )
    ```

3. **Routing Decision Logic:**

    - Compare overall_confidence vs bot's auto_send_threshold
    - Route to auto-send or HITL queue
    - Log decision for analytics

4. **Testing:**
    - Unit tests: Confidence formula with various inputs
    - Unit tests: Routing decisions
    - Integration tests: End-to-end confidence flow
    - Edge cases: No context, all sentences cited, etc.

### Frontend (Next.js)

1. **Confidence Display (Agent UI):**

    - Show confidence score in HITL queue
    - Color-coded indicator (green >=80%, yellow 60-80%, red <60%)
    - Breakdown of components (retrieval, generation, coverage)
    - Explanation: "Why this score?"

2. **Confidence Display (End-User UI):**

    - Don't show exact score to end-user
    - Show "Verified" badge for Verified KB answers
    - Show "Checking with team..." for low confidence (auto-routed)
    - Show notification when answer arrives

3. **Bot Settings:**
    - Slider to adjust auto-send threshold (0-100%)
    - Preview: How many of last 100 queries would auto-send?
    - Toggle: Enable/disable auto-send

## Dependencies

### Required

-   Story 3.3 (Citation Generation): Need citation data
-   Story 3.2 (Answer Generation): Need generated answer text

### Optional

-   Verified KB implementation for high-confidence answers

## Acceptance Test Plan

### Test Scenarios

**Scenario 1: High Confidence Score**

-   Given: Query with perfect match in context
-   When: Confidence is calculated
-   Then: Score >= 80%, routing is "auto_send"

**Scenario 2: Low Confidence Score**

-   Given: Query with poor context match
-   When: Confidence is calculated
-   Then: Score < 80%, routing is "hitl"

**Scenario 3: No Context (Zero Confidence)**

-   Given: Query with empty search results
-   When: Confidence is calculated
-   Then: Score = 0%, response is "I don't have information", routing is "hitl"

**Scenario 4: Verified KB Answer**

-   Given: Query matching Verified KB entry
-   When: Answer retrieved
-   Then: Confidence = 95%, auto-send always, no HITL

**Scenario 5: Threshold Override**

-   Given: Answer with 75% confidence, threshold at 80%
-   When: Agent manually approves answer
-   Then: Response is sent to end-user, logged as "manual override"

**Scenario 6: Confidence Breakdown**

-   Given: Answer with mixed citations
-   When: Agent views confidence details
-   Then: Components visible: retrieval=0.85, generation=0.75, coverage=0.80

## Definition of Done

-   [ ] Confidence calculator working with all three components
-   [ ] Weighting formula (40/30/30) validated
-   [ ] Routing decision logic correct
-   [ ] Confidence scores calibrated (80% = likely correct)
-   [ ] HITL queue receives low-confidence answers
-   [ ] Agent UI shows confidence details
-   [ ] End-user sees appropriate messaging
-   [ ] Verified KB answers always high confidence
-   [ ] Analytics track confidence distribution
-   [ ] Code reviewed and tested
-   [ ] Code merged to main

## Functional Requirements Covered

-   **FR23:** System calculates and returns confidence score (0-100%) ✓
-   **FR24:** System checks Verified KB first before generating ✓
-   **FR31:** Low-confidence responses display "I'm checking with the team" ✓

## Technical Notes

### Confidence Calibration

Over time, calibrate formula to real outcomes:

-   Track which confidence levels resulted in user satisfaction
-   Adjust weights if certain component consistently off
-   Example: If 80% confidence answers often get rejected, lower threshold

### Monitoring Metrics

-   Distribution of confidence scores (histogram)
-   Correlation between confidence and user feedback
-   HITL rejection rate by confidence level
-   Auto-send accuracy (measure satisfaction)

### Learning Feedback Loop

1. Collect user feedback (thumbs up/down, agent edits/rejections)
2. Analyze correlation with confidence scores
3. Retrain or adjust confidence formula
4. Deploy improved version

## Risk & Mitigation

| Risk                             | Mitigation                                   |
| -------------------------------- | -------------------------------------------- |
| Overconfident scores             | Conservative weighting, validation testing   |
| Underconfident scores            | Calibration over time, formula tuning        |
| Context coverage miscalculation  | Robust citation extraction, test edge cases  |
| LLM self-reporting unreliable    | Use inference + prompting, validate in tests |
| Verified KB not marked high conf | Explicit handling in routing logic           |

## Dev Agent Record

### Context Reference

<!-- Story context XML will be added by context workflow -->

### Agent Model Used

Claude Haiku 4.5

### Completion Notes List

-   Story 3.4 drafted with comprehensive confidence scoring formula
-   Three-component model (retrieval, generation, context coverage)
-   Weighting strategy documented (40/30/30 ratios)
-   Routing decision logic clear (threshold-based)
-   Verified KB handling ensures high confidence
-   Calibration strategy for real-world accuracy
-   HITL integration for low-confidence answers
-   Agent UI showing confidence breakdown

### Debug Log References

### File List

<!-- Will be updated by dev agent during implementation -->

## Change Log

-   2025-12-04: Initial draft created by SM
    -   Three-component confidence formula specified
    -   Weighting ratios defined (40/30/30)
    -   Routing logic for auto-send vs HITL
    -   Verified KB special handling
    -   Confidence calibration strategy
    -   Agent UI requirements for confidence display
    -   End-user messaging for low confidence
    -   Database schema for confidence logging
