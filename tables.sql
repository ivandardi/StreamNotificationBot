CREATE TABLE IF NOT EXISTS subscribers (
  subscriber_id BIGINT PRIMARY KEY,
  channel_id    BIGINT NOT NULL,
  UNIQUE (subscriber_id, channel_id)
);

CREATE TABLE IF NOT EXISTS streamers (
  streamer_id SERIAL  PRIMARY KEY,
  service_id  TEXT    NOT NULL,
  service     TEXT    NOT NULL,
  username    TEXT    NOT NULL,
  UNIQUE (service, username)
);

CREATE TABLE IF NOT EXISTS subscriptions (
  subscriber_id BIGINT  NOT NULL REFERENCES subscribers (subscriber_id) ON DELETE CASCADE,
  streamer_id   INTEGER NOT NULL REFERENCES streamers   (streamer_id)   ON DELETE CASCADE,
  PRIMARY KEY (subscriber_id, streamer_id)
);
