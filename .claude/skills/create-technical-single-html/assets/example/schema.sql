-- Order alerts — DDL draft (example)
CREATE TABLE alert_events (
    id          uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    order_id    bigint      NOT NULL,
    kind        varchar(16) NOT NULL,          -- SHIPPED | DELAYED
    source      varchar(32) NOT NULL,
    source_ref  varchar(128) NOT NULL,
    occurred_at timestamptz NOT NULL,
    CONSTRAINT uq_alert_events_source UNIQUE (source, source_ref)
);

CREATE TABLE alert_deliveries (
    id          uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    event_id    uuid NOT NULL REFERENCES alert_events(id),
    status      varchar(16) NOT NULL DEFAULT 'SCHEDULED',   -- SCHEDULED | SENT | SEND_FAILED
    attempts    smallint NOT NULL DEFAULT 0,
    sent_at     timestamptz,
    CONSTRAINT ck_alert_deliveries_sent CHECK (status <> 'SENT' OR sent_at IS NOT NULL)
);
CREATE INDEX ix_alert_deliveries_due ON alert_deliveries (status) WHERE status <> 'SENT';
