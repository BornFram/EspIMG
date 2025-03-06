from PIL import Image, ImageSequence
import io

DISPALY_WIDTH = 320 
DISPLAY_HEIGHT = 240
DISPLAY_SIZE = (DISPALY_WIDTH, DISPLAY_HEIGHT)

S_STRETCH = "stretch"
S_FITTED = "fitted"
S_CROP = "crop"

def get_fit_res(width, height, type=S_STRETCH, 
                max_width=DISPALY_WIDTH, max_height=DISPLAY_HEIGHT):
    """
    Возвращает разрешение для картинки, которое вместится в заданные максимальные размеры,
    сохраняя соотношение сторон.

    :param width: Исходная ширина.
    :param height: Исходная высота.
    :param max_width: Максимально допустимая ширина.
    :param max_height: Максимально допустимая высота.

    :return tuple: Новое разрешение (ширина, высота).
    """
    new_width = max_width
    new_height = max_height
    if (type == S_STRETCH):
        new_width = max_width
        new_height = max_height
        
    elif (type == S_FITTED):
    # Вычисляем коэффициент масштабирования по ширине и высоте
        scale_by_width = min(1.0, max_width / width)
        scale_by_height = min(1.0, max_height / height)

        # Используем наименьший коэффициент масштабирования для сохранения соотношения сторон
        scale_factor = min(scale_by_width, scale_by_height)

        # Вычисляем новое разрешение с учетом масштабирования
        new_width = int(width * scale_factor)
        new_height = int(height * scale_factor)
        
    elif (type == S_CROP):
        # TODO: crop image. здесь уже нужно юзать саму либу,тк надо будет обрезать изображение
        new_width = max_width
        new_height = max_height

    return (new_width, new_height)


def compress_gif(input_bytes, 
                 target_size=(DISPALY_WIDTH, DISPLAY_HEIGHT), 
                 max_colors=64, skip_frames=0, dispsl=5, qlty=85, 
                 frame_limit=80):
    """
    Сжимает GIF-файл.
    
    :param input_bytes: Исходные данные GIF в виде байтов.
    :param target_size: Размер (ширина, высота) для уменьшения GIF.
    :param max_colors: Максимальное количество цветов в палитре (чем меньше, тем сильнее сжатие).
    :param skip_frames: Количество кадров для пропуска между сохраняемыми кадрами (0 - не пропускать).
    :param displ: процент удаления лишнего
    :param qlty: качество (?)
    
    img.info.get('duration', 100) - продолжительность одного кадра
    
    :return bytes: Сжатые данные GIF в виде байтов.
    
    """
    koef_for_dura = 40 # на это число умножается ским-фрейм и получается новая продолжительность одного кадра
    
    # Открываем исходный GIF из потока байтов
    with io.BytesIO(input_bytes) as byte_stream:
        img = Image.open(byte_stream)
        
        frames = []
        frame_index = 0
        
        for frame in ImageSequence.Iterator(img):
            if skip_frames > 0 and frame_index % (skip_frames + 1) != 0:
                frame_index += 1
                continue
            
            if frame_index > frame_limit:
                break
            
            # Изменяем размер каждого кадра
            resized_frame = frame.resize(target_size)
            
            # Уменьшаем количество цветов для каждого кадра
            optimized_frame = resized_frame.convert('P', palette=Image.ADAPTIVE, colors=max_colors)
            
            frames.append(optimized_frame)
            
            frame_index += 1
            
        #print(img.info.get('duration', 100))
        # Сохраняем оптимизированный GIF в поток байтов
        with io.BytesIO() as output_byte_stream:
            dura = skip_frames * koef_for_dura
            
            frames[0].save(output_byte_stream,
                           save_all=True,
                           append_images=frames[1:],
                           optimize=True,
                           duration=img.info.get('duration', 100)+dura,
                           disposal=dispsl,
                           quality=qlty,
                           format='GIF')

            return output_byte_stream.getvalue()

# Пример использования функции с чтением файла и записью результата обратно в файлы через IO-операции
'''
with open('input.gif', 'rb') as file:
    input_bytes = file.read()

print(len(input_bytes)/1024)
output_bytes = compress_gif(input_bytes,
                            target_size=(320, 240),
                            max_colors=64,
                            skip_frames=2,
                            dispsl=40,
                            qlty=10)
print(len(output_bytes)/1024)
with open('output.gif', 'wb') as file:
    file.write(output_bytes)
'''

