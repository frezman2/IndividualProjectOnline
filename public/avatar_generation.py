from PIL import Image, ImageDraw, ImageFont
import random
import io


def generate_avatar(nickname, size=128):
    """
    Генератор аватарок по нику (включая поддержку русского текста).
    
    :param nickname: Имя пользователя (строка).
    :param size: Размер аватарки (квадрат) в пикселях.
    :return: Байты PNG-изображения.
    """
    # Случайный цвет фона
    background_color = tuple(random.randint(0, 255) for _ in range(3))
    
    # Цвет текста (чтобы был читаемым)
    text_color = (255, 255, 255) if sum(background_color) < 382 else (0, 0, 0)

    # Инициал(ы) из ника (первая буква каждого слова)
    initials = ''.join(word[0].upper() for word in nickname.split() if word).strip()

    # Создание изображения
    img = Image.new("RGB", (size, size), background_color)
    draw = ImageDraw.Draw(img)

    # Загрузка шрифта (путь к системному шрифту)
    try:
        font = ImageFont.truetype("arial.ttf", int(size * 0.4))
    except IOError:
        font = ImageFont.load_default()

    # Размер текста и его позиционирование
    text_bbox = draw.textbbox((0, 0), initials, font=font)  # Получение границ текста
    text_width = text_bbox[2] - text_bbox[0]
    text_height = text_bbox[3] - text_bbox[1]
    text_position = ((size - text_width) / 2, (size - text_height) / 2 - text_bbox[1])

    # Рисование текста
    draw.text(text_position, initials, fill=text_color, font=font)

    # Сохранение в байты
    output = io.BytesIO()
    img.save(output, format="PNG")
    return output.getvalue()


# Тестирование генератора
if __name__ == "__main__":
    nickname = "Иван Иванов"
    avatar = generate_avatar(nickname)
    with open("avatar.png", "wb") as f:
        f.write(avatar)
