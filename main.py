import requests
import json
import urllib.parse
import sys


class CatImageAPI:
    """Класс для получения изображений с cataas.com."""
    BASE_URL = "https://cataas.com/cat/says/"

    def __init__(self, text: str):
        if not text or not text.strip():
            raise ValueError("Текст для картинки не может быть пустым.")
        self.text = text.strip()

    def get_image(self) -> bytes:
        """Скачивает изображение с текстом и возвращает его в виде байтов."""
        # Кодируем текст для безопасной передачи в URL (например, пробелы)
        encoded_text = urllib.parse.quote(self.text)
        url = f"{self.BASE_URL}{encoded_text}"

        response = requests.get(url)
        response.raise_for_status()

        # Проверяем, что сервер вернул именно изображение
        if not response.headers.get('Content-Type', '').startswith('image/'):
            raise ValueError("API cataas.com вернул не изображение.")

        return response.content


class YandexDiskAPI:
    """Класс для работы с REST API Яндекс.Диска."""
    BASE_URL = "https://cloud-api.yandex.net/v1/disk"

    def __init__(self, token: str):
        if not token:
            raise ValueError("Токен Яндекс.Диска не может быть пустым.")
        self.headers = {
            "Authorization": f"OAuth {token}",
            "Content-Type": "application/json"
        }

    def create_folder(self, folder_name: str) -> bool:
        """Создает папку на Яндекс.Диске, если её еще нет."""
        url = f"{self.BASE_URL}/resources"
        # Путь к папке должен быть закодирован (например, /PYAPI-162)
        params = {"path": f"/{folder_name}"}

        response = requests.put(url, headers=self.headers, params=params)

        # Код 201 означает успешное создание
        if response.status_code == 201:
            return True
        # Если папка уже существует (код 409), это не ошибка для нас
        elif response.status_code == 409:
            print(f"Папка '{folder_name}' уже существует на Диске. Будем использовать её.")
            return True
        else:
            # Если произошла другая ошибка, выводим детали
            print(f"Ошибка при создании папки: {response.status_code} {response.text}")
            response.raise_for_status()
            return False

    def upload_image(self, folder_name: str, file_name: str, image_bytes: bytes) -> dict:
        """Загружает изображение в указанную папку на Диске по ссылке для загрузки."""
        # 1. Получаем URL, по которому нужно загрузить файл
        url = f"{self.BASE_URL}/resources/upload"
        # Путь к файлу: /PYAPI-162/текст.jpg
        params = {
            "path": f"/{folder_name}/{file_name}",
            "overwrite": "true"  # Перезаписываем, если файл с таким именем уже есть
        }

        response = requests.get(url, headers=self.headers, params=params)
        response.raise_for_status()

        # В ответе получаем ссылку для загрузки
        upload_url = response.json().get("href")

        # 2. Загружаем файл по полученной ссылке
        # Для загрузки данных используется метод PUT, заголовок Content-Type не нужен
        upload_response = requests.put(upload_url, data=image_bytes)
        upload_response.raise_for_status()

        # Возвращаем информацию об успешной загрузке
        return {
            "filename": file_name,
            "size_bytes": len(image_bytes),
            "status": "uploaded"
        }


def save_metadata_to_json(data: dict, file_path: str = "result.json"):
    """Сохраняет информацию о загруженном файле в локальный JSON-файл."""
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)
    print(f"Информация сохранена в {file_path}")


def main():
    print("--- Резервное копирование котиков на Яндекс.Диск ---")

    # 1. Ввод данных от пользователя
    user_text = input("Введите текст для картинки: ")

    # Создаем безопасное имя файла: заменяем недопустимые символы в имени файла на "_"
    # В Windows и Linux запрещены символы: \ / : * ? " < > |
    invalid_chars = '<>:"/\\|?*'
    safe_filename = user_text
    for char in invalid_chars:
        safe_filename = safe_filename.replace(char, '_')
    safe_filename += ".jpg"  # Добавляем расширение

    token = input("Введите OAuth-токен Яндекс.Диска: ").strip()

    # 2. Выполнение операций
    try:
        # Получаем картинку
        print("Получение изображения с cataas.com...")
        cat_api = CatImageAPI(user_text)
        image_data = cat_api.get_image()
        print(f"Изображение получено. Размер: {len(image_data)} байт.")

        # Работа с Яндекс.Диском
        disk_api = YandexDiskAPI(token)

        # Название папки по заданию
        folder_name = "PYAPI-162"
        print(f"Создание папки {folder_name} на Яндекс.Диске...")
        disk_api.create_folder(folder_name)

        # Загрузка файла
        print(f"Загрузка файла '{safe_filename}' на Яндекс.Диск...")
        file_info = disk_api.upload_image(folder_name, safe_filename, image_data)

        # 3. Сохранение информации в JSON
        save_metadata_to_json(file_info)

        print("--- Готово! Все задачи выполнены. ---")

    except ValueError as ve:
        print(f"Ошибка в данных: {ve}")
    except requests.exceptions.RequestException as re_err:
        print(f"Ошибка сети или API: {re_err}")
    except Exception as e:
        print(f"Произошла непредвиденная ошибка: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()