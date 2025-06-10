import logging
from aiogram import Bot, Dispatcher, types, F
from aiogram.enums import ParseMode
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils.keyboard import ReplyKeyboardBuilder
from aiogram import Router
from aiogram.client.default import DefaultBotProperties
from aiogram.fsm.state import StatesGroup, State

# Настройка логирования
logging.basicConfig(level=logging.INFO)

# Инициализация объектов
bot = Bot(
    token="7729020193:AAHNd76RUEAxts8l3beOFi-Vf6qNyT2Bj4w",
    default=DefaultBotProperties(parse_mode=ParseMode.HTML)  # Установка параметров по умолчанию
)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)
router = Router()
dp.include_router(router)

# Словарь с ценами
PRICES = {
    "Полотно ПВХ": 400,
    "Полотно тканевое Descor": 2500,
    "Багет ПВХ": 100,
    "Багет flexy под подсветку": 2000,
    "Заглушка": 100,
    "Более 4 углов": 100,
    "Cтойки под пожарную сигнализацию": 400,
    # Добавьте остальные товары по аналогии
}

class OrderState(StatesGroup):
    select_product = State()
    enter_quantity = State()
    enter_contacts = State()

# Главное меню
def main_kb() -> ReplyKeyboardMarkup:
    builder = ReplyKeyboardBuilder()

    # Добавляем кнопки
    builder.add(
        KeyboardButton(text="Полотно ПВХ"),
        KeyboardButton(text="Полотно тканевое Descor"),
        KeyboardButton(text="Багет ПВХ"),
        KeyboardButton(text="Багет flexy под подсветку"),
        KeyboardButton(text="Заглушка"),
        KeyboardButton(text="Другие товары"),
        KeyboardButton(text="Оформить заказ")
    )

    # Распределение кнопок по рядам:
    # 2 кнопки в первом ряду, 2 во втором, 2 в третьем, 1 в четвертом
    builder.adjust(2, 2, 2, 1)

    return builder.as_markup(
        resize_keyboard=True,
        input_field_placeholder="Выберите действие"
    )

# Обработчик команды /start
@router.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer(
        "Добро пожаловать! Выберите товар:",
        reply_markup=main_kb()
    )

# Обработчик кнопки "Другие товары"
@router.message(F.text == "Другие товары")
async def other_products(message: types.Message):
    builder = ReplyKeyboardBuilder()
    builder.add(KeyboardButton(text="Более 4 углов"))
    builder.add(KeyboardButton(text="Cтойки под пожарную сигнализацию"))
    builder.adjust(2)
    builder.row(KeyboardButton(text="Назад"))
    await message.answer(
        "Дополнительные товары:",
        reply_markup=builder.as_markup(resize_keyboard=True)
    )

# Обработчик кнопки "Назад"
@router.message(F.text == "Назад")
async def back_handler(message: types.Message):
    await cmd_start(message)

# Обработчик оформления заказа
@router.message(F.text == "Оформить заказ")
async def order_handler(message: types.Message, state: FSMContext):
    await state.set_state(OrderState.enter_contacts)
    await message.answer("Введите ваше имя и контактный телефон:")

# Обработчик контактных данных
@router.message(OrderState.enter_contacts)
async def process_contacts(message: types.Message, state: FSMContext):
    with open("orders.txt", "a", encoding="utf-8") as file:
        file.write(f"Клиент: {message.text}\n")
    await state.clear()
    await message.answer("Спасибо! Мы с вами свяжемся.", reply_markup=main_kb())

# Обработчик выбора товара
@router.message(F.text.in_(PRICES.keys()))
async def product_selected(message: types.Message, state: FSMContext):
    await state.update_data(selected_product=message.text)
    await state.set_state(OrderState.enter_quantity)
    await message.answer(f"Введите количество/размер для {message.text}:")

# Обработчик ввода количества
@router.message(OrderState.enter_quantity)
async def process_quantity(message: types.Message, state: FSMContext):
    try:
        quantity = float(message.text)
        data = await state.get_data()
        product = data.get('selected_product')
        cost = PRICES[product] * quantity
        await message.answer(f"Стоимость {product}: {cost} руб.")
    except ValueError:
        await message.answer("Пожалуйста, введите число!")
    finally:
        await state.clear()
        await cmd_start(message)

if __name__ == '__main__':
    dp.run_polling(bot, skip_updates=True)