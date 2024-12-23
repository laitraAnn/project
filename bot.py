import asyncio
import logging
from datetime import datetime, timedelta
import pytz
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler, filters, 
    ContextTypes, ConversationHandler, CallbackQueryHandler
)
from apscheduler.schedulers.asyncio import AsyncIOScheduler
import json
import os
pid = os.getpid()
print(pid)



def save_plans_to_json(filename='plans.json'):
    logging.info("Сохранение планов в файл.")
    try:
        # Преобразуем планы для сериализации
        serializable_plans = {
            user_id: [
                {
                    'date': plan['date'].strftime('%Y-%m-%d'),  # Преобразуем дату в строку
                    'title': plan['title'],
                    'time': plan['time'].strftime('%H:%M') if plan['time'] else None
                }
                for plan in user_plans
            ]
            for user_id, user_plans in plans.items()
        }
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(serializable_plans, f, ensure_ascii=False, indent=4)
        logging.info("Планы успешно сохранены.")
        print("Планы успешно сохранены.")
    except Exception as e:
        logging.error(f"Ошибка при сохранении планов: {e}")

def load_plans_from_json(filename='plans.json'):
    global plans
    try:
        logging.info("Загрузка планов из файла.")
        with open(filename, 'r', encoding='utf-8') as f:
            loaded_plans = json.load(f)
            # Преобразуем загруженные планы обратно в нужный формат
            plans = {
                int(user_id): [
                    {
                        'date': datetime.strptime(plan['date'], '%Y-%m-%d').date(),  # Преобразуем строку обратно в date
                        'title': plan['title'],
                        'time': datetime.strptime(plan['time'], '%H:%M').time() if plan['time'] else None
                    }
                    for plan in user_plans
                ]
                for user_id, user_plans in loaded_plans.items()
            }
        logging.info("Планы успешно загружены.")
    except FileNotFoundError:
        logging.warning("Файл не найден, инициализация пустого словаря.")
        plans = {}
    except json.JSONDecodeError:
        logging.error("Ошибка декодирования JSON. Файл может быть поврежден.")
        plans = {}
    except Exception as e:
        logging.error(f"Ошибка при загрузке планов: {e}")
        
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
scheduler = AsyncIOScheduler()
# Глобальные переменные
TOKEN = "7690640025:AAH0FmVZk1yJyYren7ipYDL22XRK6bczaEA"  # Замените на ваш токен
LOCAL_TZ = pytz.timezone('Europe/Moscow')
plans = {}

# Состояния для диалогов
CHOOSE_DATE, ENTER_PLAN, ENTER_TIME = range(3)

def get_main_keyboard():
    keyboard = [
        [KeyboardButton("✏️ Добавить план"), KeyboardButton("👀 Показать планы")],
        [KeyboardButton("📅 Планы на сегодня"), KeyboardButton("❌ Удалить план")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)


async def delete_plan_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text(
        'Выберите дату для удаления плана:',
        reply_markup=get_date_keyboard()
    )
    return CHOOSE_DATE

async def delete_plan_for_date(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()

    try:
        selected_date = datetime.strptime(query.data, "%d.%m.%Y").date()
        user_id = update.effective_user.id
        
        user_plans = [
            plan for plan in plans.get(user_id, []) 
            if plan['date'] == selected_date
        ]

        if user_plans:
            plans_text = f"🌟 Планы на {selected_date.strftime('%d.%m.%Y')}:\n\n"
            for idx, plan in enumerate(user_plans, start=1):
                time_str = plan['time'].strftime('%H:%M') if plan['time'] else 'Без времени'
                plans_text += f"{idx}. {plan['title']} ({time_str})\n"
            
            await query.message.reply_text(
                plans_text + "\nВведите номер плана для удаления или напишите 'все' для удаления всех планов.",
                reply_markup=get_main_keyboard()
            )
            context.user_data['selected_date'] = selected_date
            return ENTER_PLAN  # Используем ENTER_PLAN для обработки ввода
        else:
            await query.message.reply_text(
                f"На {selected_date.strftime('%d.%m.%Y')} нет запланированных задач.", 
                reply_markup=get_main_keyboard()
            )
            return ConversationHandler.END
    
    except ValueError:
        await query.message.reply_text(
            "Неверный формат даты. Попробуйте снова.",
            reply_markup=get_date_keyboard()
        )
        return CHOOSE_DATE

async def process_delete_plan(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_id = update.effective_user.id
    selected_date = context.user_data.get('selected_date')

    if update.message.text.lower() == 'все':
        # Удаляем все планы на выбранную дату
        plans[user_id] = [plan for plan in plans.get(user_id, []) if plan['date'] != selected_date]
        await update.message.reply_text(f"Все планы на {selected_date.strftime('%d.%m.%Y')} удалены.", reply_markup=get_main_keyboard())
    else:
        try:
            plan_index = int(update.message.text)  # Используем введенное значение напрямую
            user_plans = plans.get(user_id, [])
            selected_plans = [plan for plan in user_plans if plan['date'] == selected_date]

            if 1 <= plan_index <= len(selected_plans):  # Проверяем, что индекс в пределах
                # Удаляем выбранный план
                plan_to_delete = selected_plans[plan_index - 1]
                user_plans.remove(plan_to_delete)  # Удаляем план из user_plans
                await update.message.reply_text(f"План '{plan_to_delete['title']}' удален.", reply_markup=get_main_keyboard())
            else:
                await update.message.reply_text("Неверный номер плана. Попробуйте снова.", reply_markup=get_main_keyboard())
        except (ValueError, IndexError):
            await update.message.reply_text("Неверный ввод. Введите номер плана или 'все'.", reply_markup=get_main_keyboard())

    save_plans_to_json()  # Сохраняем планы после удаления
    return ConversationHandler.END


def get_date_keyboard():
    today = datetime.now(LOCAL_TZ).date()
    keyboard = [
        [InlineKeyboardButton(f"{today.strftime('%d.%m.%Y')}", callback_data=today.strftime("%d.%m.%Y"))],
        [InlineKeyboardButton(f"{(today + timedelta(days=1)).strftime('%d.%m.%Y')}", 
                               callback_data=(today + timedelta(days=1)).strftime("%d.%m.%Y"))],
        [InlineKeyboardButton(f"{(today + timedelta(days=2)).strftime('%d.%m.%Y')}", 
                               callback_data=(today + timedelta(days=2)).strftime("%d.%m.%Y"))],
        [InlineKeyboardButton("Выбрать другую дату", callback_data="custom_date")]
    ]
    return InlineKeyboardMarkup(keyboard)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        '💃Привет! Я помогаю планировать задачи. Выбери действие:',
        reply_markup=get_main_keyboard()
    )

async def add_plan_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text(
        'Выберите дату для плана:',
        reply_markup=get_date_keyboard()
    )
    return CHOOSE_DATE

async def choose_date(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()

    if query.data == "custom_date":
        await query.message.reply_text("Введите дату в формате ДД.ММ.ГГГГ")
        return CHOOSE_DATE  # Добавьте это, чтобы бот знал, что ожидает ввода

    try:
        selected_date = datetime.strptime(query.data, "%d.%m.%Y").date()
        
        # Проверяем, что выбранная дата не в прошлом
        if selected_date < datetime.now(LOCAL_TZ).date():
            await query.message.reply_text(
                "Нельзя выбрать прошедшую дату. Выберите актуальную дату.",
                reply_markup=get_date_keyboard()
            )
            return CHOOSE_DATE

        context.user_data['selected_date'] = selected_date
        await query.message.reply_text(
            f"Выбрана дата: {selected_date.strftime('%d.%m.%Y')}\n"
            "Введите название плана:"
        )
        return ENTER_PLAN
    except ValueError:
        await query.message.reply_text(
            "Неверный формат даты. Попробуйте снова.",
            reply_markup=get_date_keyboard()
        )
        return CHOOSE_DATE
    
async def process_custom_date(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_id = update.effective_user.id
    try:
        selected_date = datetime.strptime(update.message.text, "%d.%m.%Y").date()
        # Проверка на прошедшую дату
        if selected_date < datetime.now(LOCAL_TZ).date():
            await update.message.reply_text(
                "Нельзя выбрать прошедшую дату. Выберите актуальную дату.",
                reply_markup=get_date_keyboard()
            )
            return CHOOSE_DATE

        context.user_data['selected_date'] = selected_date
        await update.message.reply_text(
            f"Выбрана дата: {selected_date.strftime('%d.%m.%Y')}\n"
            "Введите название плана:"
        )
        return ENTER_PLAN
    except ValueError:
        await update.message.reply_text(
            "Неверный формат даты. Попробуйте снова.",
            reply_markup=get_date_keyboard()
        )
        return CHOOSE_DATE
    
async def enter_plan(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    plan_title = update.message.text
    context.user_data['plan_title'] = plan_title

    keyboard = [
        [InlineKeyboardButton("🕒 Добавить время", callback_data="add_time")],
        [InlineKeyboardButton("❌ Без времени", callback_data="no_time")]
    ]
    await update.message.reply_text(
        "Хотите добавить время к плану?",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    return ENTER_TIME

async def enter_time(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()

    if query.data == "no_time":
        # Сохраняем план без времени
        user_id = update.effective_user.id
        selected_date = context.user_data['selected_date']
        plan_title = context.user_data['plan_title']

        if user_id not in plans:
            plans[user_id] = []

        plans[user_id].append({
            'date': selected_date,
            'title': plan_title,
            'time': None
        })

        await query.message.reply_text(
            f"Задача добавлена:\n"
            f"Дата: {selected_date.strftime('%d.%m.%Y')}\n"
            f"Задача: {plan_title}",
            reply_markup=get_main_keyboard()
        )
        save_plans_to_json()
        return ConversationHandler.END

    elif query.data == "add_time":
        await query.message.reply_text("Введите время в формате ЧЧ:ММ")
        return ENTER_TIME

async def process_time(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    try:
        time_str = update.message.text
        time_obj = datetime.strptime(time_str, "%H:%M").time()
        
        user_id = update.effective_user.id
        selected_date = context.user_data['selected_date']
        plan_title = context.user_data['plan_title']

        # Создаем "offset-aware" datetime
        selected_datetime = LOCAL_TZ.localize(datetime.combine(selected_date, time_obj))

        # Проверяем, что время не в прошлом
        if selected_datetime < datetime.now(LOCAL_TZ):
            await update.message.reply_text(
                "Нельзя выбрать прошедшее время. Введите актуальное время.",
                reply_markup=get_main_keyboard()
            )
            return ConversationHandler.END

        if user_id not in plans:
            plans[user_id] = []

        plans[user_id].append({
            'date': selected_date,
            'title': plan_title,
            'time': time_obj
        })

        await update.message.reply_text(
            f"План добавлен:\n"
            f"Дата: {selected_date.strftime('%d.%m.%Y')}\n"
            f"Время: {time_obj.strftime('%H:%M')}\n"
            f"Задача: {plan_title}",
            reply_markup=get_main_keyboard()
        )
        save_plans_to_json()
        return ConversationHandler.END
    except ValueError:
        await update.message.reply_text(
            "Неверный формат времени. Введите время в формате ЧЧ:ММ",
            reply_markup=get_main_keyboard()
        )
        return ConversationHandler.END

async def show_plans(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        'Выберите дату для просмотра планов:',
        reply_markup=get_date_keyboard()
    )
    return CHOOSE_DATE

async def show_plans_for_date(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()

    try:
        selected_date = datetime.strptime(query.data, "%d.%m.%Y").date()
        user_id = update.effective_user.id
        
        user_plans = [
            plan for plan in plans.get(user_id, []) 
            if plan['date'] == selected_date
        ]

        if user_plans:
            plans_text = f"Планы на {selected_date.strftime('%d.%m.%Y')}:\n\n"
            for plan in sorted(user_plans, key=lambda x: x['time'] or datetime.min.time()):
                time_str = plan['time'].strftime('%H:%M') if plan['time'] else 'Без времени'
                plans_text += f"• {plan['title']} ({time_str})\n"
            
            await query.message.reply_text(
                plans_text, 
                reply_markup=get_main_keyboard()
            )
        else:
            await query.message.reply_text(
                f"🏖 На {selected_date.strftime('%d.%m.%Y')} нет запланированных задач.", 
                reply_markup=get_main_keyboard()
            )
        return ConversationHandler.END
    
    except ValueError:
        if query.data == "custom_date":
            await query.message.reply_text("Введите дату в формате ДД.ММ.ГГГГ")
            return CHOOSE_DATE
        
        await query.message.reply_text(
            "Неверный формат даты. Попробуйте снова.",
            reply_markup=get_date_keyboard()
        )
        return CHOOSE_DATE

async def show_today_plans(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    today = datetime.now(LOCAL_TZ).date()
    user_id = update.effective_user.id
    
    user_plans = [
        plan for plan in plans.get(user_id, []) 
        if plan['date'] == today
    ]

    if user_plans:
        plans_text = f"🌟 Планы на сегодня ({today.strftime('%d.%m.%Y')}):\n\n"
        for plan in sorted(user_plans, key=lambda x: x['time'] or datetime.min.time()):
            time_str = plan['time'].strftime('%H:%M') if plan['time'] else 'Без времени'
            plans_text += f"• {plan['title']} ({time_str})\n"
        
        await update.message.reply_text(
            plans_text, 
            reply_markup=get_main_keyboard()
        )
    else:
        await update.message.reply_text(
            "🏖 На сегодня нет запланированных задач.", 
            reply_markup=get_main_keyboard()
        )

async def daily_plan_reminder(context: ContextTypes.DEFAULT_TYPE) -> None:
    try:
        today = datetime.now(LOCAL_TZ).date()
        
        for user_id, user_plans in plans.items():
            today_plans = [
                plan for plan in user_plans 
                if plan['date'] == today
            ]
            
            if today_plans:
                plans_text = f"🌟 Ваши планы на сегодня ({today.strftime('%d.%m.%Y')}):\n\n"
                for plan in sorted(today_plans, key=lambda x: x['time'] or datetime.min.time()):
                    time_str = plan['time'].strftime('%H:%M') if plan['time'] else 'Без времени'
                    plans_text += f"• {plan['title']} ({time_str})\n"
                
                try:
                    logging.info(f"Отправка сообщения пользователю {user_id}: {plans_text}")  # Log the message being sent
                    await context.bot.send_message(
                        chat_id=user_id, 
                        text=plans_text
                    )
                except Exception as e:
                    logging.error(f"Не удалось отправить напоминание пользователю {user_id}: {e}")
    except Exception as e:
        logging.error(f"Ошибка в daily_plan_reminder: {e}")

async def plan_reminders(context: ContextTypes.DEFAULT_TYPE) -> None:
    try:
        now = datetime.now(LOCAL_TZ)
        
        for user_id, user_plans in plans.items():
            for plan in user_plans:
                if plan['time'] and plan['date'] == now.date():
                    plan_time = LOCAL_TZ.localize(datetime.combine(plan['date'], plan['time']))  # Сделаем plan_time "offset-aware"
                    
                    # Проверяем, что время плана наступило в течение ближайших 50 секунд
                    if (plan_time - now).total_seconds() <= 50 and (plan_time - now).total_seconds() > 0:
                        try:
                            await context.bot.send_message(
                                chat_id=user_id, 
                                text=f"🔔 Напоминание!\nПлан: {plan['title']}\nВремя: {plan['time'].strftime('%H:%M')}"
                            )
                        except Exception as e:
                            logging.error(f"Не удалось отправить напоминание пользователю {user_id}: {e}")
    except Exception as e:
        logging.error(f"Ошибка в plan_reminders: {e}")

# Function to add a reminder
async def add_reminder(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    if len(context.args) < 2:
        await update.message.reply_text("Используйте: /add <время в формате ЧЧ:ММ> <текст напоминания>")
        return

    reminder_time = context.args[0]  # Ожидаем время в формате HH:MM
    reminder_text = ' '.join(context.args[1:])  # Остальное - текст напоминания

    try:
        # Парсим время и создаем объект datetime
        reminder_datetime = datetime.strptime(reminder_time, "%H:%M").replace(tzinfo=pytz.timezone('Europe/Moscow'))

        # Проверяем, что время не в прошлом
        if reminder_datetime < datetime.now(pytz.timezone('Europe/Moscow')):
            await update.message.reply_text("Нельзя установить напоминание на прошедшее время.")
            return

        # Запланируем напоминание
        scheduler.add_job(send_reminder, 'date', run_date=reminder_datetime, args=[context, user_id, reminder_text])
        await update.message.reply_text(f"Напоминание установлено на {reminder_time}.")
    except ValueError:
        await update.message.reply_text("Неверный формат времени. Используйте ЧЧ:ММ.")


# Function to send the reminder
async def send_reminder(context: ContextTypes.DEFAULT_TYPE, user_id, reminder_text):
    await context.bot.send_message(chat_id=user_id, text=f"🔔 Напоминание: {reminder_text}")   

def main():
    """Функция для создания и запуска бота"""
    load_plans_from_json()
    application = ApplicationBuilder().token(TOKEN).build()
    delete_plan_handler = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex('^❌ Удалить план$'), delete_plan_start)],
        states={
            CHOOSE_DATE: [CallbackQueryHandler(delete_plan_for_date)],
            ENTER_PLAN: [MessageHandler(filters.TEXT & ~filters.COMMAND, process_delete_plan)]
        },
        fallbacks=[CommandHandler('cancel', start)]
    )
    # Создаем ConversationHandler для добавления плана
    add_plan_handler = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex('^✏️ Добавить план$'), add_plan_start)],
        states={
            CHOOSE_DATE: [CallbackQueryHandler(choose_date)],
            ENTER_PLAN: [MessageHandler(filters.TEXT & ~filters.COMMAND, enter_plan)],
            ENTER_TIME: [
                CallbackQueryHandler(enter_time),
                MessageHandler(filters.TEXT & ~filters.COMMAND, process_time)
            ]
        },
        fallbacks=[CommandHandler('cancel', start)]
    )

    # Создаем ConversationHandler для просмотра планов
    show_plans_handler = ConversationHandler(
        entry_points=[
            MessageHandler(filters.Regex('^👀 Показать планы$'), show_plans),
            MessageHandler(filters.Regex('^Выбрать дату$'), show_plans)
        ],
        states={
            CHOOSE_DATE: [CallbackQueryHandler(show_plans_for_date)]
        },
        fallbacks=[CommandHandler('cancel', start)]
    )

    # Добавление обработчиков
    application.add_handler(CommandHandler("start", start))
    application.add_handler(add_plan_handler)
    application.add_handler(show_plans_handler)
    application.add_handler(delete_plan_handler)  # Добавляем обработчик для удаления планов
    application.add_handler(MessageHandler(filters.Regex('^📅 Планы на сегодня$'), show_today_plans))


    # Проверяем наличие job_queue перед добавлением джобов
    
    # В функции main() измените время на 3:00

    if hasattr(application, 'job_queue') and application.job_queue is not None:
    # Добавляем job для ежедневных напоминаний
        application.job_queue.run_daily(
            daily_plan_reminder, 
            time=datetime.now(LOCAL_TZ).replace(hour=3, minute=10, second=0, microsecond=0).time()
        )
    save_plans_to_json()
    # Добавляем job для напоминаний о конкретных планах
    application.job_queue.run_repeating(plan_reminders, interval=60)
    # Запуск бота
    application.run_polling(drop_pending_updates=True)

def run_bot():
    """Функция запуска бота с корректной обработкой исключений"""
    try:
        asyncio.run(start_bot())
    except KeyboardInterrupt:
        logging.info("Bot stopped by user")
    except Exception as e:
        logging.error(f"Async bot error: {e}", exc_info=True)
    finally:
        save_plans_to_json()  # Сохраняем планы при завершении работы

async def start_bot():
    """Асинхронный запуск бота"""
    try:
        load_plans_from_json()
        application = ApplicationBuilder().token(TOKEN).build()
         # Создаем ConversationHandler для удаления плана
        delete_plan_handler = ConversationHandler(
            entry_points=[MessageHandler(filters.Regex('^❌ Удалить план$'), delete_plan_start)],
            states={
                CHOOSE_DATE: [
                    CallbackQueryHandler(delete_plan_for_date),
                    MessageHandler(filters.TEXT & ~filters.COMMAND, process_custom_date)  # Добавьте этот обработчик
                ],
                ENTER_PLAN: [MessageHandler(filters.TEXT & ~filters.COMMAND, process_delete_plan)]
            },
            fallbacks=[CommandHandler('cancel', start)]
        )
        # Настройка обработчиков (те же, что и в main())
        add_plan_handler = ConversationHandler(
            entry_points=[MessageHandler(filters.Regex('^✏️ Добавить план$'), add_plan_start)],
            states={
                CHOOSE_DATE: [
                    CallbackQueryHandler(choose_date),
                    MessageHandler(filters.TEXT & ~filters.COMMAND, process_custom_date)  # Добавьте этот обработчик
                ],
                ENTER_PLAN: [MessageHandler(filters.TEXT & ~filters.COMMAND, enter_plan)],
                ENTER_TIME: [
                    CallbackQueryHandler(enter_time),
                    MessageHandler(filters.TEXT & ~filters.COMMAND, process_time)
                ]
            },
            fallbacks=[CommandHandler('cancel', start)]
        )

        show_plans_handler = ConversationHandler(
            entry_points=[
                MessageHandler(filters.Regex('^👀 Показать планы$'), show_plans),
                MessageHandler(filters.Regex('^Выбрать дату$'), show_plans)
            ],
            states={
                CHOOSE_DATE: [CallbackQueryHandler(show_plans_for_date)]
            },
            fallbacks=[CommandHandler('cancel', start)]
        )

        application.add_handler(CommandHandler("start", start))
        application.add_handler(add_plan_handler)
        application.add_handler(show_plans_handler)
        application.add_handler(delete_plan_handler)  # Добавляем обработчик для удаления планов
        application.add_handler(MessageHandler(filters.Regex('^📅 Планы на сегодня$'), show_today_plans))


        # Проверяем наличие job_queue перед добавлением джобов
        if hasattr(application, 'job_queue') and application.job_queue is not None:
            # Добавляем job для ежедневных напоминаний
            application.job_queue.run_daily(
                daily_plan_reminder, 
                time=datetime.now(LOCAL_TZ).replace(hour=3, minute=10, second=0, microsecond=0).time()
            )

            # Добавляем job для напоминаний о конкретных планах
            application.job_queue.run_repeating(plan_reminders, interval=60)
        else:
            logging.warning("Job queue is not available. Scheduled jobs will not run.")
        save_plans_to_json()
        # Запуск бота
        await application.initialize()
        await application.start()
        await application.updater.start_polling(drop_pending_updates=True)
        
        # Работаем, пока не будет остановлен
        await asyncio.get_event_loop().create_future()
    
    except Exception as e:
        logging.error(f"Error in start_bot: {e}", exc_info=True)

def run_async_bot():
    """Альтернативный метод запуска для более надежной обработки"""
    try:
        asyncio.run(start_bot())
    except KeyboardInterrupt:
        logging.info("Bot stopped by user")
    except Exception as e:
        logging.error(f"Async bot error: {e}", exc_info=True)
    finally:
        save_plans_to_json()  # Сохраняем планы при завершении работы

if __name__ == '__main__':
    try:
        run_async_bot()
    except KeyboardInterrupt:
        print("Bot stopped")
    finally:
        save_plans_to_json()  # Сохраняем планы при завершении работы