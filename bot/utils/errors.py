class StreamNotificationBotError(Exception):
    pass


class InvalidUsernameError(StreamNotificationBotError):
    pass


class StreamerNotFoundError(StreamNotificationBotError):
    pass


class StreamerAlreadyExists(StreamNotificationBotError):
    pass


class NotSubscribedError(StreamNotificationBotError):
    pass


class InvalidChannelError(StreamNotificationBotError):
    pass


class UnexpectedApiError(StreamNotificationBotError):
    pass
