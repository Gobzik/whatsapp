import sys
import time
import random
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                             QLabel, QLineEdit, QPushButton, QSpinBox, QTextEdit)
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from messages import MESSAGES


class WhatsAppBotGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("WhatsApp Bot")
        self.setGeometry(100, 100, 500, 600)

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)

        self.layout = QVBoxLayout()
        self.central_widget.setLayout(self.layout)

        self.init_ui()
        self.drivers = []
        self.accounts = []

    def init_ui(self):
        # Количество аккаунтов
        self.layout.addWidget(QLabel("Количество номеров (2-5):"))
        self.num_accounts = QSpinBox()
        self.num_accounts.setRange(2, 5)
        self.layout.addWidget(self.num_accounts)

        # Время работы
        self.layout.addWidget(QLabel("Время работы (минут):"))
        self.duration = QSpinBox()
        self.duration.setRange(1, 120)
        self.duration.setValue(10)
        self.layout.addWidget(self.duration)

        # Поля для номеров
        self.phone_inputs = []
        for i in range(5):
            phone_input = QLineEdit()
            phone_input.setPlaceholderText(f"Номер {i + 1} (79123456789)")
            phone_input.setVisible(False)
            self.phone_inputs.append(phone_input)
            self.layout.addWidget(phone_input)

        # Кнопка запуска
        self.start_btn = QPushButton("Запустить бота")
        self.start_btn.clicked.connect(self.start_bot)
        self.layout.addWidget(self.start_btn)

        # Лог
        self.log = QTextEdit()
        self.log.setReadOnly(True)
        self.layout.addWidget(self.log)

        # Обновляем видимость полей
        self.num_accounts.valueChanged.connect(self.update_inputs)

    def update_inputs(self):
        num = self.num_accounts.value()
        for i, input_field in enumerate(self.phone_inputs):
            input_field.setVisible(i < num)

    def log_message(self, message):
        self.log.append(f"[{time.strftime('%H:%M:%S')}] {message}")
        QApplication.processEvents()

    def login_to_whatsapp(self, driver, phone):
        driver.get("https://web.whatsapp.com/")
        self.log_message(f"{phone}: Отсканируйте QR-код...")

        try:
            WebDriverWait(driver, 60).until(
                EC.presence_of_element_located((By.XPATH, '//div[@aria-label="Список чатов"]'))
            )
            self.log_message(f"{phone}: Успешный вход!")
            return True
        except:
            self.log_message(f"{phone}: Не удалось войти!")
            return False

    def send_message(self, driver, contact_phone, message):
        try:
            search_box = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.XPATH, '//div[@contenteditable="true"][@data-tab="3"]'))
            )
            search_box.clear()
            search_box.send_keys(contact_phone)
            time.sleep(random.uniform(1, 3))
            search_box.send_keys(Keys.ENTER)

            message_box = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.XPATH, '//div[@contenteditable="true"][@data-tab="10"]'))
            )
            message_box.send_keys(message)
            message_box.send_keys(Keys.ENTER)
            self.log_message(f"Отправлено {contact_phone}: '{message}'")
            time.sleep(random.uniform(2, 5))
        except Exception as e:
            self.log_message(f"Ошибка: {str(e)}")

    def start_bot(self):
        self.accounts = []
        for i in range(self.num_accounts.value()):
            phone = self.phone_inputs[i].text().strip()
            if not phone:
                self.log_message(f"Ошибка: номер {i + 1} не введен!")
                return
            self.accounts.append({"phone": phone})

        self.drivers = []
        for account in self.accounts:
            try:
                driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))
                self.drivers.append(driver)
                if not self.login_to_whatsapp(driver, account["phone"]):
                    return
            except Exception as e:
                self.log_message(f"Ошибка запуска браузера: {str(e)}")
                return

        self.start_btn.setEnabled(False)
        self.log_message("\n=== Начало переписки ===")

        start_time = time.time()
        duration_sec = self.duration.value() * 60

        try:
            while time.time() - start_time < duration_sec:
                for account in self.accounts:
                    driver = self.drivers[self.accounts.index(account)]
                    other_accounts = [acc for acc in self.accounts if acc != account]
                    receiver = random.choice(other_accounts)

                    msg = random.choice(MESSAGES)
                    self.send_message(driver, receiver["phone"], msg)

                time.sleep(random.uniform(10, 30))

        except Exception as e:
            self.log_message(f"Ошибка: {str(e)}")
        finally:
            self.stop_bot()

    def stop_bot(self):
        self.log_message("\n=== Завершение работы ===")
        for driver in self.drivers:
            try:
                driver.quit()
            except:
                pass
        self.start_btn.setEnabled(True)
        self.log_message("Все браузеры закрыты")

    def closeEvent(self, event):
        self.stop_bot()
        event.accept()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = WhatsAppBotGUI()
    window.show()
    sys.exit(app.exec_())