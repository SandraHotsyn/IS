import requests

def download_database():
    file_id = "1amblywCXghM9ckCAdZdk9XjdY3I6fkR3"
    url = f"https://drive.google.com/uc?export=download&id={file_id}"
    output_path = "database.db"

    response = requests.get(url)
    if response.status_code == 200:
        with open(output_path, "wb") as f:
            f.write(response.content)
        print("✅ database.db завантажено")
    else:
        print("❌ Помилка завантаження:", response.status_code)

if __name__ == "__main__":
    download_database()
