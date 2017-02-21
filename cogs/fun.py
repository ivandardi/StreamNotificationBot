import random

from discord.ext import commands

from notification import httpclient


class Fun:
    def __init__(self, bot):
        self.bot = bot
        self.why_list = None

    @commands.command()
    async def why(self, ctx):
        """why

        DISCLAIMER: This command fetches from https://xkcd.com/why.txt .
        I am not responsible for anything that this command outputs.

        """

        if not self.why_list:
            async with httpclient.client.get('https://xkcd.com/why.txt') as r:
                self.why_list = await r.text()
                self.why_list = self.why_list.split('\n')

        await ctx.send(random.choice(self.why_list))


def setup(bot):
    bot.add_cog(Fun(bot))
