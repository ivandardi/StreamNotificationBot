import atexit

import aiohttp

client = aiohttp.ClientSession()


@atexit.register
def close_connection():
    client.close()
