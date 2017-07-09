CREATE TABLE IF NOT EXISTS streamers (
  streamer_id SERIAL  PRIMARY KEY,
  service_id  TEXT    NOT NULL,
  service     TEXT    NOT NULL,
  username    TEXT    NOT NULL,
  UNIQUE (service, username)
);

CREATE TABLE IF NOT EXISTS subscriptions (
  subscriber_id BIGINT  NOT NULL,
  streamer_id   INTEGER NOT NULL REFERENCES streamers (streamer_id) ON DELETE CASCADE,
  PRIMARY KEY (subscriber_id, streamer_id)
);

CREATE OR REPLACE FUNCTION delete_empty() RETURNS trigger AS
$$
BEGIN
  IF (SELECT COUNT(*) FROM subscriptions WHERE streamer_id = OLD.streamer_id) = 0 THEN
    DELETE FROM streamers
    WHERE streamers.streamer_id = OLD.streamer_id;
  END IF;

  RETURN OLD;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS empty_streamers on subscriptions;
CREATE TRIGGER empty_streamers
  AFTER DELETE
  ON subscriptions
  FOR EACH ROW EXECUTE PROCEDURE delete_empty();
