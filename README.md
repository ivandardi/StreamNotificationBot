# Stream Notification Bot v2.0.0

A bot that notifies you when your favorite streamers go online!

## Currently supported services

* Twitch
* Picarto

## Usage and examples

* Subscribing to streamers:
    * `snb?{service} add username`
    * Example: `snb?{service} add mykegreywolf`

* Subscribing a channel to streamers:
    * `snb?{service} add username channel`
    * Example: `snb?{service} add mykegreywolf #general`
    
* Unsubscribing to streamers:
    * `snb?{service} del username`
    * Example: `snb?{service} del mykegreywolf`

* Unsubscribing a channel to streamers:
    * `snb?{service} del username channel`
    * Example: `snb?{service} del mykegreywolf #general`
    
* Listing your streamers:
    * `snb?{service} list`
    * `Example: snb?{service} list`

* Listing a channel's streamers:
    * `snb?{service} list channel`
    * Example: `snb?{service} list #general`
    
## Running the bot

To invoke the bot, be in the root directory and execute

```
TOKEN_DISCORD=token TOKEN_TWITCH=token TOKEN_PICARTO=token python3.6 -m bot
```