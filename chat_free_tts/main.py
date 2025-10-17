import pygame as pg
import pyperclip
from chat_utils import wrap_text, split_text
import config
from speech import speak_async_chunked
import internet_check

# --- Pygame init ---
pg.init()
try:
    pg.mixer.init()
except Exception:
    # Если инициализация микшера не удалась, приложение всё ещё может работать без звука
    print("Warning: pygame.mixer init failed; audio may not work.")
WIDTH, HEIGHT = 800, 600
screen = pg.display.set_mode((WIDTH, HEIGHT), pg.RESIZABLE)
pg.display.set_caption("Free TTS Chat")
font = pg.font.SysFont("Arial", 22)
clock = pg.time.Clock()

chat = []
input_text = ''
voice_index = 0
use_offline = False
scroll_offset = 0
scroll_speed = 1
scrolling_up = scrolling_down = False
dark_mode = False
# шаги и границы для управления скоростью и громкостью (проценты)
SPEED_STEP = 10
VOLUME_STEP = 10
MIN_SPEED, MAX_SPEED = -50, 200
MIN_VOLUME, MAX_VOLUME = -100, 100


# --- UI обновление ---
def render_ui():
    screen.fill(config.WHITE)
    if dark_mode:
        bg_color = (30, 30, 30)
        panel_color = (50, 50, 50)
        text_color = (200, 200, 200)
        phone_color = (25,25,25)
    else:
        bg_color = config.WHITE
        panel_color = config.GRAY
        text_color = config.BLACK
        phone_color = config.GRAY

    screen.fill(bg_color)
    pg.draw.rect(screen, panel_color, (20, 20, WIDTH - 40, HEIGHT - 190))
    pg.draw.rect(screen, phone_color, (20, 20, WIDTH - 40, HEIGHT - 190))
    pg.draw.rect(screen, phone_color, (20, HEIGHT - 100, WIDTH - 40, 80))

    # высота строки и видимое количество
    line_height = 23
    max_lines_visible = (HEIGHT - 220) // line_height

    # формируем все строки для рендера
    all_lines = []
    for speaker, message in chat:
        color = config.BLUE if speaker != 'Ты' else text_color
        wrapped_lines = wrap_text(f"{speaker}: {message}", font, WIDTH - 60)
        for l in wrapped_lines:
            all_lines.append((l, color))

    # прокрутка
    start_index = max(0, len(all_lines) - max_lines_visible - scroll_offset)
    end_index = len(all_lines) - scroll_offset if scroll_offset != 0 else None
    visible_lines = all_lines[start_index:end_index]

    # отображаем строки
    y = 30
    for line, color in visible_lines:
        surf = font.render(line, True, color)
        screen.blit(surf, (30, y))
        y += line_height
    # нижняя панель
    screen.blit(font.render(f"Громкость: {config.speech_volume}", True, text_color), (20, HEIGHT - 160))
    screen.blit(font.render(f"Скорость: {config.speech_speed}", True, text_color), (20, HEIGHT - 130))
    screen.blit(font.render(f"Голос: {config.voices_list[voice_index][1]}", True, text_color), (300, HEIGHT - 160))
    is_offline_mode = use_offline or not internet_check.internet_status
    screen.blit(font.render(f"Режим: {'Офлайн' if is_offline_mode else 'Онлайн'}",
                            True, config.RED if is_offline_mode else config.GREEN), (300, HEIGHT - 130))

    input_surf = font.render(input_text, True, text_color)
    screen.blit(input_surf, (30, HEIGHT - 90))
    # Кружочек должен быть зелёным только если мы в онлайн-режиме и интернет доступен
    circle_color = config.GREEN if (not use_offline and internet_check.internet_status) else config.RED
    pg.draw.circle(screen, circle_color, (20, 10), 6)

# --- Главный цикл ---
running = True
while running:
    for e in pg.event.get():
        if e.type == pg.QUIT or (e.type == pg.KEYDOWN and e.key == pg.K_ESCAPE):
            running = False
        elif e.type == pg.VIDEORESIZE:
            WIDTH, HEIGHT = e.w, e.h
            screen = pg.display.set_mode((WIDTH, HEIGHT), pg.RESIZABLE)
        elif e.type == pg.KEYDOWN:
            mods = pg.key.get_mods()
            if e.key == pg.K_BACKSPACE:
                input_text = input_text[:-1]
            elif e.key == pg.K_RETURN:
                if input_text.strip():
                    chat.append(('Ты', input_text))
                    speak_async_chunked(input_text, voice_index, use_offline, config.speech_speed, config.speech_volume)
                    input_text = ''
                    scroll_offset = 0
            elif e.key == pg.K_v and mods & pg.KMOD_CTRL:
                input_text += pyperclip.paste()
            elif e.key == pg.K_F2:
                voice_index = (voice_index + 1) % len(config.voices_list)
            elif e.key == pg.K_F3:
                use_offline = not use_offline
            elif e.key == pg.K_PAGEUP:
                scrolling_up = True
            elif e.key == pg.K_PAGEDOWN:
                scrolling_down = True
            elif e.key == pg.K_F9:
                dark_mode = not dark_mode
            elif e.key == pg.K_LEFT:
                # уменьшить скорость
                new_speed = max(MIN_SPEED, config.speech_speed - SPEED_STEP)
                config.speech_speed = new_speed
            elif e.key == pg.K_RIGHT:
                # увеличить скорость
                new_speed = min(MAX_SPEED, config.speech_speed + SPEED_STEP)
                config.speech_speed = new_speed
            elif e.key == pg.K_UP:
                # увеличить громкость
                new_vol = min(MAX_VOLUME, config.speech_volume + VOLUME_STEP)
                config.speech_volume = new_vol
            elif e.key == pg.K_DOWN:
                # уменьшить громкость
                new_vol = max(MIN_VOLUME, config.speech_volume - VOLUME_STEP)
                config.speech_volume = new_vol
            else:
                if len(input_text) < config.MAX_INPUT_LEN:
                    input_text += e.unicode
        elif e.type == pg.KEYUP:
            if e.key == pg.K_PAGEUP:
                scrolling_up = False
            elif e.key == pg.K_PAGEDOWN:
                scrolling_down = False


    # авто-прокрутка при удержании
    if scrolling_up:
        scroll_offset = min(scroll_offset + scroll_speed, 20)
    if scrolling_down:
        scroll_offset = max(scroll_offset - scroll_speed, 0)

    render_ui()
    pg.display.flip()
    clock.tick(60)

pg.quit()
