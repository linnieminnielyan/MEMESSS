from flask import Flask, render_template, request, redirect, url_for, flash, session
import sqlite3
import os
from PIL import Image, ImageDraw, ImageFont
import uuid
from functools import wraps

app = Flask(__name__)
app.secret_key = 'секретныйключ123'

os.makedirs('static/uploads', exist_ok=True)
os.makedirs('static/memes', exist_ok=True)


def get_db():
    conn = sqlite3.connect('memes.db')
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db()
    conn.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    ''')
    conn.execute('''
        CREATE TABLE IF NOT EXISTS memes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            image_path TEXT NOT NULL,
            top_text TEXT NOT NULL,
            bottom_text TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    conn.commit()
    conn.close()

def update_db():
    conn = get_db()
    try:
        conn.execute('ALTER TABLE memes ADD COLUMN text_color TEXT DEFAULT "white"')
        conn.commit()
        print("База данных обновлена")
    except:
        print("Колонка уже существует")
    conn.close()

update_db()
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Пожалуйста, войдите')
            return redirect(url_for('auth'))
        return f(*args, **kwargs)

    return decorated_function

def create_meme(image_path, top_text, bottom_text, output_path, text_color='white'):
    img = Image.open(image_path)
    if img.mode != 'RGB':
        img = img.convert('RGB')

    draw = ImageDraw.Draw(img)
    width, height = img.size

    font_size = int(height / 10)

    font = None
    possible_fonts = ["impact.ttf", "ofont.ru_Impact.ttf", "ofont.ru_Impact", "Impact.ttf", "arial.ttf"]

    for font_name in possible_fonts:
        try:
            font = ImageFont.truetype(font_name, font_size)
            break
        except:
            continue

    if font is None:
        font = ImageFont.load_default()

    if text_color == 'pink':
        main_color = (255, 182, 193)
        outline_color = 'black'
    else:
        main_color = 'white'
        outline_color = 'black'

    def split_text(text, max_chars=30):
        if not text:
            return []
        text = text.upper()
        words = text.split()
        lines = []
        current_line = []
        for word in words:
            if len(' '.join(current_line + [word])) <= max_chars:
                current_line.append(word)
            else:
                if current_line:
                    lines.append(' '.join(current_line))
                current_line = [word]
        if current_line:
            lines.append(' '.join(current_line))
        return lines

    if top_text:
        top_lines = split_text(top_text, 30)
        y = 20
        for line in top_lines:
            bbox = draw.textbbox((0, 0), line, font=font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
            x = (width - text_width) // 2

            for dx, dy in [(-2, -2), (-2, 2), (2, -2), (2, 2), (0, -2), (0, 2), (-2, 0), (2, 0)]:
                draw.text((x + dx, y + dy), line, font=font, fill=outline_color)
            draw.text((x, y), line, font=font, fill=main_color)
            y += text_height + 10

    if bottom_text:
        bottom_lines = split_text(bottom_text, 30)
        y = height - 80
        for line in reversed(bottom_lines):
            bbox = draw.textbbox((0, 0), line, font=font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
            x = (width - text_width) // 2
            y -= text_height

            for dx, dy in [(-2, -2), (-2, 2), (2, -2), (2, 2), (0, -2), (0, 2), (-2, 0), (2, 0)]:
                draw.text((x + dx, y + dy), line, font=font, fill=outline_color)
            draw.text((x, y), line, font=font, fill=main_color)
            y -= 10

    img.save(output_path, 'JPEG', quality=95)

@app.route('/')
def auth():
    if 'user_id' in session:
        return redirect(url_for('meme'))
    return render_template('auth.html')


@app.route('/login', methods=['POST'])
def login():
    username = request.form['username']
    password = request.form['password']
    db = get_db()
    user = db.execute('SELECT * FROM users WHERE username = ? AND password = ?', (username, password)).fetchone()
    db.close()
    if user:
        session['user_id'] = user['id']
        session['username'] = user['username']
        flash('Вход выполнен')
        return redirect(url_for('meme'))
    else:
        flash('Неверное имя или пароль')
        return redirect(url_for('auth'))


@app.route('/register', methods=['POST'])
def register():
    username = request.form['username']
    password = request.form['password']
    db = get_db()
    existing = db.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()
    if existing:
        flash('Пользователь уже существует')
        db.close()
        return redirect(url_for('auth'))
    db.execute('INSERT INTO users (username, password) VALUES (?, ?)', (username, password))
    db.commit()
    db.close()
    flash('Регистрация успешна! Теперь войдите')
    return redirect(url_for('auth'))


@app.route('/meme', methods=['GET', 'POST'])
@login_required
def meme():
    if request.method == 'POST':
        if 'image' not in request.files:
            flash('Выберите картинку')
            return redirect(url_for('meme'))
        file = request.files['image']
        top_text = request.form.get('top_text', '')
        bottom_text = request.form.get('bottom_text', '')
        text_color = request.form.get('text_color', 'white')

        if file.filename == '':
            flash('Выберите картинку')
            return redirect(url_for('meme'))

        ext = file.filename.rsplit('.', 1)[1].lower()
        filename = f"{uuid.uuid4().hex}.{ext}"
        original_path = os.path.join('static/uploads', filename)
        file.save(original_path)

        meme_filename = f"meme_{uuid.uuid4().hex}.jpg"
        meme_path = os.path.join('static/memes', meme_filename)

        try:
            create_meme(original_path, top_text, bottom_text, meme_path, text_color)

            db = get_db()
            db.execute(
                'INSERT INTO memes (user_id, image_path, top_text, bottom_text, text_color) VALUES (?, ?, ?, ?, ?)',
                (session['user_id'], f'/static/memes/{meme_filename}', top_text, bottom_text, text_color))
            db.commit()
            db.close()
            flash('Мем создан')
        except Exception as e:
            flash(f'Ошибка: {e}')
        return redirect(url_for('meme'))

    db = get_db()
    memes = db.execute('SELECT * FROM memes WHERE user_id = ? ORDER BY created_at DESC',
                       (session['user_id'],)).fetchall()
    db.close()
    return render_template('meme.html', memes=memes, username=session['username'])


@app.route('/logout')
def logout():
    session.clear()
    flash('Вы вышли')
    return redirect(url_for('auth'))


if __name__ == '__main__':
    init_db()
    app.run(debug=True, port=5000)