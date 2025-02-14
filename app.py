# app.py
# TODO: декоратор на авторизацию
# TODO: встроить структуру (каждая функция в свой файл) или перейти на жангу


import os
import sqlite3
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, flash, session, send_from_directory, g
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename

from flask import Response
from PIL import Image
import io

# -----PARAMETERS -----
picExt = ".png"
# ---------------------

app = Flask(__name__)

# Конфигурация приложения
app.config['SECRET_KEY'] = 'your_secret_key'  # КЛЮЧ
# Файл базы данных с расширением .sqlite
app.config['DATABASE'] = os.path.join(app.root_path, 'schema.sqlite')
app.config['UPLOAD_FOLDER'] = os.path.join(app.root_path, 'uploads')
#app.config['ALLOWED_EXTENSIONS'] = {'jpg', 'jpeg'}
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg'}

# Если папка для загрузок не существует, то соаздём её
if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])


# Функция для получения соединения с базой данных
def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(app.config['DATABASE'])
        db.row_factory = sqlite3.Row  # Чтобы строки возвращались в виде словарей
    return db


# Функция инициализации базы данных из файла schema.sql
def init_db():
    with app.app_context():
        db = get_db()
        with app.open_resource('schema.sqlite', mode='r') as f:
            db.executescript(f.read())
        db.commit()
        print("База данных успешно инициализирована.")


# Закрытие соединения с БД после обработки запроса
@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()


# Проверка допустимого расширения файла
def allowed_file(img_name):
    return '.' in img_name and img_name.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']


# Главная страница (список изображений авторизованного пользователя)
@app.route('/')
def index():
    if 'user_id' in session:
        db = get_db()
        cur = db.cursor()
        cur.execute("SELECT * FROM images WHERE user_id = ?", (session['user_id'],))
        images = cur.fetchall()
        return render_template('index.html', images=images)
    else:
        return redirect(url_for('login'))


# Страница регистрации
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username'].strip()
        password = request.form['password']
        email = request.form['email'].strip()

        if not username or not password:
            flash("Имя пользователя и пароль обязательны для заполнения.")
            return redirect(url_for('register'))

        db = get_db()
        cur = db.cursor()
        # Проверяем, существует ли пользователь с таким именем
        cur.execute("SELECT id FROM users WHERE username = ?", (username,))
        if cur.fetchone() is not None:
            flash("Пользователь с таким именем уже существует.")
            return redirect(url_for('register'))

        hashed_password = generate_password_hash(password)
        cur.execute("INSERT INTO users (username, password, email) VALUES (?, ?, ?)",
                    (username, hashed_password, email))
        db.commit()
        flash("Регистрация прошла успешно! Теперь войдите в систему.")
        return redirect(url_for('login'))
    return render_template('register.html')


# Страница входа (авторизации)
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username'].strip()
        password = request.form['password']
        db = get_db()
        cur = db.cursor()
        cur.execute("SELECT * FROM users WHERE username = ?", (username,))
        user = cur.fetchone()
        if user is None or not check_password_hash(user['password'], password):
            flash("Неверное имя пользователя или пароль.")
            return redirect(url_for('login'))

        session['user_id'] = user['id']
        session['username'] = user['username']
        flash("Вы успешно вошли в систему.")
        return redirect(url_for('index'))
    return render_template('login.html')


# Выход из системы
@app.route('/logout')
def logout():
    session.pop('user_id', None)
    session.pop('username', None)
    flash("Вы вышли из системы.")
    return redirect(url_for('login'))


# Страница загрузки изображения
@app.route('/upload', methods=['GET', 'POST'])
def upload():
    if 'user_id' not in session:
        flash("Необходимо войти в систему.")
        return redirect(url_for('login'))

    if request.method == 'POST':
        if 'file' not in request.files:
            flash("Файл не найден в запросе.")
            return redirect(request.url)
        file = request.files['file']
        
        if file.filename == '':
            flash("Файл не выбран.")
            return redirect(request.url)
        if file and allowed_file(file.filename):
            img_name = secure_filename(file.filename)
            # Чтение бинарных данных из файла
            image_data = file.read()
            # Сохраняем бинарные данные в БД
            db = get_db()
            cur = db.cursor()
            cur.execute(
                "INSERT INTO images (user_id, image_data, filename) VALUES (?, ?, ?)",
                (session['user_id'], image_data, img_name)
            )
            db.commit()
            flash("Файл успешно загружен и сохранён в базе данных.")
            return redirect(url_for('index'))
        else:
            flash("Неверный формат файла. Допустимы только JPEG. и .PNG")
            return redirect(request.url)
    return render_template('upload.html')


from flask import Response

@app.route('/get_image/<int:image_id>')
def get_image(image_id):
    db = get_db()
    cur = db.cursor()
    cur.execute("SELECT image_data FROM images WHERE id = ?", (image_id,))
    row = cur.fetchone()
    if row:
        # Возвращаем бинарные данные изображения
        return Response(row['image_data'], mimetype='image/jpeg')
    else:
        return "Изображение не найдено", 404

@app.route('/delete_image/<int:image_id>', methods=['POST'])
def delete_image(image_id):
    db = get_db()
    cur = db.cursor()
    cur.execute("DELETE FROM images WHERE id = ?", (image_id,))
    db.commit()

    print(f"Изображение с ID {image_id} удалено.")  # Замените на реальное удаление
    return '', 204  # Успешное удаление, возвращаем пустой ответ с кодом 204

# -----------------------------------------------------------

@app.route('/checking', methods=['POST'])
def device_checking():
    print("--- checking ---")
    # auth
    auth_header = request.headers.get('Authorization')
    credentials_pair = auth_header.split(" ")[1]
    credentialsDecode = credentials_pair #credentials_pair.decode("utf-8")
    
    userLogin = credentialsDecode.split(":")[0]
    deviceID = credentialsDecode.split(":")[1]
    
    print("--- response for "+userLogin)
    if userLogin:
        device_images = request.data.decode('utf-8')
        device_images = device_images.split()
        
        print(device_images)
    
        responso = {"remove":[], "update":[], "updateNum": 0}
        
        db = get_db()
        cur = db.cursor()
        cur.execute("SELECT id FROM users WHERE username = ?", (userLogin,))
        user_id = cur.fetchone()
        
        cur.execute("SELECT id FROM images WHERE user_id = ?", (user_id[0],))
        images_in_db = cur.fetchall()
        for i in range(len(images_in_db)):
            images_in_db[i] = str(images_in_db[i]["id"]) + picExt #'.png'
        
        missing_images_count = 0
        
        #files_to_delete = [file for file in device_images if file not in images_in_db]
        #missing_images_count = sum(1 for file in images_in_db if file not in device_images)
        
        for file in device_images:
            if file not in images_in_db:
                responso["remove"].append(file)

        for file in images_in_db:
            if file not in device_images:
                responso["update"].append(file)
                missing_images_count += 1
        
        responso["updateNum"] = missing_images_count
        print("responso:")
        print(responso)
        #responso = {"remove":[], "update":[], "updateNum": 0}
        return responso
       
    return "Unauthorized", 401


@app.route('/pic-update', methods=['GET'])
def get_imagee():
    # auth
    print("--- pic-upgate ---")
    auth_header = request.headers.get('Authorization')
    print(auth_header)
    credentials_pair = auth_header.split(" ")[1]
    credentialsDecode = credentials_pair #credentials_pair.decode("utf-8")
    
    needPic = request.headers.get('filename')
    print(needPic)
    
    userLogin = credentialsDecode.split(":")[0]
    deviceID = credentialsDecode.split(":")[1]

    print("--- response for "+userLogin)
    if userLogin:
        db = get_db()
        cur = db.cursor()
        
        cur.execute("SELECT id FROM users WHERE username = ?", (userLogin,))
        user_id = cur.fetchone()
        cur.execute("SELECT image_data FROM images WHERE id = ?", (needPic.split('.')[0],))
        img = cur.fetchone()
        
        img_data = img["image_data"]
        img_name = needPic
        
        image = Image.open(io.BytesIO(img_data))
        image = image.resize((320,240))
        img_byte_arr = io.BytesIO()
        image.save(img_byte_arr, format='PNG')
        img_byte_arr = img_byte_arr.getvalue()
        
        print("file name: "+img_name)

        b = (img_name + '\n')
        b = b.encode("utf-8")
        #img_data = b + img_data
        send_data = b + img_byte_arr
        
        respo = Response(
            response=send_data,
            status=200,
            mimetype='image/png',
            headers={
                'Content-Disposition': f'attachment; img_name="{img_name}"',
                'X-File-Name': img_name
            }
        )
        return respo
       
    return "Unauthorized", 401


# Запуск приложения
if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)
