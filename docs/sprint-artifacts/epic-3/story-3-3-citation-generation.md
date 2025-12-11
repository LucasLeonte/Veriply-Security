# Story 3.3: Citation Generation

**Epic:** 3. RAG Q&A Engine  
**Status:** in-progress  
**Assigned to:** Kainy  
**Blocked by:** 3-2-context-only-answer-generation
**Context:** docs/sprint-artifacts/epic-3/story-3-3.context.xml

## Story

As a User,  
I want every AI answer to include source citations,  
so that I can verify the information myself.

## Acceptance Criteria

### Citation Inclusion

- [ ] Every factual statement in the answer includes a citation to source
- [ ] Citation format is clear and clickable
- [ ] Citations link to the actual source document chunk
- [ ] Citations include: document name, section (if available), page number (if PDF)

### Citation Formats

- [ ] Inline format: "According to [Returns Policy, Section 2.1]..."
- [ ] Footnote format: "...30-day refund window.[1]" with "[1] Returns Policy.pdf, Page 3"
- [ ] Hover tooltip: Shows full source and relevance score
- [ ] Citation color: Distinct visual (blue, underlined)

### Citation Accuracy

- [ ] Citation text matches the actual chunk text
- [ ] Citation source matches the document metadata
- [ ] No citations for synthesized/summarized information
- [ ] If multiple chunks support statement, ALL are cited

### Missing Citations Detection

- [ ] If LLM generates statement without citation:
  - [ ] System flags as error (should never happen)
  - [ ] Error logged for debugging
  - [ ] Response marked as requiring review

### Citation UI

- [ ] Citations are clickable (not decorative)
- [ ] Click opens source chunk in side panel or new tab
- [ ] User can read source context
- [ ] Citation quality score visible (similarity %)
- [ ] Source document title and section clearly labeled

## Technical Specifications

### Citation Post-Processing

**Approach:** Parse LLM response and match statements to context chunks

**Algorithm:**
1. Split LLM answer into sentences
2. For each sentence, identify source chunk(s):
   - Semantic similarity between sentence and chunk (>0.7 threshold)
   - Or exact phrase match in chunk
3. Assign highest similarity chunk as primary source
4. If multiple chunks match (>0.6), list all as co-sources
5. Generate citation markup

**Python Pseudocode:**
```python
def add_citations(answer_text, context_chunks):
    """Post-process answer to add citations"""
    sentences = split_into_sentences(answer_text)
    citations_map = {}
    
    for sent_idx, sentence in enumerate(sentences):
        # Embed sentence
        sent_embedding = embed(sentence)
        
        # Find matching chunks
        matches = []
        for chunk in context_chunks:
            similarity = cosine_similarity(sent_embedding, chunk.embedding)
            if similarity > 0.7 or phrase_matches(sentence, chunk.text):
                matches.append((chunk, similarity))
        
        if matches:
            # Sort by similarity
            matches.sort(key=lambda x: x[1], reverse=True)
            primary = matches[0][0]
            co_sources = [m[0] for m in matches[1:] if m[1] > 0.6]
            
            citations_map[sent_idx] = {
                'primary': primary,
                'co_sources': co_sources,
                'confidence': matches[0][1]
            }
    
    return inject_citations(answer_text, citations_map)
```

### Citation Data Structure

```python
class Citation:
    chunk_id: UUID
    document_id: UUID
    document_name: str
    section_title: Optional[str]
    page_number: Optional[int]
    similarity_score: float  # 0-1
    chunk_position: int
    confidence: str  # "high", "medium", "low"

class AnswerWithCitations:
    answer_html: str  # With citation markup
    citations: List[Citation]
    missing_citations: List[str]  # Sentences without citations (error)
```

### HTML Markup

**Input (LLM Response):**
```
The refund policy allows returns within 30 days.
Customers can request refunds through the support portal.
```

**Output (With Citations):**
```html
<p>The refund policy allows returns within <span class="citation" data-citation-id="0">30 days</span>.</p>
<p>Customers can request refunds through <span class="citation" data-citation-id="1">the support portal</span>.</p>

<div class="citations">
  <div class="citation" id="citation-0">
    <strong>Source:</strong> Returns Policy.pdf - Section 2.1
    <strong>Similarity:</strong> 92%
    <a href="#chunk-abc123">View source</a>
  </div>
  <div class="citation" id="citation-1">
    <strong>Source:</strong> FAQ.md - Customer Support
    <strong>Similarity:</strong> 87%
    <a href="#chunk-def456">View source</a>
  </div>
</div>
```

### Citation Matching Strategy

| Scenario | Strategy | Threshold |
|----------|----------|-----------|
| Exact phrase match | Direct mapping | 1.0 (100%) |
| High semantic match | Embedding similarity | 0.8-1.0 |
| Medium match | Includes topic | 0.6-0.8 |
| Low match | Partial relevance | 0.4-0.6 |
| No match | Synthesized content | <0.4 (no citation) |

### Citation UI Components

**Inline Citation (Footnote Style):**
```
The company offers a 30-day return window.[1]

[1] Returns Policy.pdf - Section 2, Page 3 (92% match)
    Click to view source
```

**Hover Tooltip:**
```
[Returns Policy.pdf - Section 2]
Similarity: 92%
"We offer a 30-day money-back guarantee for all purchases."
View full chunk →
```

**Citation Panel (Side Modal):**
```
Citation Source

Document: Returns Policy.pdf
Section: Returns & Refunds
Relevance: 92%

Full Chunk Text:
"We offer a 30-day money-back guarantee. Refunds are processed..."

Context:
- Previous chunk: [Navigation]
- Next chunk: [How to Request]
```

## API Contract

### Endpoint
```
POST /api/bots/{bot_id}/query/with-citations
```

### Request
```json
{
  "query": "What is the refund policy?",
  "context_chunks": [...],
  "stream": false
}
```

### Response
```json
{
  "answer": "The refund policy allows returns within 30 days.",
  "answer_html": "<p>The refund policy allows returns within <span class=\"citation\" data-citation-id=\"0\">30 days</span>.</p>",
  "citations": [
    {
      "id": "citation-0",
      "chunk_id": "uuid",
      "document_id": "uuid",
      "document_name": "Returns Policy.pdf",
      "section": "Returns & Refunds",
      "page_number": 3,
      "similarity_score": 0.92,
      "text_snippet": "We offer a 30-day money-back guarantee...",
      "confidence": "high"
    }
  ],
  "missing_citations": [],
  "model": "qwen2.5-14b"
}
```

## Implementation Tasks

### Backend (FastAPI)

1. **Citation Post-Processing Service:**
   - Sentence splitter (use spacy)
   - Sentence-to-chunk matcher (semantic + phrase matching)
   - Citation injector (generate HTML markup)
   - Confidence scorer for citations

2. **Citation Validation:**
   - Detect missing citations (error condition)
   - Validate citation sources exist in provided context
   - Log citation quality metrics

3. **API Endpoint:**
   - POST /api/bots/{bot_id}/query/with-citations
   - Returns structured response with citations
   - Integrates with answer generation (Story 3.2)

4. **Testing:**
   - Unit tests: Citation matching algorithm
   - Unit tests: HTML markup generation
   - Integration tests: End-to-end citation generation
   - Edge cases: No matching chunks, partial matches, multiple matches

### Frontend (Next.js)

1. **Citation Display Component:**
   - Render citations inline (highlighted, clickable)
   - Render citation list below answer
   - Hover tooltip with source info
   - Click to view source chunk

2. **Citation Panel:**
   - Side modal showing full source chunk
   - Navigation to previous/next chunks
   - Link to full document

3. **Citation Styling:**
   - Citation color (blue, distinct from body text)
   - Superscript numbers or inline brackets
   - Hover effects (highlight source)
   - Responsive on mobile

## Dependencies

### Required
- Story 3.2 (Answer Generation): Must provide LLM answer text
- Story 3.1 (Vector Search): Must provide context chunks with embeddings

### Optional
- spacy for NLP (sentence segmentation)
- Custom NLP model for better sentence boundaries

## Acceptance Test Plan

### Test Scenarios

**Scenario 1: Perfect Citation Match**
- Given: Answer matching 3 context chunks perfectly
- When: Citations are generated
- Then: All 3 chunks cited with 100% confidence

**Scenario 2: Partial Citation Match**
- Given: Answer with some synthesized content
- When: Citations are generated
- Then: Only factual statements cited, synthesized content unmarked

**Scenario 3: Multiple Sources**
- Given: Statement supported by 2 chunks
- When: Citations are generated
- Then: Both sources listed with similarity scores

**Scenario 4: No Matching Source**
- Given: Answer with unsupported statement
- When: Citation matching runs
- Then: Error flagged, statement marked as missing citation

**Scenario 5: Citation UI**
- Given: Answer with citations
- When: User hovers over citation
- Then: Tooltip shows source document and relevance
- And: Clicking opens source panel

**Scenario 6: HTML Rendering**
- Given: Citations with special characters
- When: HTML is generated
- Then: Markup is valid and renders correctly

## Definition of Done

- [ ] Citation post-processing algorithm working
- [ ] Citations match answer statements to chunks
- [ ] HTML markup generated correctly
- [ ] Missing citations detected and logged
- [ ] Citation UI components rendering
- [ ] Click-to-view-source working
- [ ] Mobile responsive
- [ ] Code reviewed and tested
- [ ] API documented
- [ ] Code merged to main

## Functional Requirements Covered

- **FR22:** System provides citations (source + section) for every answer ✓

## Technical Notes

### Citation Confidence Levels

| Level | Similarity | Meaning |
|-------|-----------|---------|
| High | > 0.85 | Direct quote or very close paraphrase |
| Medium | 0.65-0.85 | Related information, some interpretation |
| Low | 0.45-0.65 | Loosely related, consider reviewing |
| Questionable | < 0.45 | May not be properly cited, flag error |

### Sentence Splitting

Use spacy for robust sentence segmentation:
```python
import spacy
nlp = spacy.load("en_core_web_sm")
doc = nlp(answer_text)
sentences = [sent.text for sent in doc.sents]
```

### Embedding Comparison

Use same embedding model as document chunks (bge-m3):
```python
from sentence_transformers import SentenceTransformer
model = SentenceTransformer('BAAI/bge-m3')
sent_embedding = model.encode(sentence)
chunk_embedding = chunk.embedding
similarity = cosine_similarity([sent_embedding], [chunk_embedding])[0][0]
```

### Citation Link Format

Citation links should be permanent and shareable:
```
/api/bots/{bot_id}/chunks/{chunk_id}
```

This allows user to view source chunk context.

## Risk & Mitigation

| Risk | Mitigation |
|------|-----------|
| Citation mismatch | Implement validation, test extensively |
| Performance overhead | Cache embeddings, batch processing |
| HTML injection | Sanitize citation data, use HTML escaping |
| Missing citations undetected | Implement validation checks, log errors |
| User confusion (many citations) | Limit to most relevant 2-3 sources per statement |

## Dev Agent Record

### Context Reference

<!-- Story context XML will be added by context workflow -->

### Agent Model Used

Claude Haiku 4.5

### Completion Notes List

- Story 3.3 drafted with comprehensive citation post-processing strategy
- Citation matching algorithm defined (semantic + phrase matching)
- HTML markup generation for inline citations
- Citation UI components specified (inline, footnote, tooltip, modal)
- Confidence levels defined for citation quality
- Citation data structure and API contract detailed
- Edge cases covered (multiple sources, missing citations, synthesis)

### Debug Log References

### File List

<!-- Will be updated by dev agent during implementation -->

## Change Log

- 2025-12-04: Initial draft created by SM
  - Citation post-processing algorithm (semantic matching)
  - HTML markup generation strategy
  - Citation UI component specifications
  - Confidence scoring for citations
  - Sentence segmentation approach (spacy)
  - Citation validation and error detection
  - Integration with answer generation pipeline

