import pygame as pg
import pyttsx3
import threading
import sys

pg.init()
WIDTH, HEIGHT = 800, 600
screen = pg.display.set_mode((WIDTH, HEIGHT))
pg.display.set_caption("Чат с озвучкой на pyttsx3")
font = pg.font.SysFont(None, 24)
clock = pg.time.Clock()

WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GRAY = (230, 230, 230)
BLUE = (0, 0, 255)

chat = []
input_text = ''

# --- Инициализация синтезатора
engine = pyttsx3.init()
voices = engine.getProperty('voices')

def set_voice_by_lang(lang):
    for v in voices:
        if lang == 'ru' and 'russian' in v.name.lower():
            engine.setProperty('voice', v.id)
            return
        elif lang == 'en' and 'english' in v.name.lower():
            engine.setProperty('voice', v.id)
            return

def detect_lang(text):
    if not text:
        return 'ru'
    first_char = text.strip()[0].lower()
    if 'а' <= first_char <= 'я' or first_char == 'ё':
        return 'ru'
    elif 'a' <= first_char <= 'z':
        return 'en'
    return 'ru'

def speak_async(text):
    def _speak():
        try:
            lang = detect_lang(text)
            set_voice_by_lang(lang)
            engine.say(text)
            engine.runAndWait()
        except Exception as e:
            print("Ошибка озвучки:", e)
    threading.Thread(target=_speak, daemon=True).start()

# --- Основной цикл
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
            else:
                input_text += e.unicode

    screen.fill(WHITE)
    pg.draw.rect(screen, GRAY, (20, 20, WIDTH - 40, HEIGHT - 140))
    pg.draw.rect(screen, GRAY, (20, HEIGHT - 100, WIDTH - 40, 80))

    y = 30
    for speaker, text in chat[-20:]:
        col = BLUE if speaker != 'Ты' else BLACK
        surf = font.render(f"{speaker}: {text}", True, col)
        screen.blit(surf, (30, y))
        y += 25

    surf_input = font.render(input_text, True, BLACK)
    screen.blit(surf_input, (30, HEIGHT - 90))

    pg.display.flip()
    clock.tick(60)

pg.quit()
sys.exit()
