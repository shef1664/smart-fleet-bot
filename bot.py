import os
import logging
import json
from datetime import datetime
from telegram import Update, WebAppInfo, KeyboardButton, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BOT_TOKEN = os.getenv("BOT_TOKEN", "8663680672:AAGif_fHZP0UZwbMkNo5Pr1cq3Tj4JhCMrM")
WEBAPP_URL = os.getenv("WEBAPP_URL", "https://your-app.railway.app")
DIRECTOR_ID = int(os.getenv("DIRECTOR_ID", "0"))

ROLES = {}

ROLE_LABELS = {
    "driver":    "🚛 Водитель",
    "mechanic":  "🔧 Слесарь",
    "economist": "💰 Экономист",
    "logist":    "🚚 Логист",
    "director":  "📊 Директор",
}

ROLE_DESC = {
    "driver":    "Рейсы · топливо · кабинет",
    "mechanic":  "Ремонты · запчасти · кабинет",
    "economist": "Миксеры · наличные",
    "logist":    "Длинномеры · заказы",
    "director":  "Полный доступ · дашборд",
}

async def notify_director(context, message):
    if DIRECTOR_ID:
        try:
            await context.bot.send_message(DIRECTOR_ID, message)
        except Exception as e:
            logger.error(f"Ошибка уведомления: {e}")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    role = ROLES.get(user.id)
    if not role:
        await update.message.reply_text(
            f"👋 Добрый день, {user.first_name}!\n\n"
            f"Ваш ID: `{user.id}`\n\n"
            f"Для доступа к системе обратитесь к директору.",
            parse_mode="Markdown"
        )
        if DIRECTOR_ID:
            await notify_director(context,
                f"🔔 Новый пользователь:\n{user.first_name} {user.last_name or ''}\n"
                f"@{user.username or 'нет'}\nID: `{user.id}`\n\n"
                f"Назначьте роль:\n`/setrole {user.id} driver`",
            )
        return

    label = ROLE_LABELS.get(role, role)
    desc = ROLE_DESC.get(role, "")
    btn = KeyboardButton(f"📱 Открыть приложение", web_app=WebAppInfo(url=f"{WEBAPP_URL}?role={role}"))
    kb = ReplyKeyboardMarkup([[btn]], resize_keyboard=True)
    await update.message.reply_text(
        f"👋 {user.first_name}!\n\nРоль: {label}\n{desc}\n\nНажмите кнопку ниже 👇",
        reply_markup=kb
    )

async def setrole(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    if uid != DIRECTOR_ID and DIRECTOR_ID != 0:
        await update.message.reply_text("❌ Только для директора.")
        return
    if len(context.args) < 2:
        await update.message.reply_text(
            "Использование: /setrole <id> <роль>\n"
            "Роли: driver, mechanic, economist, logist, director\n"
            "Пример: /setrole 123456789 driver"
        )
        return
    target = int(context.args[0])
    role = context.args[1].lower()
    if role not in ROLE_LABELS:
        await update.message.reply_text(f"❌ Неизвестная роль. Доступные: {', '.join(ROLE_LABELS)}")
        return
    ROLES[target] = role
    await update.message.reply_text(f"✅ {ROLE_LABELS[role]} назначен пользователю {target}")
    try:
        await context.bot.send_message(target, f"✅ Вам назначена роль: {ROLE_LABELS[role]}\nНапишите /start")
    except:
        pass

async def myid(update: Update, context: ContextTypes.DEFAULT_TYPE):
    u = update.effective_user
    role = ROLES.get(u.id, "не назначена")
    await update.message.reply_text(f"👤 {u.first_name}\nID: `{u.id}`\nРоль: {ROLE_LABELS.get(role, role)}", parse_mode="Markdown")

async def roles_list(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != DIRECTOR_ID and DIRECTOR_ID != 0:
        await update.message.reply_text("❌ Только для директора.")
        return
    if not ROLES:
        await update.message.reply_text("Ни одной роли не назначено.")
        return
    text = "👥 Пользователи:\n\n" + "\n".join(f"{uid} — {ROLE_LABELS.get(r,r)}" for uid, r in ROLES.items())
    await update.message.reply_text(text)

async def webapp_data(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    try:
        payload = json.loads(update.message.web_app_data.data)
        action = payload.get("action", "")
        data = payload.get("data", {})
        now = datetime.now().strftime("%d.%m.%Y %H:%M")

        if action == "new_trip":
            auto, driver = data.get("auto","?"), data.get("driver", user.first_name)
            mat, client = data.get("material","?"), data.get("client","?")
            unload = data.get("unload","?")
            has_tn = data.get("has_tn", False)
            await update.message.reply_text(
                f"✅ Рейс сохранён!\n🚛 {auto} · {driver}\n📦 {mat} → {client}\n⚖️ {unload} т\n📄 ТН: {'✓' if has_tn else '⚠️ нет'}"
            )
            await notify_director(context,
                f"🚛 Новый рейс · {now}\n\nМашина: {auto}\nВодитель: {driver}\n"
                f"Материал: {mat} → {client}\nВыгрузка: {unload} т\nТН: {'есть ✅' if has_tn else 'НЕТ ⚠️'}"
            )

        elif action == "shift_start":
            worker = data.get("worker", user.first_name)
            rate = data.get("rate", 6000)
            await update.message.reply_text(f"✅ Смена начата!")
            await notify_director(context, f"🔧 {worker} вышел на смену · {now}\nОклад: ₽{rate:,}")

        elif action == "advance_request":
            worker = data.get("worker", user.first_name)
            amount = data.get("amount", 0)
            comment = data.get("comment", "")
            await update.message.reply_text(f"✅ Запрос аванса ₽{amount:,} отправлен директору.")
            await notify_director(context, f"💸 Запрос аванса · {now}\n{worker}: ₽{amount:,}\n{comment}")

        elif action == "cash_delivered":
            driver = data.get("driver", user.first_name)
            amount = data.get("amount", 0)
            method = data.get("method", "лично")
            await update.message.reply_text(f"✅ Передача ₽{amount:,} зафиксирована.")
            await notify_director(context, f"💵 {driver} передал наличные · {now}\n₽{amount:,} · {method}")

        elif action == "cash_confirmed":
            amount = data.get("amount", 0)
            from_driver = data.get("from_driver", "?")
            await update.message.reply_text(f"✅ Получение ₽{amount:,} подтверждено.")
            await notify_director(context, f"✅ Наличные получены · {now}\nОт: {from_driver} · ₽{amount:,}\nПринял: {user.first_name}")

        elif action == "repair_open":
            auto = data.get("auto","?")
            cat = data.get("category","?")
            desc = data.get("description","?")
            rtype = data.get("type","свой")
            await update.message.reply_text(f"✅ Ремонт открыт! {auto} · {cat}")
            await notify_director(context, f"🔧 Открыт ремонт · {now}\nМашина: {auto}\nКатегория: {cat}\nОписание: {desc}\nТип: {rtype}")

        else:
            await update.message.reply_text("✅ Данные сохранены.")

    except Exception as e:
        logger.error(f"Ошибка обработки данных: {e}")
        await update.message.reply_text("✅ Готово.")

def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("setrole", setrole))
    app.add_handler(CommandHandler("myid", myid))
    app.add_handler(CommandHandler("roles", roles_list))
    app.add_handler(MessageHandler(filters.StatusUpdate.WEB_APP_DATA, webapp_data))
    logger.info("🚛 Умный автопарк запущен!")
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
