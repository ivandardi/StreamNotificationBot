# Stream Notification Bot

A bot that notifies you when your favorite streamers go online!

## Currently supported services

* Twitch
* Picarto

## Usage and examples

* Subscribe to a streamer
    * `snb?add <service> <username>`
    * Example: `snb?add picarto mykegreywolf`

* Unsubscribe from a streamer
    * `snb?del <service> <username>`
    * Example: `snb?del picarto mykegreywolf`
    
* List subscribed streamers
    * `snb?list`
    
* Subscribe a channel to a streamer
    * `snb?add <service> <username> <channel>`
    * Example: `snb?add picarto mykegreywolf #general`

* Unsubscribe a channel from a streamer
    * `snb?del <service> <username> <channel>`
    * Example: `snb?del picarto mykegreywolf #general`
    
* List subscribed streamers of a channel
    * `snb?list #general`

For more help about any command, type `snb?help <command>`.
Examples:
* `snb?help add`
* `snb?help del`
* `snb?help list`