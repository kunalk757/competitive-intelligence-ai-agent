export interface Company {
  id: string;
  name: string;
  ticker?: string;
  industry?: string;
  description?: string;
  logoText?: string;
  logoUrl?: string;
  accentColor?: string;
}

export interface CompanySource {
  title: string;
  url: string;
  snippet?: string | null;
}

export interface CompanyWebInfo {
  name: string;
  overview?: string | null;
  website?: string | null;
  industry?: string | null;
  sources: CompanySource[];
}

export interface CompanyNewsItem {
  title: string;
  description?: string | null;
  source: string;
  published_at: string;
  url: string;
  image_url?: string | null;
}

export interface CompanyDetailsResponse {
  company: CompanyWebInfo;
  news: CompanyNewsItem[];
  last_updated?: string | null;
  cached?: boolean;
  has_data: boolean;
  message?: string | null;
}
