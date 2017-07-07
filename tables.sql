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

CREATE OR REPLACE FUNCTION delete_empty() RETURNS trigger AS
$$
BEGIN
  IF (SELECT COUNT(*) FROM subscriptions WHERE subscriber_id = OLD.subscriber_id) = 0 THEN
    DELETE FROM subscribers
    WHERE subscribers.subscriber_id = OLD.subscriber_id;
  END IF;

  IF (SELECT COUNT(*) FROM subscriptions WHERE streamer_id = OLD.streamer_id) = 0 THEN
    DELETE FROM streamers
    WHERE streamers.streamer_id = OLD.streamer_id;
  END IF;

  RETURN OLD;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS empty_subscribers on subscriptions;
CREATE TRIGGER empty_subscribers
  AFTER DELETE
  ON subscriptions
  FOR EACH ROW EXECUTE PROCEDURE delete_empty();
