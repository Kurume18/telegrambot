import logging
from aiogram import Bot, Dispatcher, executor, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup

API_TOKEN = 'ВАШ_ТОКЕН_БОТА'

logging.basicConfig(level=logging.INFO)
bot = Bot(token=API_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)

# Словарь с ценами из файла
PRICES = {
    "Полотно пленка": 400,
    "Полотно тканевое Descor": 2500,
    "Багет ПВХ": 100,
    "Багет flexy под подсветку": 2000,
    "Заглушка": 100,
    # ... остальные товары можно добавить аналогично
}


class OrderState(StatesGroup):
    waiting_product = State()
    waiting_quantity = State()
    waiting_contact = State()


def calculate_cost(product: str, quantity: float) -> float:
    return PRICES.get(product, 0) * quantity


@dp.message_handler(commands=['start'])
async def cmd_start(message: types.Message):
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add("Полотно пленка", "Полотно тканевое Descor")
    keyboard.add("Багет ПВХ", "Багет flexy под подсветку")
    keyboard.add("Заглушка", "Другие товары")
    keyboard.add("Оформить заказ")

    await message.answer(
        "Добро пожаловать! Выберите товар:",
        reply_markup=keyboard
    )


@dp.message_handler(text="Другие товары")
async def other_products(message: types.Message):
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add("Более 4 углов", "Обработка углов")
    keyboard.add("Назад")
    await message.answer("Дополнительные товары:", reply_markup=keyboard)


@dp.message_handler(text="Назад")
async def back_to_main(message: types.Message):
    await cmd_start(message)


@dp.message_handler(text="Оформить заказ")
async def request_contact(message: types.Message):
    await OrderState.waiting_contact.set()
    await message.answer("Введите ваше имя и контактный телефон:")


@dp.message_handler(state=OrderState.waiting_contact)
async def process_contact(message: types.Message, state: FSMContext):
    with open("orders.txt", "a") as file:
        file.write(f"Клиент: {message.text}\n")
    await state.finish()
    await message.answer("Спасибо! Мы с вами свяжемся.")


@dp.message_handler()
async def process_product(message: types.Message):
    product = message.text
    if product not in PRICES:
        return

    await OrderState.waiting_quantity.set()
    await message.answer(f"Введите количество/размер для {product}:")


@dp.message_handler(state=OrderState.waiting_quantity)
async def process_quantity(message: types.Message, state: FSMContext):
    try:
        quantity = float(message.text)
        product = (await state.get_data()).get('product')
        cost = calculate_cost(product, quantity)
        await message.answer(f"Стоимость: {cost} руб.")
    except ValueError:
        await message.answer("Пожалуйста, введите число!")
    finally:
        await state.finish()


if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)