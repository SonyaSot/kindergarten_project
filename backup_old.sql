--
-- PostgreSQL database dump
--

\restrict yGhuRLYyjFwtnwkoHNU2NY5vVa3KgYceQbZxutHnhetXzbX4TY5ocGn5TUILTGK

-- Dumped from database version 18.3
-- Dumped by pg_dump version 18.3

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

--
-- Name: attendancestatus; Type: TYPE; Schema: public; Owner: postgres
--

CREATE TYPE public.attendancestatus AS ENUM (
    'PRESENT',
    'ABSENT',
    'SICK',
    'NOT_MARKED'
);


ALTER TYPE public.attendancestatus OWNER TO postgres;

--
-- Name: userrole; Type: TYPE; Schema: public; Owner: postgres
--

CREATE TYPE public.userrole AS ENUM (
    'ADMIN',
    'TEACHER',
    'ACCOUNTANT'
);


ALTER TYPE public.userrole OWNER TO postgres;

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: attendance; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.attendance (
    id integer NOT NULL,
    child_id integer NOT NULL,
    teacher_id integer NOT NULL,
    date date NOT NULL,
    status public.attendancestatus,
    comment text,
    created_at timestamp without time zone,
    updated_at timestamp without time zone
);


ALTER TABLE public.attendance OWNER TO postgres;

--
-- Name: attendance_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.attendance_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.attendance_id_seq OWNER TO postgres;

--
-- Name: attendance_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.attendance_id_seq OWNED BY public.attendance.id;


--
-- Name: children; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.children (
    id integer NOT NULL,
    full_name character varying NOT NULL,
    date_of_birth date NOT NULL,
    group_id integer NOT NULL,
    parent_name character varying NOT NULL,
    parent_phone character varying,
    parent_email character varying,
    has_discount boolean,
    discount_reason text,
    is_active boolean
);


ALTER TABLE public.children OWNER TO postgres;

--
-- Name: children_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.children_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.children_id_seq OWNER TO postgres;

--
-- Name: children_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.children_id_seq OWNED BY public.children.id;


--
-- Name: groups; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.groups (
    id integer NOT NULL,
    name character varying NOT NULL,
    age_range character varying,
    teacher_id integer,
    created_at timestamp without time zone
);


ALTER TABLE public.groups OWNER TO postgres;

--
-- Name: groups_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.groups_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.groups_id_seq OWNER TO postgres;

--
-- Name: groups_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.groups_id_seq OWNED BY public.groups.id;


--
-- Name: payments; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.payments (
    id integer NOT NULL,
    child_id integer NOT NULL,
    month date NOT NULL,
    amount double precision NOT NULL,
    paid_amount double precision,
    status character varying,
    comment text,
    created_at timestamp without time zone,
    updated_at timestamp without time zone
);


ALTER TABLE public.payments OWNER TO postgres;

--
-- Name: payments_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.payments_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.payments_id_seq OWNER TO postgres;

--
-- Name: payments_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.payments_id_seq OWNED BY public.payments.id;


--
-- Name: users; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.users (
    id integer NOT NULL,
    email character varying NOT NULL,
    hashed_password character varying NOT NULL,
    full_name character varying NOT NULL,
    role public.userrole NOT NULL,
    is_active boolean,
    created_at timestamp without time zone
);


ALTER TABLE public.users OWNER TO postgres;

--
-- Name: users_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.users_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.users_id_seq OWNER TO postgres;

--
-- Name: users_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.users_id_seq OWNED BY public.users.id;


--
-- Name: attendance id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.attendance ALTER COLUMN id SET DEFAULT nextval('public.attendance_id_seq'::regclass);


--
-- Name: children id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.children ALTER COLUMN id SET DEFAULT nextval('public.children_id_seq'::regclass);


--
-- Name: groups id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.groups ALTER COLUMN id SET DEFAULT nextval('public.groups_id_seq'::regclass);


--
-- Name: payments id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.payments ALTER COLUMN id SET DEFAULT nextval('public.payments_id_seq'::regclass);


--
-- Name: users id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.users ALTER COLUMN id SET DEFAULT nextval('public.users_id_seq'::regclass);


--
-- Data for Name: attendance; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.attendance (id, child_id, teacher_id, date, status, comment, created_at, updated_at) FROM stdin;
\.


--
-- Data for Name: children; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.children (id, full_name, date_of_birth, group_id, parent_name, parent_phone, parent_email, has_discount, discount_reason, is_active) FROM stdin;
32	Алексеев Дмитрий	2020-01-15	1	Алексеева Ольга	+79991111111	alekseeva@mail.ru	f	\N	t
33	Борисова Анна	2020-02-20	1	Борисов Игорь	+79992222222	borisov@mail.ru	t	Многодетная семья	t
34	Васильев Максим	2020-03-10	1	Васильева Елена	+79993333333	vasileva@mail.ru	f	\N	t
35	Григорьев Иван	2020-04-05	1	Григорьева Мария	+79994444444	grigoreva@mail.ru	f	\N	t
36	Дмитриев Сергей	2020-05-12	1	Дмитриева Наталья	+79995555555	dmitrieva@mail.ru	t	Малоимущая семья	t
37	Егоров Павел	2020-06-18	1	Егорова Ирина	+79996666666	egorova@mail.ru	f	\N	t
38	Жуков Андрей	2020-07-22	1	Жукова Светлана	+79997777777	zhukova@mail.ru	f	\N	t
39	Зайцев Николай	2020-08-30	1	Зайцева Татьяна	+79998888888	zaytseva@mail.ru	f	\N	t
40	Иванов Артем	2020-09-14	1	Иванова Екатерина	+79999999999	ivanova@mail.ru	t	Ребенок-инвалид	t
41	Козлов Михаил	2020-10-25	1	Козлова Анна	+79990000000	kozlova@mail.ru	f	\N	t
42	Лебедев Даниил	2020-11-03	1	Лебедева Юлия	+79991112222	lebedeva@mail.ru	f	\N	t
43	Соколов Дмитрий	2020-01-10	3	Соколова Ольга	+79996667777	sokolova@mail.ru	f	\N	t
44	Титова Анна	2020-02-15	3	Титов Игорь	+79997778888	titov@mail.ru	t	Многодетная семья	t
45	Ушаков Максим	2020-03-20	3	Ушакова Елена	+79998889999	ushakova@mail.ru	f	\N	t
46	Федоров Иван	2020-04-25	3	Федорова Мария	+79999990000	fedorova@mail.ru	f	\N	t
47	Харитонов Сергей	2020-05-30	3	Харитонова Наталья	+79990001111	haritonova@mail.ru	t	Малоимущая семья	t
48	Цветков Павел	2020-06-05	3	Цветкова Ирина	+79991112222	tsvetkova@mail.ru	f	\N	t
49	Царев Андрей	2020-07-10	3	Царева Светлана	+79992223333	tsareva@mail.ru	f	\N	t
50	Чернов Николай	2020-08-15	3	Чернова Татьяна	+79993334444	chernova@mail.ru	f	\N	t
51	Шаров Артем	2020-09-20	3	Шарова Екатерина	+79994445555	sharova@mail.ru	t	Ребенок-инвалид	t
52	Щукин Михаил	2020-10-25	3	Щукина Анна	+79995556666	shchukina@mail.ru	f	\N	t
\.


--
-- Data for Name: groups; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.groups (id, name, age_range, teacher_id, created_at) FROM stdin;
1	Солнышко	3-4	2	2026-03-16 13:48:25.613273
3	Пупсы	2-4 года	4	2026-03-22 15:48:09.276497
\.


--
-- Data for Name: payments; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.payments (id, child_id, month, amount, paid_amount, status, comment, created_at, updated_at) FROM stdin;
\.


--
-- Data for Name: users; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.users (id, email, hashed_password, full_name, role, is_active, created_at) FROM stdin;
1	admin@sadik.ru	$pbkdf2-sha256$29000$.F/r/f.f01rLec8Zw1iL8Q$Ds.BF6M0Ywe9dPQUWOPw9UooHdxBcOaPRvt6A9mKP4A	string	ADMIN	t	2026-03-16 13:47:42.625765
2	sotnikova@bk.ru	$pbkdf2-sha256$29000$lTImhBAiZIxxLiVEyFnrXQ$1PqAKV1fj8V1.qC87FQs4dG8i98jJPRfqJpj..UZdxU	Сотникова София	TEACHER	t	2026-03-22 15:54:49.737974
4	naumenko@sadik.ru	$pbkdf2-sha256$29000$UKr13tubcw7B2BsDAGBMaQ$b7odudiLVId0kJfDOkW/FLkshHW.SEvM18fWSHOcX2c	Науменко Владимир	TEACHER	t	2026-03-23 11:11:08.634899
\.


--
-- Name: attendance_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.attendance_id_seq', 2, true);


--
-- Name: children_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.children_id_seq', 52, true);


--
-- Name: groups_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.groups_id_seq', 3, true);


--
-- Name: payments_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.payments_id_seq', 2, true);


--
-- Name: users_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.users_id_seq', 4, true);


--
-- Name: attendance attendance_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.attendance
    ADD CONSTRAINT attendance_pkey PRIMARY KEY (id);


--
-- Name: children children_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.children
    ADD CONSTRAINT children_pkey PRIMARY KEY (id);


--
-- Name: groups groups_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.groups
    ADD CONSTRAINT groups_pkey PRIMARY KEY (id);


--
-- Name: payments payments_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.payments
    ADD CONSTRAINT payments_pkey PRIMARY KEY (id);


--
-- Name: users users_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_pkey PRIMARY KEY (id);


--
-- Name: ix_attendance_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_attendance_id ON public.attendance USING btree (id);


--
-- Name: ix_children_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_children_id ON public.children USING btree (id);


--
-- Name: ix_groups_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_groups_id ON public.groups USING btree (id);


--
-- Name: ix_payments_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_payments_id ON public.payments USING btree (id);


--
-- Name: ix_users_email; Type: INDEX; Schema: public; Owner: postgres
--

CREATE UNIQUE INDEX ix_users_email ON public.users USING btree (email);


--
-- Name: ix_users_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_users_id ON public.users USING btree (id);


--
-- Name: attendance attendance_child_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.attendance
    ADD CONSTRAINT attendance_child_id_fkey FOREIGN KEY (child_id) REFERENCES public.children(id);


--
-- Name: attendance attendance_teacher_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.attendance
    ADD CONSTRAINT attendance_teacher_id_fkey FOREIGN KEY (teacher_id) REFERENCES public.users(id);


--
-- Name: children children_group_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.children
    ADD CONSTRAINT children_group_id_fkey FOREIGN KEY (group_id) REFERENCES public.groups(id);


--
-- Name: groups groups_teacher_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.groups
    ADD CONSTRAINT groups_teacher_id_fkey FOREIGN KEY (teacher_id) REFERENCES public.users(id);


--
-- Name: payments payments_child_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.payments
    ADD CONSTRAINT payments_child_id_fkey FOREIGN KEY (child_id) REFERENCES public.children(id);


--
-- PostgreSQL database dump complete
--

\unrestrict yGhuRLYyjFwtnwkoHNU2NY5vVa3KgYceQbZxutHnhetXzbX4TY5ocGn5TUILTGK

