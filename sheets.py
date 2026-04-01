"""
Модуль для записи данных в Google Sheets.

Настройка:
1. Создайте проект в Google Cloud Console
2. Включите Google Sheets API и Google Drive API
3. Создайте Service Account и скачайте credentials.json
4. Поделитесь таблицей с email сервис-аккаунта
5. Вставьте ID таблицы в SPREADSHEET_ID ниже
"""

import gspread
from google.oauth2.service_account import Credentials
from config import SPREADSHEET_ID, CREDENTIALS_FILE

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]

# Заголовки колонок в таблице
HEADERS = [
    "Дата отправки",
    "Дата рейса",
    "Водитель",
    "Машина",
    "Количество рейсов",
    "Карьер/Завод",
    "Клиент",
    "Материал",
    "Тоннаж (т)",
    "Фото ТН",
    "Telegram ID",
]


def get_sheet():
    """Подключиться к Google Sheets."""
    creds = Credentials.from_service_account_file(CREDENTIALS_FILE, scopes=SCOPES)
    client = gspread.authorize(creds)
    spreadsheet = client.open_by_key(SPREADSHEET_ID)

    # Используем первый лист или создаём "Отчёты"
    try:
        sheet = spreadsheet.worksheet("Отчёты")
    except gspread.WorksheetNotFound:
        sheet = spreadsheet.add_worksheet(title="Отчёты", rows=1000, cols=20)
        sheet.append_row(HEADERS)

    return sheet


def ensure_headers(sheet):
    """Добавить заголовки если таблица пустая."""
    if sheet.row_count == 0 or not sheet.row_values(1):
        sheet.append_row(HEADERS)


def save_report(data: dict):
    """Сохранить отчёт водителя в Google Sheets."""
    sheet = get_sheet()
    ensure_headers(sheet)

    row = [
        data.get("submitted_at", ""),
        data.get("date", ""),
        data.get("driver", ""),
        data.get("truck", ""),
        data.get("trips", ""),
        data.get("quarry", ""),
        data.get("client", ""),
        data.get("material", ""),
        data.get("tonnage", ""),
        data.get("photo_url", ""),
        str(data.get("telegram_id", "")),
    ]

    sheet.append_row(row)
