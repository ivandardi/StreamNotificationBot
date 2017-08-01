import pytoml

with open('strings.toml') as f:
    _strings = pytoml.load(f)

database_queries = _strings['database']

help_strings = _strings['help_strings']
add_command_help = help_strings['add_command_help']
del_command_help = help_strings['del_command_help']
list_command_help = help_strings['list_command_help']
enable_command_help = help_strings['enable_command_help']
disable_command_help = help_strings['disable_command_help']

group_command_help = '\n'.join([
    add_command_help,
    del_command_help,
    list_command_help,
    enable_command_help,
    disable_command_help
])

bot_description = f"""\
Hello! I am the StreamNotification bot created to notify you when streamers go online!

Bot server for announcements, complaints, feedback and suggestions: https://discord.gg/xrzJhqq

Currently supported services:
  - Twitch
  - Picarto
  
Note that to manage a Discord channel subscription, you need one of the following:
  - The "Manage Channels" permission
  - The "Notification Manager" role

==== HOW TO USE THE BOT ====

{group_command_help}

==== All Commands ====

"""
