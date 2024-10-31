import logging
import requests
import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.types import Message
from aiogram.filters import Command
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram import F, Router

# Ваш API ключ от GISMETEO и Telegram API токен
API_TOKEN = '######'
GISMETEO_API_KEY = '######'  # Пример API-ключа, замените на свой

# Логирование для отладки
logging.basicConfig(level=logging.INFO)

# Инициализация бота и диспетчера
bot = Bot(token=API_TOKEN)
dp = Dispatcher(storage=MemoryStorage())
router = Router()


# Команда /start
@router.message(Command("start"))
async def send_welcome(message: Message):
    await message.reply("Привет! Я бот, который может показывать прогноз погоды по GISMETEO.\n"
                        "Введи название города, чтобы узнать погоду.")


# Команда /help
@router.message(Command("help"))
async def send_help(message: Message):
    await message.reply("/start - Запуск бота\n"
                        "/help - Помощь\n"
                        "Просто введи название города, и я покажу тебе прогноз погоды.")


# Получение прогноза погоды через API GISMETEO
def get_weather_gismeteo(city: str):
    # Пример запроса для поиска города
    city_search_url = f"https://api.gismeteo.net/v2/search/cities/?query={city}"
    headers = {
        "X-Gismeteo-Token": GISMETEO_API_KEY  # API-ключ в заголовке
    }

    # Поиск города
    search_response = requests.get(city_search_url, headers=headers)

    if search_response.status_code == 200:
        search_data = search_response.json()

        # Проверяем, есть ли результаты поиска и правильная ли структура данных
        if 'response' in search_data and 'items' in search_data['response'] and search_data['response']['items']:
            city_id = search_data['response']['items'][0]['id']  # Используем первый результат из списка
        else:
            return "Город не найден. Проверьте правильность названия."
    else:
        return "Ошибка при поиске города."

    # Используем найденный ID города для запроса погоды
    weather_url = f"https://api.gismeteo.net/v2/weather/current/{city_id}/"
    response = requests.get(weather_url, headers=headers)

    if response.status_code == 200:
        data = response.json()
        if 'temperature' in data and 'air' in data['temperature']:
            temp = data['temperature']['air']['C']
            wind_speed = data['wind']['speed']['m_s']
            humidity = data['humidity']['percent']
            description = data['description']['full']

            weather_info = (f"Погода в городе {city}:\n"
                            f"Описание: {description.capitalize()}\n"
                            f"Температура: {temp}°C\n"
                            f"Влажность: {humidity}%\n"
                            f"Скорость ветра: {wind_speed} м/с")
            return weather_info
        else:
            return "Не удалось получить данные о погоде."
    else:
        return "Не удалось получить данные о погоде. Попробуйте позже."


# Обработка текстовых сообщений (ввод названия города)
@router.message(F.text)
async def send_weather(message: Message):
    city = message.text
    weather_info = get_weather_gismeteo(city)
    await message.reply(weather_info, parse_mode="Markdown")


# Асинхронная функция для запуска бота
async def main():
    dp.include_router(router)
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


# Запуск бота
if __name__ == '__main__':
    asyncio.run(main())
