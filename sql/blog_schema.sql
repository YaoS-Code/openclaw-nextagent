--
-- PostgreSQL database dump
--

\restrict BICn4NFXnwJrhcVINmJOcWVmllg1hrAEyagB0TOAK7n2zcDkV128lFhqUcGBsOq

-- Dumped from database version 17.9 (Ubuntu 17.9-1.pgdg24.04+1)
-- Dumped by pg_dump version 17.9 (Ubuntu 17.9-1.pgdg24.04+1)

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET transaction_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: blog_posts; Type: TABLE; Schema: public; Owner: oc_admin
--

CREATE TABLE public.blog_posts (
    id integer NOT NULL,
    slug text NOT NULL,
    title text NOT NULL,
    title_en text,
    summary text,
    summary_en text,
    content_md text NOT NULL,
    content_en_md text,
    category text NOT NULL,
    subcategory text,
    tags text[] DEFAULT '{}'::text[],
    source_url text,
    source_name text,
    author text DEFAULT 'NexAgent AI'::text,
    image_url text,
    is_auto boolean DEFAULT true,
    published boolean DEFAULT false,
    featured boolean DEFAULT false,
    view_count integer DEFAULT 0,
    embedding public.vector(1024),
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now(),
    content_tsv tsvector GENERATED ALWAYS AS (to_tsvector('english'::regconfig, ((((COALESCE(title, ''::text) || ' '::text) || COALESCE(title_en, ''::text)) || ' '::text) || COALESCE(content_md, ''::text)))) STORED
);


ALTER TABLE public.blog_posts OWNER TO oc_admin;

--
-- Name: blog_posts_id_seq; Type: SEQUENCE; Schema: public; Owner: oc_admin
--

CREATE SEQUENCE public.blog_posts_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.blog_posts_id_seq OWNER TO oc_admin;

--
-- Name: blog_posts_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: oc_admin
--

ALTER SEQUENCE public.blog_posts_id_seq OWNED BY public.blog_posts.id;


--
-- Name: blog_posts id; Type: DEFAULT; Schema: public; Owner: oc_admin
--

ALTER TABLE ONLY public.blog_posts ALTER COLUMN id SET DEFAULT nextval('public.blog_posts_id_seq'::regclass);


--
-- Name: blog_posts blog_posts_pkey; Type: CONSTRAINT; Schema: public; Owner: oc_admin
--

ALTER TABLE ONLY public.blog_posts
    ADD CONSTRAINT blog_posts_pkey PRIMARY KEY (id);


--
-- Name: blog_posts blog_posts_slug_key; Type: CONSTRAINT; Schema: public; Owner: oc_admin
--

ALTER TABLE ONLY public.blog_posts
    ADD CONSTRAINT blog_posts_slug_key UNIQUE (slug);


--
-- Name: idx_blog_category; Type: INDEX; Schema: public; Owner: oc_admin
--

CREATE INDEX idx_blog_category ON public.blog_posts USING btree (category) WHERE published;


--
-- Name: idx_blog_created; Type: INDEX; Schema: public; Owner: oc_admin
--

CREATE INDEX idx_blog_created ON public.blog_posts USING btree (created_at DESC) WHERE published;


--
-- Name: idx_blog_embedding; Type: INDEX; Schema: public; Owner: oc_admin
--

CREATE INDEX idx_blog_embedding ON public.blog_posts USING hnsw (embedding public.vector_cosine_ops) WITH (m='16', ef_construction='200') WHERE published;


--
-- Name: idx_blog_fts; Type: INDEX; Schema: public; Owner: oc_admin
--

CREATE INDEX idx_blog_fts ON public.blog_posts USING gin (content_tsv);


--
-- Name: idx_blog_slug; Type: INDEX; Schema: public; Owner: oc_admin
--

CREATE INDEX idx_blog_slug ON public.blog_posts USING btree (slug);


--
-- Name: idx_blog_source_url; Type: INDEX; Schema: public; Owner: oc_admin
--

CREATE UNIQUE INDEX idx_blog_source_url ON public.blog_posts USING btree (source_url) WHERE (source_url IS NOT NULL);


--
-- Name: idx_blog_tags; Type: INDEX; Schema: public; Owner: oc_admin
--

CREATE INDEX idx_blog_tags ON public.blog_posts USING gin (tags) WHERE published;


--
-- PostgreSQL database dump complete
--

\unrestrict BICn4NFXnwJrhcVINmJOcWVmllg1hrAEyagB0TOAK7n2zcDkV128lFhqUcGBsOq

