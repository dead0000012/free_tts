import pygame as pg
import asyncio
import edge_tts
import threading
import tempfile
import os
import requests
import pyttsx3
import time
import pyperclip

# --- Голоса
voices_list = [
    ("ru-RU-SvetlanaNeural", "ru Светлана"),
    ("en-US-EmmaMultilingualNeural", "us Emma"),
    ("en-US-BrianMultilingualNeural", "us Brian"),
    ("ru-RU-DmitryNeural", "ru Дмитрий"),
    ("ru-RU-DariyaNeural", "ru Дирия"),
    ("uz-UZ-SardorNeural", "uz Сардор"),
    ("uz-UZ-MadinaNeural", "uz Мадина")
]
voice_index = 0

# --- Настройки
speech_speed = 0
speech_volume = 0
use_offline = False

# --- Pygame
pg.init()
WIDTH, HEIGHT = 800, 600
screen = pg.display.set_mode((WIDTH, HEIGHT))
pg.display.set_caption("Чат с озвучкой")
font = pg.font.SysFont(None, 24)
clock = pg.time.Clock()

WHITE, BLACK, GRAY, BLUE, RED, GREEN = (255,)*3, (0,)*3, (230,)*3, (0,0,255), (255,0,0), (0,255,0)

chat = []
input_text = ''
key_state = {pg.K_UP: False, pg.K_DOWN: False, pg.K_LEFT: False, pg.K_RIGHT: False}
internet_status = True

# --- pyttsx3 init
engine = pyttsx3.init()
engine.setProperty('rate', 200)
engine.setProperty('volume', 1.0)

def format_edge_param(value: int) -> str:
    return f"{'+' if value >= 0 else ''}{value}%"

def wrap_text(text, font, max_width):
    words = text.split()
    lines = []
    current_line = ""

    for word in words:
        test_line = f"{current_line} {word}".strip()
        if font.size(test_line)[0] <= max_width:
            current_line = test_line
        else:
            lines.append(current_line)
            current_line = word

    if current_line:
        lines.append(current_line)
    return lines


def check_internet():
    global internet_status
    while True:
        try:
            requests.get("https://www.google.com", timeout=5)
            internet_status = True
        except:
            internet_status = False
        time.sleep(5)

threading.Thread(target=check_internet, daemon=True).start()

def detect_lang(text):
    if not text: return 'ru'
    first = text.strip()[0].lower()
    if 'а' <= first <= 'я' or first == 'ё': return 'ru'
    elif 'a' <= first <= 'z': return 'en'
    return 'ru'

def speak_offline(text):
    try:
        rate = 200 + speech_speed
        volume = max(0.0, min(1.0, 1.0 + speech_volume / 100))
        engine.setProperty('rate', rate)
        engine.setProperty('volume', volume)
        engine.say(text)
        engine.runAndWait()
    except Exception as e:
        print("❌ Ошибка офлайн озвучки:", e)

def speak_async(text):
    def _speak():
        if use_offline or not internet_status:
            speak_offline(text)
        else:
            try:
                voice = voices_list[voice_index][0]
                asyncio.run(edge_speak(text, voice))
            except Exception as e:
                print("❌ Ошибка онлайн озвучки:", e)
    threading.Thread(target=_speak, daemon=True).start()

async def edge_speak(text, voice):
    rate = format_edge_param(speech_speed)
    volume = format_edge_param(speech_volume)
    communicate = edge_tts.Communicate(text=text, voice=voice, rate=rate, volume=volume)
    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as f:
        temp_file = f.name
    await communicate.save(temp_file)
    pg.mixer.init()
    pg.mixer.music.load(temp_file)
    pg.mixer.music.play()
    while pg.mixer.music.get_busy():
        await asyncio.sleep(0.0001)
    os.remove(temp_file)

# --- Главный цикл
running = True
while running:
    for e in pg.event.get():
        if e.type == pg.QUIT or (e.type == pg.KEYDOWN and e.key == pg.K_ESCAPE):
            running = False
        elif e.type == pg.KEYDOWN:
            if e.key == pg.K_BACKSPACE:
                input_text = input_text[:-1]
            elif e.key == pg.K_RETURN:
                if input_text.strip():
                    chat.append(('Ты', input_text))
                    speak_async(input_text)
                    input_text = ''
            elif e.key == pg.K_F1:
                input_text = pyperclip.paste()
            elif e.key == pg.K_F2:
                voice_index = (voice_index + 1) % len(voices_list)
            elif e.key == pg.K_F3:
                use_offline = not use_offline
            else:
                input_text += e.unicode

    keys = pg.key.get_pressed()

    if keys[pg.K_UP] and not key_state[pg.K_UP]:
        speech_speed = min(speech_speed + 10, 200)
        key_state[pg.K_UP] = True
    elif not keys[pg.K_UP]: key_state[pg.K_UP] = False

    if keys[pg.K_DOWN] and not key_state[pg.K_DOWN]:
        speech_speed = max(speech_speed - 10, -100)
        key_state[pg.K_DOWN] = True
    elif not keys[pg.K_DOWN]: key_state[pg.K_DOWN] = False

    if keys[pg.K_RIGHT] and not key_state[pg.K_RIGHT]:
        speech_volume = min(speech_volume + 10, 100)
        key_state[pg.K_RIGHT] = True
    elif not keys[pg.K_RIGHT]: key_state[pg.K_RIGHT] = False

    if keys[pg.K_LEFT] and not key_state[pg.K_LEFT]:
        speech_volume = max(speech_volume - 10, -100)
        key_state[pg.K_LEFT] = True
    elif not keys[pg.K_LEFT]: key_state[pg.K_LEFT] = False

    # --- UI
    screen.fill(WHITE)
    pg.draw.rect(screen, GRAY, (20, 20, WIDTH - 40, HEIGHT - 190))
    pg.draw.rect(screen, GRAY, (20, HEIGHT - 100, WIDTH - 40, 80))

    y = 30
    for speaker, message in chat[-16:]:
        col = BLUE if speaker != 'Ты' else BLACK
        lines = wrap_text(f"{speaker}: {message}", font, WIDTH - 60)
        for line in lines:
            surf = font.render(line, True, col)
            screen.blit(surf, (30, y))
            y += 24 
        y += 5  



    screen.blit(font.render(f"Громкость: {speech_volume}", True, BLACK), (20, HEIGHT - 160))
    screen.blit(font.render(f"Скорость: {speech_speed}", True, BLACK), (20, HEIGHT - 130))
    screen.blit(font.render(f"Голос: {voices_list[voice_index][1]}", True, BLACK), (300, HEIGHT - 160))
    screen.blit(font.render(f"Режим: {'Офлайн' if use_offline or not internet_status else 'Онлайн'}", True, RED if use_offline else GREEN), (300, HEIGHT - 130))

    screen.blit(font.render(input_text, True, BLACK), (30, HEIGHT - 90))

    pg.draw.circle(screen, GREEN if internet_status else RED, (20, 10), 6)

    pg.display.flip()
    clock.tick(60)

pg.quit()
