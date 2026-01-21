"""Telegram bot untuk menjalankan verifikasi SheerID via python-telegram-bot."""

from __future__ import annotations

import asyncio
import logging
import os
from typing import Optional

from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

from tools import Verifikator


logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)


def _format_help(verifikator: Verifikator) -> str:
    tools_list = ", ".join(verifikator.available_tools())
    return (
        "✅ Bot siap membantu verifikasi SheerID.\n\n"
        "Perintah:\n"
        "/start - tampilkan bantuan\n"
        "/tools - daftar tool tersedia\n"
        "/verify <tool> <url> [proxy] - jalankan verifikasi\n\n"
        f"Tool tersedia: {tools_list}\n"
        "Contoh:\n"
        "/verify spotify https://example.sheerid.com/verify/xyz\n"
    )


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    verifikator: Verifikator = context.application.bot_data["verifikator"]
    await update.message.reply_text(_format_help(verifikator))


async def tools_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    verifikator: Verifikator = context.application.bot_data["verifikator"]
    tools_list = "\n".join(f"- {tool}" for tool in verifikator.available_tools())
    await update.message.reply_text(f"Tool tersedia:\n{tools_list}")


def _build_verify_response(payload: dict) -> str:
    if not payload.get("ok"):
        return f"❌ Verifikasi gagal: {payload.get('detail', 'Unknown error')}"
    return f"✅ Verifikasi selesai.\nHasil: {payload.get('result')}"


async def verify_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.message:
        return

    if len(context.args) < 2:
        await update.message.reply_text(
            "Format: /verify <tool> <url> [proxy]\nContoh: /verify spotify https://..."
        )
        return

    tool = context.args[0]
    url = context.args[1]
    proxy: Optional[str] = context.args[2] if len(context.args) > 2 else None

    verifikator: Verifikator = context.application.bot_data["verifikator"]

    await update.message.reply_text("⏳ Memulai verifikasi...")

    loop = asyncio.get_running_loop()
    try:
        result = await loop.run_in_executor(None, verifikator.verify, tool, url, proxy)
        await update.message.reply_text(_build_verify_response(result), parse_mode=ParseMode.HTML)
    except Exception as exc:  # noqa: BLE001
        logger.exception("Verifikasi gagal")
        await update.message.reply_text(f"❌ Terjadi kesalahan: {exc}")


def main() -> None:
    token = os.getenv("BOT_TOKEN")
    if not token:
        raise RuntimeError("BOT_TOKEN environment variable belum di-set")

    application = ApplicationBuilder().token(token).build()
    application.bot_data["verifikator"] = Verifikator()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", start))
    application.add_handler(CommandHandler("tools", tools_command))
    application.add_handler(CommandHandler("verify", verify_command))

    application.run_polling()


if __name__ == "__main__":
    main()
