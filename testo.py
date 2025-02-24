from PIL import Image
import os

def get_ext(file_bytes):
    """
    Определяет расширение файла по массиву байтов.

    Args:
        file_bytes (bytes): Массив байтов файла.

    Returns:
        str: Расширение файла или None, если тип не распознан.
    """
    # Определяем магические числа для различных типов файлов
    magic_numbers = {
        b'\x89PNG\r\n\x1a\n': '.png',  # PNG
        b'GIF8': '.gif',                # GIF
        b'\xff\xd8\xff': '.jpg',        # JPEG
        b'PK\x03\x04': '.zip',          # ZIP
        b'%PDF-': '.pdf',               # PDF
        b'RIFF': '.wav',                # WAV (RIFF)
        b'WAVE': '.wav',                # WAV (WAVE)
        b'ID3': '.mp3',                 # MP3
        b'OggS': '.ogg',                # OGG
        b'BZh': '.bz2',                 # BZ2
        b'7z\xBC\xAF\x27\x1C': '.7z',   # 7z
    }

    for magic, extension in magic_numbers.items():
        if file_bytes.startswith(magic):
            return extension

    return None

image_path = 'cubes.png'
with open(image_path, "rb") as image_file:
    image_binary = image_file.read()

exto = get_ext(image_binary)
print(exto)