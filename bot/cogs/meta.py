import datetime
import logging
import os
from collections import Counter

import discord.utils
from discord.ext import commands

log = logging.getLogger(__name__)


class Meta:
    """Commands that deal with the bot itself."""

    def __init__(self, bot):
        self.bot = bot

    def _bot_uptime(self):
        now = datetime.datetime.utcnow()
        delta = now - self.bot.uptime
        hours, remainder = divmod(int(delta.total_seconds()), 3600)
        minutes, seconds = divmod(remainder, 60)
        days, hours = divmod(hours, 24)

        fmt = '{h}h {m}m {s}s'
        if days:
            fmt = '{d}d ' + fmt

        uptime = fmt.format(d=days, h=hours, m=minutes, s=seconds)
        return uptime

    @commands.command()
    async def uptime(self, ctx: commands.Context):
        """Tell for how long the bot has been up."""

        await ctx.send(f'Uptime: **{self._bot_uptime()}**')

    @commands.command()
    @commands.guild_only()
    async def clean(self, ctx: commands.Context, limit=100):
        """Deletes the bot's messages up to the most 100 recent messages."""

        def is_me(m):
            return m.author.id == self.bot.user.id

        try:
            deleted = await ctx.channel.purge(limit=limit, check=is_me)
            await ctx.send(f'Deleted {len(deleted)} message(s)', delete_after=5)
        except discord.Forbidden:
            await ctx.send('The bot needs the Manage Messages permission to execute this command!')

    @commands.command(aliases=['join'])
    async def invite(self, ctx: commands.Context):
        """Provide the invite link for the bot. Danny made this command."""

        perms = discord.Permissions()
        perms.add_reactions = True
        perms.read_messages = True
        perms.send_messages = True
        perms.embed_links = True
        perms.read_message_history = True
        perms.manage_messages = True

        link = discord.utils.oauth_url(self.bot.user.id, permissions=perms)
        await ctx.send(f'Invite link: {link}')

    @commands.command()
    async def version(self, ctx: commands.Context):
        """Tell the version of the bot"""

        await ctx.send('The StreamNotificationBot is currently in version 2.0.0')

    @commands.command(aliases=['info', 'source'])
    async def about(self, ctx: commands.Context):
        """Tells you information about the bot itself."""
        cmd = r'git show -s HEAD~3..HEAD --format="[{}](https://github.com/ivandardi/StreamNotificationBot/commit/%H) %s (%cr)"'
        if os.name == 'posix':
            cmd = cmd.format(r'\`%h\`')
        else:
            cmd = cmd.format(r'`%h`')

        revision = os.popen(cmd).read().strip()
        embed = discord.Embed(description='Latest Changes:\n' + revision)
        embed.title = 'Official Bot Server Invite'
        embed.url = 'https://discord.gg/xrzJhqq'
        embed.colour = 0x738bd7  # blurple

        try:
            owner = self._owner
        except AttributeError:
            owner = self._owner = await self.bot.get_user_info(129819557115199488)

        embed.set_author(name=f'Owner: {str(owner)}', icon_url=owner.avatar_url)
        embed.set_footer(text='Made with discord.py', icon_url='http://i.imgur.com/5BFecvA.png')
        embed.timestamp = self.bot.uptime

        # statistics
        total_members = sum(len(s.members) for s in self.bot.guilds)
        total_online = sum(1 for m in self.bot.get_all_members() if m.status != discord.Status.offline)
        unique_members = set(self.bot.get_all_members())
        unique_online = sum(1 for m in unique_members if m.status != discord.Status.offline)
        text = sum(1 for c in self.bot.get_all_channels() if not isinstance(c, discord.VoiceChannel))

        members = '%s total\n%s online\n%s unique\n%s unique online' % (
            total_members, total_online, len(unique_members), unique_online)
        embed.add_field(name='Members', value=members)
        embed.add_field(name='Channels', value=f'{text} total')
        embed.add_field(name='Guilds', value=len(self.bot.guilds))
        embed.add_field(name='Uptime', value=self._bot_uptime())

        await ctx.send(embed=embed)


def setup(bot):
    bot.add_cog(Meta(bot))
