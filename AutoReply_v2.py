#─ ──────────────────────
#────────██████──────────
#──────██──────██────────
#─────█─▄▀█──█▀▄─█───────
#────▐▌──────────▐▌──────
#────█▌▀▄──▄▄──▄▀▐█──────
#───▐██──▀▀──▀▀──██▌─────
#──▄████▄──▐▌──▄████▄────
#─█████████████████─██─ ─
# Copyright (c) 2025, Vamhost/Vamics  
#Commercial use and modifications are prohibited without the author's #permission.
#All changes must include a license notice.
#Distribution in source or binary form with modifications is allowed only #for non-commercial purposes.
#Creating closed forks or integrating into closed software is prohibited. #Violation of the license terms will result in the cancellation of the #license.
#Using this software means agreeing to the terms of the license.
#------------------------------------------------------------------------#---------
# Name: AutoReply  
# meta developer: @pythonsdd
# Description: Modified Telegram Premium Auto-reply 
# Author: @pythonsdd (Vamics)
# GitHub repo: https://github.com/i9opkas/Modyles_Vamics  
# Commands:  
# .autoreply on/off
#------------------------------------------------------------------------#---------
import asyncio
import time
from .. import loader

class AutoReplyMod(loader.Module):
    """модифицированный telegram премиум автоответчик"""

    strings = {
        "name": "AutoReply",
        "enabled": "🌘Автоответчик включен.",
        "disabled": "👾Автоответчик выключен."
    }

    def __init__(self):
        self.config = loader.ModuleConfig(
            "enabled", True, lambda: "Включен ли автоответчик?",
            "cooldown", 50, lambda: "Кулдаун статуса оффлайн/онлайн в секундах.",
            "reply_cooldown", 20, lambda: "Кулдаун между автоответами в секундах.",
            "message", "Привет! Сейчас я не в сети, отвечу позже.", lambda: "Текст автоответа."
        )
        self.global_cooldown_timer = 0  
        self.last_reply_time = {}  
        self.last_reply_ids = {}

    async def client_ready(self, client, db):
        self.client = client
        me = await self.client.get_me()
        self.my_id = me.id

    async def watcher(self, message):
        """Обработчик входящих сообщений"""
        if not self.config["enabled"] or not message.is_private:
            return

        sender = await message.get_sender()
        user_id = sender.id
        now = time.time()

        global_cooldown = self.config["cooldown"]  
        reply_cooldown = self.config["reply_cooldown"]  
        reply_message = self.config["message"]

        if user_id == self.my_id:
            self.global_cooldown_timer = now
            chat_id = message.to_id.user_id if message.to_id else None
            if chat_id and chat_id in self.last_reply_ids:
                try:
                    await self.client.delete_messages(self.my_id, self.last_reply_ids[chat_id])
                    del self.last_reply_ids[chat_id] 
                except Exception:
                    pass
            return

        if now - self.global_cooldown_timer < global_cooldown:
            return

        if user_id in self.last_reply_time and now - self.last_reply_time[user_id] < reply_cooldown:
            return

        if user_id in self.last_reply_ids:
            try:
                await self.client.delete_messages(self.my_id, self.last_reply_ids[user_id])
            except Exception:
                pass

        reply = await message.reply(reply_message)
        self.last_reply_ids[user_id] = reply.id 
        self.last_reply_time[user_id] = now 

        self.global_cooldown_timer = now

    @loader.command(ru_doc="Включить/выключить автоответчик.\nПример: .autoreply on/off")
    async def autoreply(self, message):
        """Включает или отключает автоответчик"""
        args = message.text.split(maxsplit=1)[1].lower() if len(message.text.split()) > 1 else ""
        if args in ["on", "off"]:
            self.config["enabled"] = args == "on"
            await message.edit(self.strings["enabled"] if args == "on" else self.strings["disabled"])
        else:
            await message.edit("Используйте .autoreply on/off.")
