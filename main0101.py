import os
import subprocess
import sys
import telebot
from telebot import types

# التوكن الخاص بك
TOKEN = "8691858693:AAEaG1_0tuOaJtWvrlpbLRhw5xNtg0RWLOU"

print("1. جاري تهيئة البوت...")

try:
    bot = telebot.TeleBot(TOKEN)
    me = bot.get_me()
    print(f"2. تم الاتصال بنجاح! اسم البوت: @{me.username}")
except Exception as e:
    print(f"❌ خطأ في التوكن أو الاتصال بالإنترنت:\n{e}")
    input("\nاضغط Enter للخروج...")
    sys.exit()

BASE_DIR = "hosted_files"
os.makedirs(BASE_DIR, exist_ok=True)

user_states = {}
running_processes = {}


def get_user_dir(user_id):
    user_path = os.path.join(BASE_DIR, str(user_id))
    os.makedirs(user_path, exist_ok=True)
    return user_path


def main_keyboard():
    markup = types.InlineKeyboardMarkup(row_width=2)
    btn_add = types.InlineKeyboardButton("📁 إضافة ملف", callback_data="add_file")
    btn_files = types.InlineKeyboardButton("📂 ملفاتي", callback_data="my_files")
    btn_run = types.InlineKeyboardButton("⚡ تشغيل ملف", callback_data="run_file")
    btn_dev = types.InlineKeyboardButton("🧑‍💻 المطور", callback_data="developer")
    markup.add(btn_add, btn_files)
    markup.add(btn_run)
    markup.add(btn_dev)
    return markup


def back_keyboard():
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("🔙 العودة", callback_data="back_main"))
    return markup


@bot.message_handler(commands=["start"])
def send_welcome(message):
    user_states[message.chat.id] = None
    welcome_text = (
        "أهلاً بك في بوت الاستضافة التلقائي السريع!\nاختر من القائمة أدناه:"
    )
    bot.send_message(message.chat.id, welcome_text, reply_markup=main_keyboard())


@bot.callback_query_handler(func=lambda call: True)
def handle_callbacks(call):
    chat_id = call.message.chat.id

    if call.data == "back_main":
        user_states[chat_id] = None
        bot.edit_message_text(
            "أهلاً بك في بوت الاستضافة التلقائي السريع!\nاختر من القائمة أدناه:",
            chat_id,
            call.message.message_id,
            reply_markup=main_keyboard(),
        )

    elif call.data == "add_file":
        user_states[chat_id] = "waiting_file"
        bot.edit_message_text(
            "أرسل الآن ملف البوت الخاص بك بصيغة .py لرفعه وحفظه:",
            chat_id,
            call.message.message_id,
            reply_markup=back_keyboard(),
        )

    elif call.data == "my_files":
        user_dir = get_user_dir(chat_id)
        files = [f for f in os.listdir(user_dir) if f.endswith(".py")]
        msg = (
            "📂 **ملفاتك المحفوظة:**\n\n" + "\n".join([f"• `{f}`" for f in files])
            if files
            else "📂 لا توجد لديك ملفات محفوظة حالياً."
        )
        bot.edit_message_text(
            msg,
            chat_id,
            call.message.message_id,
            parse_mode="Markdown",
            reply_markup=back_keyboard(),
        )

    elif call.data == "run_file":
        user_dir = get_user_dir(chat_id)
        files = [f for f in os.listdir(user_dir) if f.endswith(".py")]

        if not files:
            bot.answer_callback_query(
                call.id, "لا توجد ملفات مرفوعة لتشغيلها!", show_alert=True
            )
            return

        markup = types.InlineKeyboardMarkup()
        for f in files:
            markup.add(
                types.InlineKeyboardButton(f"▶️ {f}", callback_data=f"exec_{f}")
            )
        markup.add(
            types.InlineKeyboardButton("🔙 العودة", callback_data="back_main")
        )

        bot.edit_message_text(
            "اختر الملف الذي تريد تشغيله:",
            chat_id,
            call.message.message_id,
            reply_markup=markup,
        )

    elif call.data.startswith("exec_"):
        file_name = call.data.replace("exec_", "")
        file_path = os.path.join(get_user_dir(chat_id), file_name)

        if os.path.exists(file_path):
            proc_key = f"{chat_id}_{file_name}"
            if proc_key in running_processes:
                try:
                    running_processes[proc_key].terminate()
                except Exception:
                    pass

            proc = subprocess.Popen(["python", file_path])
            running_processes[proc_key] = proc

            bot.answer_callback_query(call.id, f"تم تشغيل {file_name} بنجاح!")
            bot.send_message(
                chat_id,
                f"🚀 تم تشغيل الملف `{file_name}` بنجاح في الخلفية!",
                parse_mode="Markdown",
                reply_markup=main_keyboard(),
            )

    elif call.data == "developer":
        bot.answer_callback_query(
            call.id, "مطور البوت: @the_Hamd", show_alert=True
        )


@bot.message_handler(content_types=["document"])
def handle_document(message):
    chat_id = message.chat.id

    if user_states.get(chat_id) == "waiting_file":
        file_name = message.document.file_name

        if not file_name.endswith(".py"):
            bot.reply_to(
                message,
                "⚠️ يرجى إرسال ملف ينتهي بـ `.py` فقط!",
                parse_mode="Markdown",
            )
            return

        try:
            user_dir = get_user_dir(chat_id)
            file_info = bot.get_file(message.document.file_id)
            downloaded = bot.download_file(file_info.file_path)

            save_path = os.path.join(user_dir, file_name)
            with open(save_path, "wb") as new_file:
                new_file.write(downloaded)

            user_states[chat_id] = None

            bot.reply_to(
                message,
                f"تم حفظ الملف {file_name} بنجاح!\nيمكنك تشغيله الآن من قائمة (ملفاتي).",
                reply_markup=main_keyboard(),
            )
        except Exception as e:
            bot.reply_to(message, f"❌ حدث خطأ أثناء حفظ الملف:\n`{e}`")


print("3. جاري تشغيل الاستماع للرسائل (Polling)...")
try:
    bot.infinity_polling(skip_pending=True)
except Exception as err:
    print(f"\n❌ توقف البوت بسبب خطأ في الشبكة أو التشغيل:\n{err}")
    input("\nاضغط Enter للخروج...")
