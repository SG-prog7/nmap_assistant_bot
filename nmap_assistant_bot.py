#!/usr/bin/env python3
# nmap_assistant_bot.py — этичный помощник (текстовый режим)

import os
import random
import re
import requests
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from dotenv import load_dotenv

load_dotenv()
BOT_TOKEN = os.getenv("NMAP_ASSISTANT_BOT_TOKEN")

# Словарь сервисов
SERVICES = {
    21: "ftp", 22: "ssh", 23: "telnet", 25: "smtp",
    53: "dns", 80: "http", 110: "pop3", 143: "imap",
    443: "https", 3306: "mysql", 5432: "postgresql",
    3389: "rdp", 8000: "http-alt", 8080: "http-alt"
}

# === Функции ===
def simulate_scan(target: str):
    open_ports = [(80, "http"), (443, "https")]
    if re.search(r"(localhost|127\.0\.0\.1|192\.168\.|10\.|172\.1[6-9]|172\.2[0-9]|172\.3[0-1])", target):
        open_ports.append((22, "ssh"))
        if random.random() < 0.3:
            open_ports.append(random.choice([(3306, "mysql"), (5432, "postgresql")]))
    elif "scanme" in target.lower():
        open_ports = [(22, "ssh"), (80, "http")]
    return sorted(open_ports)

def analyze_security_headers(url: str):
    try:
        r = requests.get(
            url,
            headers={"User-Agent": "Mozilla/5.0"},
            timeout=5,
            verify=False
        )
        missing = []
        for h in ["X-Frame-Options", "Content-Security-Policy",
                 "X-Content-Type-Options", "X-XSS-Protection",
                 "Strict-Transport-Security"]:
            if not r.headers.get(h):
                missing.append(h)
        return {
            "status": r.status_code,
            "server": r.headers.get("Server", "—"),
            "missing": missing
        }
    except:
        return None

# === Обработчики ===
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = (
        "⚠️ *Nmap Assistant Bot*\n\n"
        "Этот бот — *учебный инструмент*.\n"
        "Он НЕ сканирует хосты автоматически.\n\n"
        "🔒 Сканирование без разрешения — незаконно.\n"
        "✅ Используйте ТОЛЬКО для:\n"
        "• Своих машин\n"
        "• Лабораторий (DVWA, HTB)\n"
        "• Систем с согласия владельца\n\n"
        "Команды:\n"
        "• `/cmd <IP>` — симуляция сканирования портов\n"
        "• `/probe <URL>` — анализ security headers"
    )
    await update.message.reply_text(msg, parse_mode="Markdown")

async def cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("UsageId: `/cmd <IP>`")
        return
    target = context.args[0].strip()
    if not re.match(r"^[a-zA-Z0-9.-]+$", target):
        await update.message.reply_text("❌ Некорректная цель.")
        return
    open_ports = simulate_scan(target)
    res = "✅ Открытые порты:\n" + "\n".join(f"• {p}/tcp → {s}" for p, s in open_ports) if open_ports else "📭 Все порты закрыты."
    await update.message.reply_text(res)

async def probe(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("UsageId: `/probe <URL>`\nПример: `/probe https://google.com`")
        return

    url = context.args[0].strip()
    if not url.startswith(("http://", "https://")):
        url = "http://" + url

    result = analyze_security_headers(url)
    if not result:
        await update.message.reply_text("❌ Ошибка при запросе к URL.")
        return

    sec_lines = []
    for name in [
        "X-Frame-Options", "Content-Security-Policy",
        "X-Content-Type-Options", "X-XSS-Protection",
        "Strict-Transport-Security"
    ]:
        mark = "✅" if name not in result["missing"] else "❌"
        sec_lines.append(f"{mark} {name}: {'Missing' if name in result['missing'] else 'OK'}")

    response = (
        f"Status: {result['status']}\n"
        f"Server: {result['server']}\n\n"
        "🛡️ Security Headers:\n" + "\n".join(sec_lines)
    )
    await update.message.reply_text(response)

# === Запуск ===
def main():
    if not BOT_TOKEN:
        print("❌ BOT_TOKEN не найден в .env")
        return

    requests.packages.urllib3.disable_warnings()

    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("cmd", cmd))
    app.add_handler(CommandHandler("probe", probe))

    print("✅ Nmap Assistant Bot (text-only) запущен.")
    app.run_polling()

if __name__ == "__main__":
    main()