import os
import tempfile
import logging
from pathlib import Path

from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, FSInputFile
from aiogram.enums import ChatAction
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()
logging.basicConfig(level=logging.INFO)

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
CHAT_MODEL = os.getenv("OPENAI_CHAT_MODEL", "gpt-4o-mini")
TRANSCRIBE_MODEL = os.getenv("OPENAI_TRANSCRIBE_MODEL", "gpt-4o-mini-transcribe")
TTS_MODEL = os.getenv("OPENAI_TTS_MODEL", "gpt-4o-mini-tts")
TTS_VOICE = os.getenv("OPENAI_TTS_VOICE", "alloy")

if not TELEGRAM_BOT_TOKEN or not OPENAI_API_KEY:
    raise RuntimeError("Set TELEGRAM_BOT_TOKEN and OPENAI_API_KEY in your .env file.")

bot = Bot(token=TELEGRAM_BOT_TOKEN)
dp = Dispatcher()
ai = OpenAI(api_key=OPENAI_API_KEY)

SYSTEM_PROMPT = """
You are Speaking Zone, a friendly English-speaking practice coach inside Telegram.
Speak naturally in clear English suitable for a B1-B2 learner unless the user asks otherwise.
Keep most replies concise and conversational. Ask one follow-up question to keep the conversation going.
If the user makes English mistakes, first respond naturally to their meaning, then add a short
'Quick correction' section with a corrected version and one brief explanation. Do not overcorrect
every tiny informal expression. If asked, run IELTS Speaking practice and give cautious estimated
feedback on fluency, vocabulary, grammar, and coherence. Do not claim an official IELTS score.
For pronunciation, explain that audio-based feedback is approximate and depends on the quality
of the recording. Be supportive and never shame the learner.
"""

# Lightweight in-memory chat history. It resets when the bot restarts.
histories = {}
MAX_TURNS = 12

def get_history(user_id: int):
    if user_id not in histories:
        histories[user_id] = [{"role": "system", "content": SYSTEM_PROMPT}]
    return histories[user_id]

async def get_ai_reply(user_id: int, user_text: str) -> str:
    history = get_history(user_id)
    history.append({"role": "user", "content": user_text})
    # Keep system prompt plus recent turns only.
    if len(history) > MAX_TURNS + 1:
        histories[user_id] = [history[0]] + history[-MAX_TURNS:]
        history = histories[user_id]
    response = ai.chat.completions.create(
        model=CHAT_MODEL,
        messages=history,
        temperature=0.7,
    )
    answer = response.choices[0].message.content or "Sorry, I couldn't form a reply. Try again."
    history.append({"role": "assistant", "content": answer})
    return answer

async def send_long_text(message: Message, text: str):
    # Telegram messages have a practical 4096-character limit.
    for start in range(0, len(text), 3900):
        await message.answer(text[start:start + 3900])

@dp.message(CommandStart())
async def start(message: Message):
    await message.answer(
        "👋 Welcome to Speaking Zone AI!\n\n"
        "Practise English with me by text or voice.\n\n"
        "• Send a text message to chat.\n"
        "• Send a voice note and I’ll transcribe it, reply, and send a voice response.\n"
        "• Use /practice for an IELTS-style speaking question.\n"
        "• Use /reset to clear this chat’s short-term conversation history.\n\n"
        "Let’s start: What did you do today?"
    )

@dp.message(Command("help"))
async def help_command(message: Message):
    await message.answer(
        "Commands:\n/start — start the bot\n/practice — get a speaking question\n/reset — reset conversation history\n\n"
        "You can send text or a Telegram voice note."
    )

@dp.message(Command("reset"))
async def reset(message: Message):
    histories[message.from_user.id] = [{"role": "system", "content": SYSTEM_PROMPT}]
    await message.answer("Conversation history cleared. Let’s start fresh! What topic would you like to discuss?")

@dp.message(Command("practice"))
async def practice(message: Message):
    prompt = (
        "Give me one IELTS Speaking practice question appropriate for B1-B2 level. "
        "Do not answer it. Ask me to answer in 30-60 seconds, then tell me to send my answer as text or voice."
    )
    try:
        answer = await get_ai_reply(message.from_user.id, prompt)
        await send_long_text(message, answer)
    except Exception:
        logging.exception("Practice request failed")
        await message.answer("Sorry, the AI service is temporarily unavailable. Please try again shortly.")

@dp.message(F.voice)
async def voice_message(message: Message):
    await bot.send_chat_action(message.chat.id, ChatAction.TYPING)
    voice = message.voice
    file_info = await bot.get_file(voice.file_id)

    with tempfile.TemporaryDirectory() as tmp:
        input_path = Path(tmp) / "voice.ogg"
        await bot.download_file(file_info.file_path, destination=input_path)

        try:
            with open(input_path, "rb") as audio_file:
                transcript = ai.audio.transcriptions.create(
                    model=TRANSCRIBE_MODEL,
                    file=audio_file,
                )
            spoken_text = getattr(transcript, "text", "").strip()
            if not spoken_text:
                await message.answer("I couldn't understand that recording. Please try again in a quieter place.")
                return

            await message.answer(f"📝 I heard:\n{spoken_text}")
            reply = await get_ai_reply(message.from_user.id, spoken_text)
            await send_long_text(message, reply)

            # TTS audio response. Save to a temporary MP3 and send it back.
            speech_path = Path(tmp) / "reply.mp3"
            speech = ai.audio.speech.create(
                model=TTS_MODEL,
                voice=TTS_VOICE,
                input=reply[:3500],
                instructions="Speak clearly and naturally, like a friendly English tutor.",
                response_format="mp3",
            )
            speech.stream_to_file(speech_path)
            await message.answer_audio(
                audio=FSInputFile(speech_path),
                title="Speaking Zone AI reply",
                performer="Speaking Zone AI",
            )
        except Exception:
            logging.exception("Voice handling failed")
            await message.answer(
                "Sorry, I couldn't process that voice message. Check the API key/billing and try again."
            )

@dp.message(F.text)
async def text_message(message: Message):
    if message.text.startswith("/"):
        return
    await bot.send_chat_action(message.chat.id, ChatAction.TYPING)
    try:
        reply = await get_ai_reply(message.from_user.id, message.text)
        await send_long_text(message, reply)
    except Exception:
        logging.exception("Text handling failed")
        await message.answer("Sorry, the AI service is temporarily unavailable. Check your API setup and try again.")

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
