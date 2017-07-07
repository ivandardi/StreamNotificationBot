from .picarto import Picarto
from .twitch import Twitch


def setup(bot):
    bot.add_cog(Picarto(bot))
    bot.add_cog(Twitch(bot))
