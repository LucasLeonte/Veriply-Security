// Unified citation types by reusing the chat Citation type to avoid duplication.
export type { Citation } from "./chat";

export interface AnnotatedAnswer {
  answer: string;
  answer_html: string;
  citations: import("./chat").Citation[];
  missing_citations: string[];
}
