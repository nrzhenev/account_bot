import re

from aiogram import types
from aiogram.dispatcher import FSMContext

from pkg import dp, data_base


@dp.message_handler(commands=["role"], state='*')
async def chr(message: types.Message, state: FSMContext):
    if message.from_user.id != 358058423:
        return
    role = re.search("\d+", message.text)
    if not role:
        return
    await state.finish()
    user_id = message.from_user.id
    role = int(role.group())
    data_base.update("users", {"user_id": user_id, "current_role_id": role})
    await message.answer(f"Changed role to {role}")
