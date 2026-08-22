export interface StepActivityData {
  step: number;
  action: "tool" | "final" | "error";
  tool?: string;
  summary: string;
  status: "running" | "completed" | "failed";
  timestamp: string;
}

export interface NewsArticleData {
  id?: string;
  title: string;
  source: string;
  published_at?: string;
  time?: string;
  description?: string;
  url?: string;
  image_url?: string;
  category?: string;
  company_tag?: string;
}

export interface CompanyCardData {
  id?: string;
  name: string;
  ticker?: string;
  industry?: string;
  overview?: string;
  description?: string;
  website?: string;
  logo_url?: string;
  sources?: Array<{ title: string; url: string; snippet?: string }>;
}

export interface ResearchPaperData {
  title: string;
  authors?: string;
  published_date?: string;
  source?: string;
  abstract?: string;
  url?: string;
  image_url?: string;
}

export interface PatentItemData {
  patent_number: string;
  title: string;
  assignee?: string;
  filing_date?: string;
  abstract?: string;
  url?: string;
}

export interface SourceItemData {
  title: string;
  url: string;
  snippet?: string;
}

export interface AgentRunResponse {
  success: boolean;
  answer: string;
  steps: StepActivityData[];
  tools_used: string[];
  iterations: number;
  session_id?: string;
  news_results?: NewsArticleData[];
  companies?: CompanyCardData[];
  news?: NewsArticleData[];
  research?: ResearchPaperData[];
  patents?: PatentItemData[];
  sources?: SourceItemData[];
  error?: string;
}

export interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  queryText?: string;
  response?: AgentRunResponse;
  isLoading?: boolean;
  error?: string;
  timestamp: string;
  session_id?: string;
}

