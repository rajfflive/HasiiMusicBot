LANG = {
    "en": {
        "start_pm": "Hello {0}!\nI'm **{1}**, a music bot.\nSend /help to see commands.",
        "start_gp": "Thanks for adding me, **{0}**!\nUse /play to play music.",
        "help_menu": "**Available Commands:**\n/play <song> - Play music\n/skip - Skip current\n/stop - Stop playing",
        "pinging": "Pinging...",
        "ping_pong": "**Pong!**\nLatency: `{0}ms`\nUptime: `{1}`\nAssistant Ping: `{2}ms`\nRAM: `{3}`\nCPU: `{4}%`\nActive Chats: `{5}`",
        "start_settings": "**Settings for {0}**",
        "bl_user_notify": "You are blacklisted.",
    }
}

def language():
    def decorator(func):
        async def wrapper(_, message):
            message.lang = LANG["en"]
            return await func(_, message)
        return wrapper
    return decorator
