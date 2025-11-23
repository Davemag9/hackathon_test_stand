# Photo Verification Utility для Дія

Утиліта для автоматичної перевірки фотографій на відповідність вимогам документів. Рішення усуває типові помилки користувачів під час завантаження фото для цифрових послуг у застосунку Дія та підвищує зручність і швидкість отримання цих послуг.

## Опис продукту

Застосунок аналізує зображення в режимі реального часу (до 2 кадрів/с) та надає миттєві підказки, які саме критерії не виконані:

- ✅ Неправильне розміщення обличчя
- ✅ Заплющені очі
- ✅ Відсутність прямого погляду
- ✅ Наявність окулярів
- ✅ Неоднорідний чи темний фон
- ✅ Вертикальне вирівнювання обличчя

Це дозволяє користувачу швидко скоригувати фото, не створюючи надмірного відеопотоку.

## Технології

- **Backend**: FastAPI, Python
- **Frontend**: HTML, CSS, JavaScript
- **Computer Vision**: MediaPipe, OpenCV
- **Machine Learning**: PyTorch (для класифікації окулярів)

## Вимоги

- Python 3.11+
- Веб-камера (для роботи з фронтендом)
- Мінімум 4GB RAM (рекомендовано 8GB)

## Встановлення

### 1. Клонування репозиторію

```bash
git clone https://github.com/Davemag9/hackathon_test_stand.git
cd hackathon_test_stand
```

### 2. Створення віртуального середовища

```bash
python3 -m venv venv
```

### 3. Активація віртуального середовища

**macOS/Linux:**
```bash
source venv/bin/activate
```

**Windows:**
```bash
venv\Scripts\activate
```

### 4. Встановлення залежностей

```bash
pip install -r requirements.txt
```

## Запуск

### Запуск Backend

1. Переконайтеся, що віртуальне середовище активовано
2. Запустіть сервер:

```bash
python app.py
```

Або використовуючи uvicorn безпосередньо:

```bash
uvicorn app:app --host 127.0.0.1 --port 8000 --reload
```

Backend буде доступний за адресою: `http://127.0.0.1:8000`

### Запуск Frontend

1. Відкрийте файл `front for hackathon/index.html` у веб-браузері
2. Або запустіть локальний веб-сервер:

```bash
# З кореневої директорії проєкту
cd "front for hackathon"
python3 -m http.server 8080
```

Потім відкрийте в браузері: `http://localhost:8080`

**Альтернативний спосіб (якщо встановлено Node.js):**

```bash
cd "front for hackathon"
npx http-server -p 8080
```

## Використання

1. Відкрийте фронтенд у браузері
2. Натисніть "Start Camera" для активації веб-камери
3. Виберіть один з режимів:
   - **Capture Photo** - зробити фото та відправити на аналіз
   - **Start Live Analysis** - аналіз в реальному часі (до 2 кадрів/с)
4. Отримайте детальний звіт про відповідність фото вимогам

## API Endpoints

### Health Check
```
GET http://127.0.0.1:8000/
```

### Класифікація фото
```
POST http://127.0.0.1:8000/api/classify
Content-Type: multipart/form-data

Body: file (image/jpeg, image/png, image/jpg)
```

**Response:**
```json
{
  "no_glasses": true,
  "is_centered": true,
  "open_eye_status": true,
  "eyes_centered": true,
  "is_vertical_straight": true,
  "is_bg_uniform": true,
  "is_bg_bright": true,
  "is_valid_photo": true,
  "report_info": "..."
}
```

## Структура проєкту

```
hackathon_test_stand/
├── app.py                      # Головний файл FastAPI додатку
├── requirements.txt            # Python залежності
├── src/
│   ├── mediapipe_service.py   # MediaPipe обробка зображень
│   ├── classification_serice.py # Класифікація зображень
│   ├── router.py              # API роути
│   └── utils.py               # Допоміжні функції
├── front for hackathon/
│   ├── index.html             # Головна сторінка
│   ├── style.css              # Стилі
│   └── script.js              # JavaScript логіка
└── data/
    └── best_model.pth         # Модель для класифікації окулярів
```

## Розробка

Для розробки з автоматичним перезавантаженням:

```bash
uvicorn app:app --host 127.0.0.1 --port 8000 --reload
```

## Примітки

- Переконайтеся, що веб-камера доступна та дозволена для використання браузером
- Для кращої продуктивності використовуйте Chrome або Edge браузери
- Модель `best_model.pth` повинна бути присутня в директорії `data/`

## Ліцензія

[Вкажіть ліцензію проєкту]

## Автори

[Вкажіть авторів проєкту]

