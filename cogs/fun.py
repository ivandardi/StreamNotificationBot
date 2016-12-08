import random

from discord.ext import commands


class Fun:
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        with open('why.txt', encoding='utf8') as f:
            self.why_list = list(f)

    @commands.command(pass_context=True)
    async def why(self, ctx: commands.context.Context):
        """why

        """

        await self.bot.send_message(ctx.message.channel, random.choice(self.why_list))


def setup(bot):
    bot.add_cog(Fun(bot))
