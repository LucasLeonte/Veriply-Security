# Technical Research Report: Open Source LLMs for Veriply

**Date:** 2025-11-27
**Prepared by:** Analyst Mary
**Research Focus:** Comparing Open Source LLMs for RAG-based Customer Support

---

## Executive Summary

For Veriply's RAG-based customer support platform, the choice of LLM significantly impacts cost, latency, and accuracy. After analyzing 2024-2025 benchmarks and practical considerations, we recommend a **tiered approach**:

1.  **Primary (Self-Hosted via Ollama):** Qwen 2.5 7B/14B or Llama 3.3 70B
2.  **Fallback (API):** DeepSeek V3 (excellent cost/performance) or GPT-4o-mini (reliability)
3.  **Embedding:** nomic-embed-text or bge-m3 (both excellent for RAG)

---

## 1. Open Source LLM Comparison (2025)

### Tier 1: "Runnable on Consumer Hardware" (8B-14B Parameters)

These models can run on a single RTX 4090 or equivalent, ideal for MVP and cost control.

| Model | Parameters | Context Window | Ollama Pulls | RAG Suitability | Notes |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Qwen 2.5** | 0.5B - 72B | 128K | 16.9M | ⭐⭐⭐⭐⭐ | Best multilingual, excellent reasoning. Alibaba-backed. |
| **Llama 3.2** | 1B, 3B | 128K | 47.4M | ⭐⭐⭐ | Very small, fast. Good for edge/mobile. Limited reasoning. |
| **Llama 3.1** | 8B, 70B, 405B | 128K | 106M | ⭐⭐⭐⭐ | Industry standard. Strong instruction following. |
| **Mistral** | 7B | 32K | 22.2M | ⭐⭐⭐ | Fast, good general use. Older architecture. |
| **Phi-4** | 14B | 16K | 6.3M | ⭐⭐⭐⭐ | Microsoft. Excellent reasoning for size. Short context. |
| **Gemma 3** | 1B - 27B | 128K | 26.7M | ⭐⭐⭐⭐ | Google. Runs on single GPU. Vision support. |

**Recommendation for MVP:** **Qwen 2.5 7B**
*   **Why:** Best balance of reasoning, multilingual support (important for European SMEs), and 128K context window.

---

### Tier 2: "Requires Serious Hardware" (70B+ Parameters)

These require multiple GPUs or cloud hosting but offer near-frontier performance.

| Model | Parameters | Context Window | Ollama Pulls | Performance | Cost (API) |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Llama 3.3 70B** | 70B | 128K | 2.8M | ⭐⭐⭐⭐⭐ | $0.59/$0.70 per 1M tokens |
| **Llama 4 Scout** | 16x17B MoE | 10M (!) | 851K | ⭐⭐⭐⭐ | $0.11/$0.34 per 1M tokens |
| **DeepSeek-R1** | 1.5B - 671B | 128K | 72.5M | ⭐⭐⭐⭐⭐ | $0.55/$2.19 per 1M tokens |
| **DeepSeek V3** | 671B (37B active) | 128K | 2.8M | ⭐⭐⭐⭐ | $0.27/$1.10 per 1M tokens |

**Recommendation for Scale:** **DeepSeek V3 0324** (via API) or **Llama 3.3 70B** (self-hosted if you have the hardware).
*   **Why DeepSeek:** Incredible value. Only 37B parameters active per token (MoE), so it's fast AND cheap.
*   **Why Llama 3.3:** Industry standard, massive community support, tool-use capabilities.

---

## 2. Benchmark Analysis (Veriply Use Case)

For a RAG-based support bot, we prioritize:
1.  **Instruction Following:** Does it answer the question asked?
2.  **Tool Use / Function Calling:** Can it call APIs (for future Task Automation)?
3.  **Reasoning:** Can it synthesize information from multiple documents?

### Benchmark Results (2024-2025 Data)

| Model | GPQA (Reasoning) | BFCL (Tool Use) | SWE Bench (Coding) | Speed (t/s) |
| :--- | :--- | :--- | :--- | :--- |
| DeepSeek-R1 | 71.5% | 57.53% | 49.2% | 24 |
| Llama 3.3 70B | 50.5% | **77.3%** | N/A | **2500** |
| Qwen 2.5 32B | 46% | 62.79% | 18.8% | N/A |
| Gemma 3 27B | 42.4% | 59.11% | 10.2% | 59 |
| Llama 3.1 405B | 49% | **81.1%** | N/A | 969 |

**Key Insight:** Llama models excel at **Tool Use (BFCL)**, which is critical for Veriply's future "Task Automation" feature. Qwen excels at multilingual reasoning.

---

## 3. Embedding Models for RAG

The embedding model is just as important as the LLM for RAG quality.

| Model | Dimensions | Multilingual | Ollama Pulls | Notes |
| :--- | :--- | :--- | :--- | :--- |
| **nomic-embed-text** | 768 | Limited | 46.3M | High performance, large context. Industry favorite. |
| **bge-m3** | 1024 | yes | 2.8M | BAAI. Multi-granularity (dense + sparse. |
| **mxbai-embed-large** | 1024 | Limited | 5.4M | State-of-the-art from mixedbread.ai. |
| **snowflake-arctic-embed** | Varies | Limited | 1.1M | Snowflake-optimized. |

**Recommendation:** **nomic-embed-text** for pure English use cases.

---

## 4. Hosting Strategy: Ollama vs. API

### Option A: Self-Hosted (Ollama)
*   **Pros:** Full control, no per-token costs, data never leaves your server (privacy selling point).
*   **Cons:** Requires GPU infrastructure (RTX 4090 ~$1600, or cloud GPU ~$1-3/hr).
*   **Best For:** MVP testing, privacy-sensitive customers.

### Option B: API (DeepSeek, Together, Groq)
*   **Pros:** No infrastructure management, pay-per-use, instant scalability.
*   **Cons:** Per-token costs, data leaves your network.
*   **Best For:** Production scale, variable traffic.

**Recommendation for Veriply:** Start with **Ollama (Qwen 2.5 14B)** for development and early customers. Add **DeepSeek V3 API** as a fallback for complex queries or high-traffic periods.

---

## 5. Cost Analysis (Per 1M Tokens)

| Provider / Model | Input Cost | Output Cost | Notes |
| :--- | :--- | :--- | :--- |
| **Ollama (Self-Hosted)** | ~$0 (GPU cost) | ~$0 | Fixed infra cost, variable electricity. |
| **DeepSeek V3 (API)** | $0.27 | $1.10 | Best value for 671B-class model. |
| **Llama 4 Scout (API)** | $0.11 | $0.34 | Cheapest, 10M context! |
| **GPT-4o mini (OpenAI)** | $0.15 | $0.60 | Reliable, but less capable. |
| **GPT-4o (OpenAI)** | $2.50 | $10.00 | Expensive, but battle-tested. |

---

## 6. Strategic Recommendation for Veriply

### Phase 1: MVP (Sprint 1-4)
*   **LLM:** Qwen 2.5 14B (via Ollama, self-hosted or Docker).
*   **Embedding:** nomic-embed-text (via Ollama).
*   **Vector DB:** PostgreSQL + pgvector (already in tech stack).
*   **Rationale:** Zero API costs, full privacy (selling point), excellent multilingual support for EU market.

### Phase 2: Scale (Post-MVP)
*   **Primary LLM:** DeepSeek V3 (API) for complex queries.
*   **Fast Fallback:** Llama 4 Scout (API) for simple/high-volume queries.
*   **Embedding:** Change to bge-m3 (self-hosted is fine for embeddings).
*   **Rationale:** MoE models (DeepSeek, Llama 4) are fast and cheap at scale.

### Phase 3: Enterprise (Future)
*   **Offer "Bring Your Own Model":** Let enterprise customers connect their own OpenAI/Azure keys.
*   **On-Premise Option:** Package Ollama + Qwen as a Docker image for customers who need full data sovereignty.

---

## 7. Key Risks and Mitigations

| Risk | Mitigation |
| :--- | :--- |
| **Qwen is Alibaba (China-based):** Some EU customers may be hesitant. | Offer Llama (Meta) as alternative. Both are open-weight. |
| **Self-hosting requires DevOps:** | Use pre-built Docker images. Ollama simplifies this significantly. |
| **Model quality degrades on niche topics:** | HITL workflow catches failures. This is Veriply's core value. |

---

## Appendix: Ollama Quick Start Commands

```bash
# Install Ollama
curl -fsSL https://ollama.com/install.sh | sh

# Pull recommended models
ollama pull qwen2.5:14b
ollama pull bge-m3

# Run a test query
ollama run qwen2.5:14b "Summarize this support ticket: ..."
```

---

*Sources: Vellum LLM Leaderboard (2025), Ollama Model Library, Artificial Analysis (2025)*
