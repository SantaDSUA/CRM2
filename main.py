import asyncio
import json
import sqlite3
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import CommandStart, Command

TOKEN = "8747176381:AAHiAGbVm2qSAeV6SlW04RaJe7o8VXzWhQw"

bot = Bot(token=TOKEN)
dp = Dispatcher()

# Створюємо базу даних при запуску
def init_db():
    conn = sqlite3.connect('inventory.db')
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS inventory 
                      (diameter TEXT PRIMARY KEY, count INTEGER, total_weight REAL)''')
    conn.commit()
    conn.close()

@dp.message()
async def handle_text_report(message: types.Message):
    # Перевіряємо, чи це звіт про колеса
    if "Новий прийом:" in message.text:
        try:
            # Парсимо текст: "📥 Новий прийом: R15, 10 шт. (88.0 кг)"
            parts = message.text.split(": ")[1].split(", ")
            diam = parts[0] # R15
            count = int(parts[1].split(" ")[0]) # 10
            weight = float(parts[2].split("(")[1].split(" ")[0]) # 88.0

            # Записуємо в базу (SQLite)
            conn = sqlite3.connect('inventory.db')
            cursor = conn.cursor()
            cursor.execute("INSERT INTO inventory (diameter, count, total_weight) VALUES (?, ?, ?) "
                           "ON CONFLICT(diameter) DO UPDATE SET count=count+?, total_weight=total_weight+?",
                           (diam, count, weight, count, weight))
            conn.commit()
            conn.close()

            await message.reply(f"✅ Додано до складу: {diam}. Залишок оновлено.")
        except Exception as e:
            print(f"Помилка парсингу: {e}")

# Команда для перегляду залишків
@dp.message(Command("stock"))
async def show_stock(message: types.Message):
    conn = sqlite3.connect('inventory.db')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM inventory")
    rows = cursor.fetchall()
    conn.close()

    if not rows:
        await message.answer("📭 Склад порожній.")
        return

    res = "📊 **Залишки на складі:**\n\n"
    grand_total_weight = 0
    for row in rows:
        res += f"🔹 {row[0]}: {row[1]} шт. ({row[2]} кг)\n"
        grand_total_weight += row[2]
    
    res += f"\n⚖️ **Загальна вага: {round(grand_total_weight, 2)} кг**"
    await message.answer(res, parse_mode="Markdown")

@dp.message(F.web_app_data)
async def get_data(message: types.Message):
    data = json.loads(message.web_app_data.data)
    d = data['diameter']
    c = int(data['count'])
    w = float(data['totalWeight'].replace(' кг', ''))

    # Оновлюємо базу даних
    conn = sqlite3.connect('inventory.db')
    cursor = conn.cursor()
    cursor.execute("INSERT INTO inventory (diameter, count, total_weight) VALUES (?, ?, ?) "
                   "ON CONFLICT(diameter) DO UPDATE SET count=count+?, total_weight=total_weight+?",
                   (d, c, w, c, w))
    conn.commit()
    conn.close()
    
    await message.answer(f"✅ Записано: {d}, {c} шт. ({w} кг)\nПеревірити склад: /stock")

async def main():
    init_db()
    print("Бот запущений...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())