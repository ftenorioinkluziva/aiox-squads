export interface DocumentMetadata {
  doc_id: string;
  filename: string;
  title: string;
  total_pages: number;
  file_size_bytes: number;
  upload_timestamp: string;
  extracted_parties: string[];
  process_number: string;
  court: string;
  subject: string;
  text_page_count: number;
  scanned_page_count: number;
  ocr_required: boolean;
  extraction_status: "extracted" | "partial" | "ocr_required" | "empty";
  extraction_warnings: string[];
}

export interface DocumentPage {
  page_number: number;
  text: string;
  images: string[];
  word_count: number;
  text_length: number;
  image_count: number;
  extraction_method: "text" | "image" | "ocr" | "vision_llm";
  extraction_status: "extracted" | "ocr_required" | "failed";
  needs_ocr: boolean;
}

export interface DocumentClip {
  clip_id: string;
  doc_id: string;
  page_start: number;
  page_end: number;
  x0: number;
  y0: number;
  x1: number;
  y1: number;
  clip_type: "page" | "clip" | "image" | "excerpt";
  content_text: string;
  image_path: string | null;
  label: string;
}

export interface DocumentReference {
  doc_id: string;
  page?: number;
  page_range?: string;
  clip_id?: string;
  label: string;
  ref_type: "page" | "clip" | "image" | "excerpt";
}

export interface ChatMessage {
  id: string;
  role: "user" | "assistant" | "system" | "agent";
  content: string;
  agent_id?: string;
  agent_name?: string;
  timestamp: string;
  attachments: string[];
  references: DocumentReference[];
  metadata: Record<string, unknown>;
}

export interface ChatSession {
  session_id: string;
  title: string;
  created_at: string;
  updated_at: string;
  phase: string;
  messages: ChatMessage[];
  documents: DocumentMetadata[];
  clips: DocumentClip[];
  active_agents: string[];
  considerations: string;
  context_summary: string;
}

export interface AgentInfo {
  agent_id: string;
  name: string;
  title: string;
  icon: string;
  tier: string;
  squad: string;
  description: string;
  commands: Array<{ name: string; description: string; args: string }>;
  expertise_domains: string[];
  status: string;
  is_custom: boolean;
}

export interface SessionSummary {
  session_id: string;
  title: string;
  phase: string;
  created_at: string;
  updated_at: string;
  message_count: number;
  document_count: number;
}

export interface PipelineStep {
  id: string;
  run_id: string;
  phase_id: string;
  phase_name: string;
  task_id: string;
  task_description: string;
  agent_id: string;
  status: "queued" | "running" | "completed" | "failed" | "blocked";
  dependencies: string[];
  output_text?: string | null;
  error_message?: string | null;
  sort_order: number;
  started_at?: string | null;
  completed_at?: string | null;
}

export interface PipelineEvent {
  id?: number;
  run_id?: string;
  event_type: string;
  message?: string;
  payload: Record<string, unknown>;
  created_at?: string | null;
}

export interface PipelineRun {
  id: string;
  session_id: string;
  workflow_id: string;
  status: "queued" | "running" | "completed" | "failed" | "blocked";
  current_phase_id?: string | null;
  error_message?: string | null;
  created_at?: string | null;
  updated_at?: string | null;
  completed_at?: string | null;
  steps: PipelineStep[];
  events: PipelineEvent[];
  output_md?: string | null;
}

export type PanelView = "chat" | "documents" | "agents" | "editor";
