CREATE TABLE IF NOT EXISTS subscribers (
  subscriber_id TEXT PRIMARY KEY,
  channel_id    TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS streamers (
  streamer_id INTEGER PRIMARY KEY AUTOINCREMENT,
  service_id  TEXT    NOT NULL,
  service     TEXT    NOT NULL,
  username    TEXT    NOT NULL,
  is_online   INTEGER NOT NULL CHECK (is_online IN (0, 1)) DEFAULT 0,
  UNIQUE (service, username)
);

CREATE TABLE IF NOT EXISTS subscriptions (
  subscriber_id TEXT    REFERENCES subscribers (subscriber_id),
  streamer_id   INTEGER REFERENCES streamers   (streamer_id),
  PRIMARY KEY (subscriber_id, streamer_id)
);

CREATE TABLE IF NOT EXISTS prefixes (
  guild_id TEXT NOT NULL PRIMARY KEY,
  prefix   TEXT NOT NULL
);