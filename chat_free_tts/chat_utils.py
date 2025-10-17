def wrap_text(text, font, max_width):
    """Разделяет текст на строки, учитывая длинные слова"""
    words = text.split(' ')
    lines = []
    line = ""
    
    for word in words:
        # Если слово слишком длинное, делим его на куски
        while font.size(word)[0] > max_width:
            for i in range(1, len(word)+1):
                if font.size(word[:i])[0] > max_width:
                    lines.append(word[:i-1])
                    word = word[i-1:]
                    break
        # Добавляем слово в текущую строку
        if font.size(line + word + " ")[0] > max_width:
            lines.append(line)
            line = word + " "
        else:
            line += word + " "
    if line.strip():
        lines.append(line.strip())
    return lines


def split_text(text, max_len=300):
    # Разбивка длинного текста на куски
    parts, current = [], ""
    for word in text.split():
        if len(current) + len(word) + 1 <= max_len:
            current += " " + word
        else:
            parts.append(current.strip())
            current = word
    if current:
        parts.append(current.strip())
    return parts

def format_edge_param(value: int) -> str:
    return f"{'+' if value >= 0 else ''}{value}%"
