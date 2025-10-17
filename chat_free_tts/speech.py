import threading
import asyncio
from chat_utils import split_text
from edge_tts import Communicate
from config import voices_list
import pyttsx3
import tempfile
import os
import pygame as pg
engine = pyttsx3.init()

def speak_offline(text, rate=200, volume=1.0):
    try:
        engine.setProperty('rate', rate)
        engine.setProperty('volume', max(0.0, min(1.0, volume)))
        engine.say(text)
        engine.runAndWait()
    except Exception as e:
        print('Offline TTS error:', e)

def speak_async_chunked(text, voice_index=0, use_offline=False, speed=0, volume=0):
    """Озвучка с разбивкой длинного текста"""
    def _speak():
        chunks = split_text(text)
        for chunk in chunks:
            if use_offline:
                # pyttsx3 expects rate (int) and volume (0.0-1.0)
                # map speed (%) to rate: base ~200
                rate = 200 + int(speed)
                vol = 1.0 * (max(-100, min(100, volume)) / 100.0)
                speak_offline(chunk, rate=rate, volume=vol)
            else:
                try:
                    voice = voices_list[voice_index][0]  # надо импортировать voices_list из config.py
                    # edge_tts accepts rate and volume like '+0%'
                    rate = f"{ '+' if speed >= 0 else '' }{int(speed)}%"
                    vol = f"{ '+' if volume >= 0 else '' }{int(volume)}%"
                    asyncio.run(edge_speak(chunk, voice, rate=rate, volume=vol))
                except Exception as e:
                    print("Ошибка онлайн озвучки:", e)

    threading.Thread(target=_speak, daemon=True).start()

async def edge_speak(text, voice, rate="+0%", volume="+0%"):
    communicate = Communicate(text=text, voice=voice, rate=rate, volume=volume)
    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as f:
        temp_file = f.name
    await communicate.save(temp_file)
    # Инициализируем миксер только если он ещё не инициализирован
    try:
        if not pg.mixer.get_init():
            pg.mixer.init()
    except Exception:
        print("Warning: pygame.mixer unavailable; cannot play audio.")
        try:
            os.remove(temp_file)
        except Exception:
            pass
        return

    try:
        pg.mixer.music.load(temp_file)
        pg.mixer.music.play()
        while pg.mixer.music.get_busy():
            await asyncio.sleep(0.01)
    finally:
        try:
            os.remove(temp_file)
        except Exception:
            pass
    os.remove(temp_file)
