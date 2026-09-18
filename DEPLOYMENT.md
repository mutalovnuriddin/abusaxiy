# Serverga o'rnatish (Deployment) qo'llanmasi

## 1. Server tayyorlash

```bash
# Python 3.12+ kerak
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

## 2. .env faylini to'ldirish

`.env` faylida **faqat loyihada ishlatiladigan** o'zgaruvchilar bor:

| O'zgaruvchi | Vazifasi |
|---|---|
| `SECRET_KEY` | Yangi tasodifiy kalit (quyidagi buyruq bilan generatsiya qiling) |
| `DEBUG` | Serverda albatta `False` |
| `ALLOWED_HOSTS` | Domen/IP lar, vergul bilan: `example.com,www.example.com` |
| `CSRF_TRUSTED_ORIGINS` | `https://example.com,https://www.example.com` |
| `DB_ENGINE` | `django.db.backends.sqlite3` (yoki `django.db.backends.postgresql`) |
| `DB_NAME` | SQLite fayl yo'li (PostgreSQL uchun: baza nomi) |
| `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT` | Faqat PostgreSQL ishlatsangiz kerak |
| `TELEGRAM_BOT_TOKEN` | Telegram bot tokeni (contact form uchun) |
| `TELEGRAM_CHAT_ID` | Telegram chat id (contact form uchun) |
| `SECURE_SSL_REDIRECT` | HTTPS yoqilganda `True` |
| `SESSION_COOKIE_SECURE` | HTTPS yoqilganda `True` |
| `CSRF_COOKIE_SECURE` | HTTPS yoqilganda `True` |
| `SECURE_HSTS_SECONDS` | HTTPS yoqilganda `31536000` |

Yangi `SECRET_KEY` generatsiya qilish:

```bash
python -c "import secrets; print(secrets.token_urlsafe(64))"
```

⚠️ Eski kalitni qayta ishlatmang — u kod tarixida ochiq qolgan. Telegram bot tokenini ham @BotFather orqali yangilab oling.

## 3. Ma'lumotlar bazasi va statik fayllar

```bash
python manage.py migrate
python manage.py collectstatic --noinput
python manage.py createsuperuser
```

PostgreSQL ishlatilsa: `DB_ENGINE=django.db.backends.postgresql` qilib, `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT` ni to'ldiring.

## 4. Gunicorn orqali ishga tushirish

```bash
gunicorn config.wsgi:application --bind 127.0.0.1:8000 --workers 3
```

Old tomonda Nginx (yoki boshqa HTTPS reverse proxy) turishi kerak: `/static/` — `staticfiles/` dan, `/media/` — `media/` dan xizmat qiladi.

## 5. Systemd servis (avtomatik ishga tushirish)

`/etc/systemd/system/django-shop.service`:

```ini
[Unit]
Description=Django shop (gunicorn)
After=network.target

[Service]
User=ubuntu
WorkingDirectory=/path/to/project
ExecStart=/path/to/project/venv/bin/gunicorn config.wsgi:application --bind 127.0.0.1:8000 --workers 3
Restart=always

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now django-shop
sudo systemctl status django-shop
```

## 6. Tekshirish

```bash
python manage.py check --deploy
```

Eslatma: serverda `DEBUG=True` qilmang va `.env` faylni gitga qo'shmang (`.gitignore`da allaqachon band).
