from aiogram import F, Router, types

router = Router()


@router.message(F.document)
async def get_file_id(message: types.Message):
    """Временный хэндлер — при отправке PDF бот отвечает его file_id."""
    doc = message.document
    await message.answer(
        f"📄 <b>Файл получен!</b>\n\n"
        f"<b>Название:</b> {doc.file_name}\n"
        f"<b>Размер:</b> {doc.file_size} байт\n"
        f"<b>file_id:</b>\n<code>{doc.file_id}</code>",
        parse_mode="HTML",
    )