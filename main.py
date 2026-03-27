import asyncio
import sqlite3
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command

TOKEN = "8747176381:AAHiAGbVm2qSAeV6SlW04RaJe7o8VXzWhQw"
bot = Bot(token=TOKEN)
dp = Dispatcher()

# Ініціалізація бази
conn = sqlite3.connect('inventory.db')
cursor = conn.cursor()
cursor.execute("CREATE TABLE IF NOT EXISTS inventory (diameter TEXT PRIMARY KEY, count INTEGER, weight REAL)")
conn.commit()
conn.close()

@dp.message(F.web_app_data) # Ловимо дані саме з Mini App
async def handle_webapp_data(message: types.Message):
    data_str = message.web_app_data.data # Отримуємо рядок: "ПРИЙОМ R15 КІЛЬКІСТЬ 10 ВАГА 88.0"
    print(f"Отримано дані: {data_str}")
    
    parts = data_str.split(" ")
    diam = parts[1]   # R15
    count = int(parts[3]) # 10
    weight = float(parts[5]) # 88.0

    conn = sqlite3.connect('inventory.db')
    cursor = conn.cursor()
    cursor.execute("INSERT INTO inventory (diameter, count, weight) VALUES (?, ?, ?) "
                   "ON CONFLICT(diameter) DO UPDATE SET count=count+?, weight=weight+?",
                   (diam, count, weight, count, weight))
    conn.commit()
    conn.close()
    
    await message.answer(f"✅ Додано: {diam}, {count} шт. ({weight} кг)\nЗалишки: /stock")

@dp.message(Command("stock"))
async def show_stock(message: types.Message):
    conn = sqlite3.connect('inventory.db')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM inventory")
    rows = cursor.fetchall()
    conn.close()
    
    if not rows:
        await message.answer("Склад порожній.")
        return
        
    res = "📊 СКЛАД:\n" + "\n".join([f"{r[0]}: {r[1]} шт. ({r[2]} кг)" for r in rows])
    await message.answer(res)

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())