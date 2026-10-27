import os
import random
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

logging.basicConfig(level=logging.INFO)
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
ADMIN_GROUP_ID = -1003812845388
WELCOME_PHOTO = os.path.join("photos", "welcome.jpg")

# Add character photos to photos/ using these exact filenames (JPG or PNG):
# palto.jpg, marat.jpg, adidas.jpg, eralash.jpg, zima.jpg, turbo.jpg,
# aigul.jpg, kaschey.jpg, irina.jpg, natasha.jpg
CHARACTERS = {
    "palto": ("Андрей Пальто", "Ты вдумчивый человек с внутренним стержнем. Стараешься поступать по совести и не терять себя под давлением.", "palto.jpg"),
    "marat": ("Марат", "Ты эмоциональный, смелый и сильно зависишь от того, кто рядом. Важно научиться выбирать собственный путь.", "marat.jpg"),
    "adidas": ("Вова Адидас", "Ты уверенный и амбициозный лидер. Умеешь брать ответственность, но иногда можешь слишком давить на окружающих.", "adidas.jpg"),
    "eralash": ("Ералаш", "Ты находчивый, общительный и умеешь выкручиваться из сложных ситуаций. Юмор — твоя сильная сторона.", "eralash.jpg"),
    "zima": ("Зима", "Ты спокойный стратег: сначала наблюдаешь, потом действуешь. Ценишь порядок и контроль.", "zima.jpg"),
    "turbo": ("Турбо", "Ты прямолинейный, энергичный и верный своим людям. Иногда стоит подумать, прежде чем бросаться в бой.", "turbo.jpg"),
    "aigul": ("Айгуль", "Ты чувствительный и искренний человек. Для тебя важны близость, доверие и возможность быть собой.", "aigul.jpg"),
    "kaschey": ("Кащей", "Ты независимый, осторожный и не любишь показывать слабость. Учись иногда доверять тем, кто этого заслуживает.", "kaschey.jpg"),
    "irina": ("Ирина Сергеевна", "Ты рассудительный человек с сильным чувством ответственности. Стараешься держать ситуацию под контролем и поступать правильно.", "irina.jpg"),
    "natasha": ("Наташа", "Ты самостоятельная, наблюдательная и умеешь отстаивать себя. Тебе важно, чтобы к тебе относились с уважением.", "natasha.jpg"),
}

# Каждый вариант ответа добавляет баллы одному архетипу.
QUESTIONS = [
    ("Что ты сделаешь, если друга несправедливо обидели?", [
        ("Попытаюсь разобраться и защитить его", "palto"),
        ("Сразу заступлюсь, не думая о последствиях", "turbo"),
        ("Сначала оценю, кто и зачем это сделал", "zima"),
        ("Поддержу друга и поговорю с ним наедине", "aigul"),
    ]),
    ("Что для тебя важнее всего?", [
        ("Совесть и собственные принципы", "palto"),
        ("Уважение и положение среди других", "adidas"),
        ("Верность близким", "marat"),
        ("Свобода и независимость", "kaschey"),
    ]),
    ("Как ты ведёшь себя в конфликте?", [
        ("Стараюсь решить всё словами", "irina"),
        ("Отвечаю прямо и жёстко", "turbo"),
        ("Ищу хитрый выход", "eralash"),
        ("Сохраняю спокойствие и просчитываю шаги", "zima"),
    ]),
    ("Какую роль ты обычно занимаешь в компании?", [
        ("Лидер, который принимает решения", "adidas"),
        ("Тот, кто разряжает обстановку", "eralash"),
        ("Надёжный друг рядом", "marat"),
        ("Наблюдатель, который всё замечает", "natasha"),
    ]),
    ("Что тебя сильнее всего задевает?", [
        ("Предательство", "marat"),
        ("Когда меня пытаются контролировать", "kaschey"),
        ("Несправедливость", "palto"),
        ("Неуважение и пренебрежение", "natasha"),
    ]),
    ("Как ты принимаешь важные решения?", [
        ("По совести, даже если трудно", "palto"),
        ("Быстро и уверенно", "adidas"),
        ("Обдумываю все варианты", "zima"),
        ("Слушаю чувства и близких", "aigul"),
    ]),
    ("Что лучше описывает твой характер?", [
        ("Спокойный и ответственный", "irina"),
        ("Смелый и импульсивный", "turbo"),
        ("Хитрый и находчивый", "eralash"),
        ("Самостоятельный и закрытый", "kaschey"),
    ]),
    ("Что для тебя значит сила?", [
        ("Уметь отвечать за свои поступки", "irina"),
        ("Не бросать своих", "marat"),
        ("Не позволять собой командовать", "natasha"),
        ("Уметь сохранять контроль", "zima"),
    ]),
]

AGE_OPTIONS = ["До 16 лет", "16–18 лет", "19–25 лет", "26–35 лет", "36 лет и старше"]
GENDER_OPTIONS = ["Мужской", "Женский"]

def reset(context):
    context.user_data.clear()
    context.user_data["scores"] = {key: 0 for key in CHARACTERS}
    context.user_data["answers"] = []

def keyboard(options, prefix):
    return InlineKeyboardMarkup([[InlineKeyboardButton(label, callback_data=f"{prefix}:{i}")]
                                 for i, label in enumerate(options)])

def display_username(user):
    if user.username:
        return f"@{user.username}"
    full_name = " ".join(part for part in [user.first_name, user.last_name] if part)
    return full_name or f"user_id={user.id}"

async def notify_group(context, text):
    try:
        await context.bot.send_message(chat_id=ADMIN_GROUP_ID, text=text)
    except Exception:
        logging.exception("Не удалось отправить уведомление в группу %s", ADMIN_GROUP_ID)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    reset(context)
    user = update.effective_user
    context.user_data["visitor_notified"] = True
    await notify_group(context, f"👀 Открыл(а) бота\nНикнейм/имя: {display_username(user)}")
    text = ("🧩 *Кто ты из «Слова пацана»?*\n\n"
            "Ответь на вопросы и узнай, на какого персонажа ты похож.\n"
            "Это развлекательный тест, а не психологическая диагностика.\n\n"
            "*1/10. Сколько тебе лет?*")
    if os.path.isfile(WELCOME_PHOTO):
        with open(WELCOME_PHOTO, "rb") as photo:
            await update.message.reply_photo(photo=photo, caption=text, parse_mode="Markdown",
                                             reply_markup=keyboard(AGE_OPTIONS, "age"))
    else:
        await update.message.reply_text(text + "\n\n_(Добавь фото в photos/welcome.jpg, чтобы оно появлялось здесь.)_",
                                        parse_mode="Markdown", reply_markup=keyboard(AGE_OPTIONS, "age"))

async def quiz_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    data = q.data

    if data.startswith("age:"):
        i = int(data.split(":")[1])
        context.user_data["age"] = AGE_OPTIONS[i]
        user = q.from_user
        await notify_group(context, f"🎂 Указал(а) возраст\nНикнейм/имя: {display_username(user)}\nВозраст: {AGE_OPTIONS[i]}")
        # Не редактируем приветственное фото как текст: Telegram этого не позволяет.
        await q.message.reply_text("*2/10. Какого ты пола?*",
                                   parse_mode="Markdown",
                                   reply_markup=keyboard(GENDER_OPTIONS, "gender"))
        return

    if data.startswith("gender:"):
        i = int(data.split(":")[1])
        context.user_data["gender"] = GENDER_OPTIONS[i]
        context.user_data["q_index"] = 0
        await send_question(q.message, context)
        return

    if data.startswith("answer:"):
        _, qi, oi = data.split(":")
        qi, oi = int(qi), int(oi)
        option_label, character_key = QUESTIONS[qi][1][oi]
        context.user_data["scores"][character_key] += 1
        context.user_data["answers"].append((qi, oi))
        next_q = qi + 1
        if next_q < len(QUESTIONS):
            context.user_data["q_index"] = next_q
            await send_question(q.message, context)
        else:
            await show_result(q.message, context)

async def send_question(message, context):
    qi = context.user_data["q_index"]
    prompt, options = QUESTIONS[qi]
    buttons = [[InlineKeyboardButton(label, callback_data=f"answer:{qi}:{oi}")]
               for oi, (label, _) in enumerate(options)]
    # Отправляем новый текст, чтобы переход работал и после приветственного фото.
    await message.reply_text(f"*{qi + 3}/10. {prompt}*",
                             parse_mode="Markdown",
                             reply_markup=InlineKeyboardMarkup(buttons))

async def show_result(message, context):
    scores = context.user_data["scores"]
    gender = context.user_data.get("gender", "Мужской")
    female_keys = {"aigul", "irina", "natasha"}
    eligible = female_keys if gender == "Женский" else set(CHARACTERS) - female_keys
    eligible_scores = {key: scores[key] for key in eligible}
    high = max(eligible_scores.values())
    winners = [key for key, score in eligible_scores.items() if score == high]
    winner = random.choice(winners)
    name, description, photo_name = CHARACTERS[winner]
    photo_path = os.path.join("photos", photo_name)
    caption = (f"🎬 *Твой результат: {name}!*\n\n{description}\n\n"
               f"Возраст: {context.user_data.get('age', '—')}\n"
               f"Пол: {context.user_data.get('gender', '—')}\n\n"
               "Хочешь пройти ещё раз? Напиши /start")
    if os.path.isfile(photo_path):
        with open(photo_path, "rb") as photo:
            await message.reply_photo(photo=photo, caption=caption, parse_mode="Markdown")
    else:
        await message.reply_text(caption + "\n\n_Чтобы показывать фото, добавь файл персонажа в папку photos/._",
                                 parse_mode="Markdown")

def main():
    if not TOKEN:
        raise RuntimeError("Установи переменную окружения TELEGRAM_BOT_TOKEN с токеном от BotFather.")
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(quiz_callback))
    app.run_polling()

if __name__ == "__main__":
    main()
