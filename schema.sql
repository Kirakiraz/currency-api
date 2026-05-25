CREATE TABLE IF NOT EXISTS public.exchange_rate
(
    date date NOT NULL,
    base_currency character varying(3) COLLATE pg_catalog."default",
    target_currency character varying(3) COLLATE pg_catalog."default" NOT NULL,
    rate numeric(10,4),
    updated_at timestamp without time zone,
    CONSTRAINT exchange_rate_pkey PRIMARY KEY (date, target_currency)
)