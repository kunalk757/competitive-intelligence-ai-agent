-- ==============================================================================
-- Competitive Intelligence AI Agent - News Articles Schema
-- ==============================================================================
-- Run this SQL in your Supabase SQL Editor to create the news_articles table.

CREATE TABLE IF NOT EXISTS public.news_articles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title TEXT NOT NULL,
    description TEXT,
    source_name TEXT,
    source_url TEXT NOT NULL UNIQUE,
    image_url TEXT,
    published_at TIMESTAMPTZ,
    fetched_at TIMESTAMPTZ DEFAULT NOW(),
    category TEXT DEFAULT 'Technology',
    company TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indices for performance
CREATE INDEX IF NOT EXISTS idx_news_articles_published_at 
    ON public.news_articles (published_at DESC);

CREATE INDEX IF NOT EXISTS idx_news_articles_created_at 
    ON public.news_articles (created_at DESC);

CREATE INDEX IF NOT EXISTS idx_news_articles_company 
    ON public.news_articles (company);

-- Enable Row Level Security (RLS)
ALTER TABLE public.news_articles ENABLE ROW LEVEL SECURITY;

-- Allow public read access to saved news
CREATE POLICY "Allow public read access to news_articles" 
    ON public.news_articles 
    FOR SELECT 
    USING (true);

-- Allow backend service role / authenticated write access
CREATE POLICY "Allow service role full access to news_articles" 
    ON public.news_articles 
    FOR ALL 
    USING (true)
    WITH CHECK (true);

-- ==============================================================================
-- Company Intelligence Profiles Schema
-- ==============================================================================
CREATE TABLE IF NOT EXISTS public.company_profiles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    company_name TEXT NOT NULL UNIQUE,
    overview TEXT,
    industry TEXT,
    website TEXT,
    sources JSONB DEFAULT '[]'::jsonb,
    fetched_at TIMESTAMPTZ DEFAULT NOW(),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_company_profiles_name 
    ON public.company_profiles (company_name);

ALTER TABLE public.company_profiles ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Allow public read access to company_profiles" 
    ON public.company_profiles 
    FOR SELECT 
    USING (true);

CREATE POLICY "Allow service role full access to company_profiles" 
    ON public.company_profiles 
    FOR ALL 
    USING (true)
    WITH CHECK (true);

-- ==============================================================================
-- Research Papers Schema (Semantic Scholar Integration)
-- ==============================================================================
CREATE TABLE IF NOT EXISTS public.research_papers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    external_id TEXT UNIQUE,
    title TEXT NOT NULL,
    authors JSONB DEFAULT '[]'::jsonb,
    abstract TEXT,
    year INTEGER,
    venue TEXT,
    url TEXT,
    citation_count INTEGER DEFAULT 0,
    fields_of_study JSONB DEFAULT '[]'::jsonb,
    source TEXT DEFAULT 'Semantic Scholar',
    fetched_at TIMESTAMPTZ DEFAULT NOW(),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_research_papers_external_id 
    ON public.research_papers (external_id);

CREATE INDEX IF NOT EXISTS idx_research_papers_year 
    ON public.research_papers (year DESC);

CREATE INDEX IF NOT EXISTS idx_research_papers_citations 
    ON public.research_papers (citation_count DESC);

ALTER TABLE public.research_papers ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Allow public read access to research_papers" 
    ON public.research_papers 
    FOR SELECT 
    USING (true);

CREATE POLICY "Allow service role full access to research_papers" 
    ON public.research_papers 
    FOR ALL 
    USING (true)
    WITH CHECK (true);

