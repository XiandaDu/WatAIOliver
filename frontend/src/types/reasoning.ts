export interface RAGSource {
  score: number;
  content_preview: string;
  metadata: Record<string, any>;
}

export interface RAGDetails {
  query: string;
  type: 'search_start' | 'search_complete';
  query_type?: 'original' | 'alternative';
  total_sources?: number;
  top_sources?: RAGSource[];
  all_scores?: number[];
}

export interface ReasoningStep {
  id: string;
  timestamp: Date;
  agent: string;
  action: string;
  summary: string;
  details?: string;
  status: 'running' | 'completed' | 'error';
  icon?: string;
  ragDetails?: RAGDetails;
}

export interface ReasoningState {
  isEnabled: boolean;
  steps: ReasoningStep[];
  currentAgent?: string;
  isStreaming: boolean;
}