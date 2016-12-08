CREATE TABLE IF NOT EXISTS users (
  user_id    sqlite3_uint64 PRIMARY KEY,
  channel_id sqlite3_uint64 NOT NULL
);

CREATE TABLE IF NOT EXISTS streamers (
  streamer_id INTEGER PRIMARY KEY AUTOINCREMENT,
  username    TEXT    NOT NULL,
  service     TEXT    NOT NULL,
  is_online   BOOLEAN NOT NULL CHECK (is_online IN (0, 1)) DEFAULT 0,
  UNIQUE (username, service)
);

CREATE TABLE IF NOT EXISTS subscriptions (
  user_id     sqlite3_uint64 REFERENCES users     (user_id)     ON DELETE CASCADE,
  streamer_id INTEGER        REFERENCES streamers (streamer_id) ON DELETE CASCADE,
  PRIMARY KEY (user_id, streamer_id)
);
