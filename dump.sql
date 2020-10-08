--
-- PostgreSQL database dump
--

-- Dumped from database version 10.14 (Ubuntu 10.14-0ubuntu0.18.04.1)
-- Dumped by pg_dump version 10.14 (Ubuntu 10.14-0ubuntu0.18.04.1)

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

--
-- Name: plpgsql; Type: EXTENSION; Schema: -; Owner: 
--

CREATE EXTENSION IF NOT EXISTS plpgsql WITH SCHEMA pg_catalog;


--
-- Name: EXTENSION plpgsql; Type: COMMENT; Schema: -; Owner: 
--

COMMENT ON EXTENSION plpgsql IS 'PL/pgSQL procedural language';


SET default_tablespace = '';

SET default_with_oids = false;

--
-- Name: Answers; Type: TABLE; Schema: public; Owner: user_bot
--

CREATE TABLE public."Answers" (
    user_id character varying NOT NULL,
    bill_id character varying NOT NULL,
    user_vote integer NOT NULL
);


ALTER TABLE public."Answers" OWNER TO user_bot;

--
-- Name: Bills; Type: TABLE; Schema: public; Owner: user_bot
--

CREATE TABLE public."Bills" (
    bill_id character varying NOT NULL,
    title character varying,
    date date NOT NULL,
    is_note boolean NOT NULL,
    is_pdf boolean NOT NULL,
    is_secret boolean NOT NULL,
    vote_for integer NOT NULL,
    vote_against integer NOT NULL,
    not_voted integer NOT NULL,
    abstained integer NOT NULL
);


ALTER TABLE public."Bills" OWNER TO user_bot;

--
-- Name: Users; Type: TABLE; Schema: public; Owner: user_bot
--

CREATE TABLE public."Users" (
    user_id character varying NOT NULL,
    first_name character varying NOT NULL,
    chat_id character varying NOT NULL,
    region character varying
);


ALTER TABLE public."Users" OWNER TO user_bot;

--
-- Data for Name: Answers; Type: TABLE DATA; Schema: public; Owner: user_bot
--

COPY public."Answers" (user_id, bill_id, user_vote) FROM stdin;
373793732	992429-7	1
373793732	922869-7	1
141905856	922869-7	1
203812639	922869-7	1
1149964802	922869-7	1
568557806	922869-7	-1
1065927973	922869-7	0
106286739	922869-7	1
59270332	922869-7	1
448837853	922869-7	1
\.


--
-- Data for Name: Bills; Type: TABLE DATA; Schema: public; Owner: user_bot
--

COPY public."Bills" (bill_id, title, date, is_note, is_pdf, is_secret, vote_for, vote_against, not_voted, abstained) FROM stdin;
992429-7	922869-7 Об изменениях в составах некоторых комитетов Государственной Думы и о внесении изменений в постановление Государственной Думы Федерального Собрания Российской Федерации "О составах комитетов Государственной Думы"	2020-07-21	f	t	f	389	0	59	2
922869-7	922869-7 Об экспериментальных правовых режимах в сфере цифровых инноваций в Российской Федерации	2020-07-22	t	t	f	350	27	73	0
933869-7	922869-7 Об экспериментальных правовых режимах в сфере цифровых инноваций в Российской Федерации	2020-07-21	t	t	f	350	27	73	0
\.


--
-- Data for Name: Users; Type: TABLE DATA; Schema: public; Owner: user_bot
--

COPY public."Users" (user_id, first_name, chat_id, region) FROM stdin;
373793732	Ilya	373793732	Приморский край
141905856	Constantin	141905856	Приморский край
203812639	Pavel	203812639	Приморский край
1149964802	Alex	1149964802	Приморский край
52203109	Константин	52203109	\N
568557806	Alexey	568557806	Приморский край
1065927973	Максим	1065927973	\N
146533661	Max	146533661	\N
341546944	Shulginov	341546944	Приморский край
106286739	Илья	106286739	Приморский край
59270332	Sergio	59270332	Приморский край
51365789	Vitalik	51365789	Приморский край
152433615	Михаил	152433615	\N
387194603	Evgeny	387194603	\N
448837853	Aleksey	448837853	Приморский край
173114033	Khadgar	173114033	\N
\.


--
-- Name: Answers Answers_pkey; Type: CONSTRAINT; Schema: public; Owner: user_bot
--

ALTER TABLE ONLY public."Answers"
    ADD CONSTRAINT "Answers_pkey" PRIMARY KEY (user_id, bill_id);


--
-- Name: Bills Bills_pkey; Type: CONSTRAINT; Schema: public; Owner: user_bot
--

ALTER TABLE ONLY public."Bills"
    ADD CONSTRAINT "Bills_pkey" PRIMARY KEY (bill_id);


--
-- Name: Users Users_pkey; Type: CONSTRAINT; Schema: public; Owner: user_bot
--

ALTER TABLE ONLY public."Users"
    ADD CONSTRAINT "Users_pkey" PRIMARY KEY (user_id);


--
-- Name: TABLE "Answers"; Type: ACL; Schema: public; Owner: user_bot
--

GRANT SELECT,INSERT,DELETE,UPDATE ON TABLE public."Answers" TO postgres;


--
-- Name: TABLE "Bills"; Type: ACL; Schema: public; Owner: user_bot
--

GRANT SELECT,INSERT,DELETE,UPDATE ON TABLE public."Bills" TO postgres;


--
-- Name: TABLE "Users"; Type: ACL; Schema: public; Owner: user_bot
--

GRANT SELECT,INSERT,DELETE,UPDATE ON TABLE public."Users" TO postgres;


--
-- PostgreSQL database dump complete
--

