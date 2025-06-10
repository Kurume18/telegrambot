import logging
from aiogram import Bot, Dispatcher, types, F
from aiogram.enums import ParseMode
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils.keyboard import ReplyKeyboardBuilder
from aiogram import Router

# Настройка логирования
logging.basicConfig(level=logging.INFO)

# Инициализация объектов
API_TOKEN = 'ВАШ_ТОКЕН_БОТА'
bot = Bot(token=API_TOKEN, parse_mode=ParseMode.HTML)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)
router = Router()
dp.include_router(router)

# Словарь с ценами
PRICES = {
    "Полотно пленка": 400,
    "Полотно тканевое Descor": 2500,
    "Багет ПВХ": 100,
    "Багет flexy под подсветку": 2000,
    "Заглушка": 100,
    # Добавьте остальные товары по аналогии
}

class OrderState(StatesGroup):
    select_product = State()
    enter_quantity = State()
    enter_contacts = State()

# Главное меню
def main_kb() -> ReplyKeyboardMarkup:
    builder = ReplyKeyboardBuilder()
    builder.row(
        KeyboardButton(text="Полотно пленка"),
        KeyboardButton(text="Полотно тканевое Descor")
    )
    builder.row(
        KeyboardButton(text="Багет ПВХ"),
        KeyboardButton(text="Багет flexy под подсветку")
    )
    builder.row(
        KeyboardButton(text="Заглушка"),
        KeyboardButton(text="Другие товары")
    )
    builder.row(KeyboardButton(text="Оформить заказ"))
    return builder.as_markup(resize_keyboard=True)

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
    builder.add(KeyboardButton(text="Обработка углов"))
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
    with open("orders.txt", "a") as file:
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
    dp.run_polling(bot)