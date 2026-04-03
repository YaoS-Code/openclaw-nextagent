--
-- Blog posts schema for OpenClaw NexAgent setup
-- Run against your database:
--   psql -h 127.0.0.1 -U YOUR_DB_USER -d YOUR_DB_NAME -f sql/blog_schema.sql
--
-- Requires: CREATE EXTENSION vector; (pgvector) already installed
--

SET statement_timeout = 0;
SET lock_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);

--
-- Table: public.blog_posts
--

CREATE TABLE IF NOT EXISTS public.blog_posts (
    id              SERIAL PRIMARY KEY,
    slug            TEXT NOT NULL UNIQUE,
    title           TEXT NOT NULL,
    title_en        TEXT,
    summary         TEXT,
    summary_en      TEXT,
    content_md      TEXT NOT NULL,
    content_en_md   TEXT,
    category        TEXT NOT NULL,
    subcategory     TEXT,
    tags            TEXT[] DEFAULT '{}',
    source_url      TEXT,
    source_name     TEXT,
    author          TEXT DEFAULT 'Your Agent',
    image_url       TEXT,
    is_auto         BOOLEAN DEFAULT true,
    published       BOOLEAN DEFAULT false,
    featured        BOOLEAN DEFAULT false,
    view_count      INTEGER DEFAULT 0,
    embedding       vector(1024),
    created_at      TIMESTAMPTZ DEFAULT now(),
    updated_at      TIMESTAMPTZ DEFAULT now(),
    content_tsv     TSVECTOR GENERATED ALWAYS AS (
        to_tsvector('english',
            COALESCE(title, '') || ' ' ||
            COALESCE(title_en, '') || ' ' ||
            COALESCE(content_md, '')
        )
    ) STORED
);

--
-- Indexes
--

CREATE INDEX IF NOT EXISTS idx_blog_category   ON public.blog_posts USING btree (category) WHERE published;
CREATE INDEX IF NOT EXISTS idx_blog_created    ON public.blog_posts USING btree (created_at DESC) WHERE published;
CREATE INDEX IF NOT EXISTS idx_blog_embedding  ON public.blog_posts USING hnsw (embedding vector_cosine_ops) WITH (m=16, ef_construction=200) WHERE published;
CREATE INDEX IF NOT EXISTS idx_blog_fts        ON public.blog_posts USING gin (content_tsv);
CREATE INDEX IF NOT EXISTS idx_blog_slug       ON public.blog_posts USING btree (slug);
CREATE INDEX IF NOT EXISTS idx_blog_tags       ON public.blog_posts USING gin (tags) WHERE published;
CREATE UNIQUE INDEX IF NOT EXISTS idx_blog_source_url ON public.blog_posts USING btree (source_url) WHERE source_url IS NOT NULL;
