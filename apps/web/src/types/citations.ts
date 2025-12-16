/**
 * Type definitions for citation system.
 * Shared between backend schemas and frontend components.
 */

export type ConfidenceLevel = "high" | "medium" | "low";

export interface Citation {
  id: string;
  chunk_id: string;
  document_id: string;
  document_name: string;
  section?: string;
  page_number?: number;
  similarity_score: number; // 0-1
  chunk_position: number;
  confidence: ConfidenceLevel;
  text_snippet: string;
}

export interface AnnotatedAnswer {
  answer: string;
  answer_html: string;
  citations: Citation[];
  missing_citations: string[];
}
