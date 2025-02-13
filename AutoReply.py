# meta developer: @pythonsdd
import asyncio
import json
import os
from datetime import datetime, timedelta
from .. import loader, utils

SETTINGS_FILE = "auto_reply.json"

class AutoReplyMod(loader.Module):
    """Version 1.2.14 модуль на автоответчик как у тг премиум"""
    strings = {
        "name": "AutoReply",
        "current_settings": "Текущие настройки:",
        "cooldown_label": "Кулдаун: ",
        "message_label": "Текст автоответа: ",
        "change_cooldown": "Установить кулдаун",
        "change_message": "Установить текст ",
        "cooldown_instruction": "Укажите кулдаун в секундах. Например: .setcooldown 60 для установки кулдауна в 60 секунд.",
        "message_instruction": "Укажите текст автоответа. Например: .setmessage Привет, я не в сети сейчас не могу ответить."
    }

    async def client_ready(self, client, db):
        self.client = client
        self.db = db
        self.cooldown_timers = {}
        self.last_reply_ids = {}
        await self._load_settings()
        me = await self.client.get_me()
        self.my_id = me.id
        self.is_online = False

    async def _load_settings(self):
        self.cooldown = 30
        self.auto_reply_message = "Привет! Сейчас я не в сети, отвечу позже."
        if os.path.exists(SETTINGS_FILE):
            try:
                with open(SETTINGS_FILE, "r") as f:
                    settings = json.load(f)
                    self.cooldown = settings.get("cooldown", self.cooldown)
                    self.auto_reply_message = settings.get("auto_reply_message", self.auto_reply_message)
            except (json.JSONDecodeError, ValueError):
                await self._save_settings()
        else:
            await self._save_settings()

    async def _save_settings(self):
        settings = {"cooldown": self.cooldown, "auto_reply_message": self.auto_reply_message}
        with open(SETTINGS_FILE, "w") as f:
            json.dump(settings, f, indent=4)

    @loader.command(ru_doc="Установить время кулдауна (в секундах).\nПример: .setcooldown 60")
    async def setcooldown(self, message):
        args = utils.get_args_raw(message)
        if not args or not args.isdigit():
            await message.edit(self.strings["cooldown_instruction"])
            return
        self.cooldown = int(args)
        await self._save_settings()
        await message.edit(f"Кулдаун успешно установлен на {self.cooldown} секунд.")

    @loader.command(ru_doc="Установить текст автоответа.\nПример: `.setmessage Привет, я не в сети`")
    async def setmessage(self, message):
        args = utils.get_args_raw(message)
        if not args:
            await message.edit(self.strings["message_instruction"])
            return
        self.auto_reply_message = args
        await self._save_settings()
        await message.edit("Текст автоответа успешно обновлен.")

    @loader.command(ru_doc="Показать текущие настройки автоответчика")
    async def showsettings(self, message):
        await message.edit(
            f"{self.strings['current_settings']}\n"
            f"{self.strings['cooldown_label']} {self.cooldown} секунд\n"
            f"{self.strings['message_label']} {self.auto_reply_message}"
        )

    async def set_offline(self):
        await asyncio.sleep(30)
        self.is_online = False
        print("[Статус] оффлайн.")

    async def watcher(self, message):
        if message.is_private:
            sender = await message.get_sender()
            user_id = sender.id
            if user_id == self.my_id:
                return

            if user_id in self.last_reply_ids:
                try:
                    await self.client.delete_messages(self.my_id, self.last_reply_ids[user_id])
                    del self.last_reply_ids[user_id]
                    print(f"[Автоответ] Старый автоответ удален {sender.username or user_id}")
                except Exception as e:
                    print(f"Ошибка при удалении {user_id}: {e}")

            now = datetime.now()
            last_reply_time = self.cooldown_timers.get(user_id)
            if last_reply_time and now - last_reply_time < timedelta(seconds=self.cooldown):
                print(f"[Кулдаун] Сообщение для {sender.username or user_id} отправлено недавно.")
                return

            if not self.is_online:
                reply = await message.reply(self.auto_reply_message)
                self.last_reply_ids[user_id] = reply.id  
                self.cooldown_timers[user_id] = now  
                print(f"[Автоответ] Новый автоответ отправлен пользователю {sender.username or user_id}.")

    async def client_outgoing_message(self, message):
        """Обработчик исходящих сообщений для активации статуса онлайн"""
        if message.sender.id == self.my_id:  
            self.is_online = True
            await self.set_offline()
            print("[Статус] Аккаунт теперь онлайн.")

    async def main(self):
        with self.client:
            self.client.loop.run_until_complete(self.client.start())
            self.client.loop.run_forever()
