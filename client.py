import sys
import json
import random
import re
import os
import shutil
from datetime import datetime
from PyQt5.QtWidgets import (
    QApplication, QWidget, QLabel, QLineEdit, QPushButton,
    QVBoxLayout, QHBoxLayout, QMessageBox, QListWidget, QListWidgetItem,
    QTextEdit, QFileDialog, QSizePolicy
)
from PyQt5.QtCore import Qt, QTimer, QSize
from PyQt5.QtGui import QColor, QIcon, QPixmap
from flask import Flask

USERS_DB = "users.json"

def load_users():
    try:
        with open(USERS_DB, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}

def save_users(users):
    try:
        with open(USERS_DB, "w", encoding="utf-8") as f:
            json.dump(users, f, ensure_ascii=False, indent=4)
    except Exception as e:
        print(f"Ошибка при сохранении users.json: {e}")

def generate_nick(name):
    digits = f"{random.randint(0,9999):04}"
    return f"{name}#{digits}"

def get_chat_key(nick1, nick2):
    return "|".join(sorted([nick1, nick2]))

class FriendListItem(QWidget):
    def __init__(self, nick):
        super().__init__()
        self.nick = nick
        self.init_ui()

    def init_ui(self):
        layout = QHBoxLayout()
        layout.setContentsMargins(5, 2, 5, 2)

        avatar = QLabel()
        pixmap = QPixmap(40, 40)
        pixmap.fill(QColor("#5865F2"))
        avatar.setPixmap(pixmap)
        avatar.setFixedSize(40, 40)
        avatar.setStyleSheet("border-radius:20px;")
        layout.addWidget(avatar)

        nick_label = QLabel(self.nick)
        nick_label.setStyleSheet("color: white; font-weight: 600; font-size: 14px;")
        layout.addWidget(nick_label)

        layout.addStretch()
        self.setLayout(layout)

class ChatMessageItem(QLabel):
    def __init__(self, text, is_sender):
        super().__init__()
        self.is_sender = is_sender
        self.setWordWrap(True)
        self.setTextFormat(Qt.RichText)
        self.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self.setStyleSheet(self.get_style())
        self.setText(text)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)

    def get_style(self):
        if self.is_sender:
            return """
                background-color: #5865F2;
                color: white;
                padding: 8px 12px;
                border-radius: 15px 15px 0 15px;
                max-width: 60%;
                margin-left: auto;
                font-size: 14px;
            """
        else:
            return """
                background-color: #40444b;
                color: white;
                padding: 8px 12px;
                border-radius: 15px 15px 15px 0;
                max-width: 60%;
                margin-right: auto;
                font-size: 14px;
            """

class LoginRegisterWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Регистрация / Вход")
        self.resize(360, 260)

        self.users = load_users()

        self.email_label = QLabel("Почта:")
        self.email_input = QLineEdit()
        self.pass_label = QLabel("Пароль:")
        self.pass_input = QLineEdit()
        self.pass_input.setEchoMode(QLineEdit.Password)
        self.nick_label = QLabel("Имя (для регистрации):")
        self.nick_input = QLineEdit()

        self.register_btn = QPushButton("Зарегистрироваться")
        self.login_btn = QPushButton("Войти")

        layout = QVBoxLayout()
        layout.addWidget(self.email_label)
        layout.addWidget(self.email_input)
        layout.addWidget(self.pass_label)
        layout.addWidget(self.pass_input)
        layout.addWidget(self.nick_label)
        layout.addWidget(self.nick_input)

        btn_layout = QHBoxLayout()
        btn_layout.addWidget(self.register_btn)
        btn_layout.addWidget(self.login_btn)

        layout.addLayout(btn_layout)
        self.setLayout(layout)

        self.register_btn.clicked.connect(self.register)
        self.login_btn.clicked.connect(self.login)

        self.setStyleSheet("""
            QLabel {
                font-weight: 600;
                font-size: 15px;
                color: #eceff1;
            }
            QLineEdit {
                background-color: #2a2d43;
                border: 1.5px solid #3f51b5;
                border-radius: 10px;
                padding: 10px 14px;
                color: #eceff1;
                font-size: 15px;
            }
            QLineEdit:focus {
                border-color: #7986cb;
                background-color: #353a58;
            }
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                                            stop:0 #3f51b5, stop:1 #5c6bc0);
                border-radius: 12px;
                padding: 10px 20px;
                color: white;
                font-weight: 700;
                font-size: 15px;
                box-shadow: 0 4px 10px rgba(63,81,181,0.3);
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                                            stop:0 #5c6bc0, stop:1 #7986cb);
                box-shadow: 0 6px 14px rgba(63,81,181,0.5);
            }
            QPushButton:pressed {
                background: #3949ab;
                box-shadow: none;
            }
            QWidget {
                background-color: #1e1e2f;
            }
        """)

    def register(self):
        email = self.email_input.text().strip()
        password = self.pass_input.text()
        name = self.nick_input.text().strip()

        if not email or not password or not name:
            QMessageBox.warning(self, "Ошибка", "Все поля должны быть заполнены")
            return

        if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
            QMessageBox.warning(self, "Ошибка", "Неверный формат почты")
            return

        if email in self.users:
            QMessageBox.warning(self, "Ошибка", "Пользователь с такой почтой уже существует")
            return

        nick = generate_nick(name)
        self.users[email] = {"password": password, "nick": nick, "friends": [], "messages": {}}
        save_users(self.users)

        QMessageBox.information(self, "Успех", f"Зарегистрировано! Ваш ник: {nick}")
        self.nick_input.clear()

    def login(self):
        email = self.email_input.text().strip()
        password = self.pass_input.text()

        user = self.users.get(email)
        if not user or user["password"] != password:
            QMessageBox.warning(self, "Ошибка", "Неверная почта или пароль")
            return

        self.chat_window = ChatWindow(user, self.users, email)
        self.chat_window.show()
        self.close()

class ChatWindow(QWidget):
    def __init__(self, user, users_db, user_email):
        super().__init__()
        self.setWindowTitle(f"Fpiersk - {user['nick']}")
        self.resize(900, 650)

        self.user = user
        self.users_db = users_db
        self.user_email = user_email

        self.friends_list = QListWidget()
        self.friends_list.setStyleSheet("""
            QListWidget {
                background-color: #2a2d43;
                border-radius: 12px;
                padding: 8px;
                color: #cfd8dc;
                font-size: 15px;
                outline: none;
            }
            QListWidget::item {
                padding: 12px 10px;
                border-radius: 10px;
                margin-bottom: 6px;
                color: #cfd8dc;
                font-weight: 600;
                transition: background-color 0.25s ease;
            }
            QListWidget::item:selected {
                background-color: #3f51b5;
                color: white;
                font-weight: 700;
                box-shadow: 0 4px 8px rgba(63,81,181,0.6);
            }
        """)
        self.friends_list.setIconSize(QSize(40, 40))

        self.add_friend_input = QLineEdit()
        self.add_friend_input.setPlaceholderText("Введите ник друга (например, User#1234)")
        self.add_friend_input.setStyleSheet("""
            QLineEdit {
                background-color: #2a2d43;
                border: 1.5px solid #3f51b5;
                border-radius: 10px;
                padding: 10px 14px;
                color: #eceff1;
                font-size: 15px;
            }
            QLineEdit:focus {
                border-color: #7986cb;
                background-color: #353a58;
            }
        """)

        self.add_friend_btn = QPushButton("Добавить в друзья")
        self.add_friend_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                                            stop:0 #3f51b5, stop:1 #5c6bc0);
                border-radius: 12px;
                padding: 10px 20px;
                color: white;
                font-weight: 700;
                font-size: 15px;
                box-shadow: 0 4px 10px rgba(63,81,181,0.3);
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                                            stop:0 #5c6bc0, stop:1 #7986cb);
                box-shadow: 0 6px 14px rgba(63,81,181,0.5);
            }
            QPushButton:pressed {
                background: #3949ab;
                box-shadow: none;
            }
        """)

        left_layout = QVBoxLayout()
        left_layout.addWidget(QLabel("Друзья:"))
        left_layout.addWidget(self.friends_list)
        left_layout.addWidget(self.add_friend_input)
        left_layout.addWidget(self.add_friend_btn)

        self.chat_header = QLabel("Выберите друга для начала общения")
        self.chat_header.setObjectName("chat_header")
        self.chat_header.setStyleSheet("""
            QLabel#chat_header {
                font-size: 22px;
                font-weight: 700;
                color: #e0e0e0;
                padding-bottom: 15px;
                border-bottom: 2px solid #3f51b5;
            }
        """)

        self.chat_display = QTextEdit()
        self.chat_display.setReadOnly(True)
        self.chat_display.setStyleSheet("""
            QTextEdit {
                background-color: #2a2d43;
                border-radius: 12px;
                padding: 14px;
                font-size: 15px;
                color: #eceff1;
                border: 1.5px solid #3f51b5;
                outline: none;
            }
            QTextEdit:focus {
                border-color: #7986cb;
                background-color: #353a58;
            }
        """)

        self.message_input = QLineEdit()
        self.message_input.setPlaceholderText("Введите сообщение и нажмите Enter")
        self.message_input.setStyleSheet("""
            QLineEdit {
                background-color: #2a2d43;
                border: 1.5px solid #3f51b5;
                border-radius: 10px;
                padding: 10px 14px;
                font-size: 15px;
                color: #eceff1;
            }
            QLineEdit:focus {
                border-color: #7986cb;
                background-color: #353a58;
            }
        """)

        self.attach_btn = QPushButton("📎")
        self.attach_btn.setFixedWidth(40)
        self.attach_btn.setToolTip("Прикрепить изображение")
        self.attach_btn.setObjectName("attach_btn")
        self.attach_btn.setStyleSheet("""
            QPushButton#attach_btn {
                background: transparent;
                font-size: 22px;
                color: #7986cb;
                border: none;
                padding: 0 10px;
            }
            QPushButton#attach_btn:hover {
                color: #c5cae9;
            }
        """)

        input_layout = QHBoxLayout()
        input_layout.addWidget(self.message_input)
        input_layout.addWidget(self.attach_btn)

        right_layout = QVBoxLayout()
        right_layout.addWidget(self.chat_header)
        right_layout.addWidget(self.chat_display)
        right_layout.addLayout(input_layout)

        main_layout = QHBoxLayout()
        main_layout.addLayout(left_layout, 3)
        main_layout.addLayout(right_layout, 7)

        self.setLayout(main_layout)

        self.add_friend_btn.clicked.connect(self.add_friend)
        self.friends_list.itemSelectionChanged.connect(self.friend_selected)
        self.message_input.returnPressed.connect(self.send_message)
        self.attach_btn.clicked.connect(self.attach_image)

        self.current_friend = None

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.auto_update_chat)
        self.timer.start(1000)

        self.update_friends_list()

    def update_friends_list(self):
        self.friends_list.clear()
        friends = self.user.get("friends", [])
        for nick in sorted(friends):
            item = QListWidgetItem(nick)
            font = item.font()
            font.setPointSize(18)  # Сделать ник крупнее
            font.setBold(True)
            item.setFont(font)
            self.friends_list.addItem(item)

    def add_friend(self):
        try:
            nick = self.add_friend_input.text().strip()
            if not nick:
                return
            if not any(u.get("nick") == nick for u in self.users_db.values()):
                QMessageBox.warning(self, "Ошибка", "Пользователь с таким ником не найден")
                return
            if nick == self.user["nick"]:
                QMessageBox.warning(self, "Ошибка", "Нельзя добавить себя")
                return
            if nick in self.user.get("friends", []):
                QMessageBox.information(self, "Инфо", "Пользователь уже в друзьях")
                return

            self.user.setdefault("friends", []).append(nick)

            friend_email = None
            for email, u in self.users_db.items():
                if u.get("nick") == nick:
                    friend_email = email
                    break

            if friend_email is None:
                QMessageBox.warning(self, "Ошибка", "Не удалось найти email друга")
                return

            friend_data = self.users_db[friend_email]
            friend_data.setdefault("friends", [])
            if self.user["nick"] not in friend_data["friends"]:
                friend_data["friends"].append(self.user["nick"])
            self.users_db[friend_email] = friend_data

            self.users_db[self.user_email] = self.user
            save_users(self.users_db)
            self.update_friends_list()
            self.add_friend_input.clear()
            QMessageBox.information(self, "Успех", f"Пользователь {nick} добавлен в друзья (взаимно)")

        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Произошла ошибка при добавлении друга:\n{e}")
            import traceback
            traceback.print_exc()

    def friend_selected(self):
        selected = self.friends_list.selectedItems()
        if selected:
            nick = selected[0].text()
            self.current_friend = nick
            self.chat_header.setText(f"Чат с {self.current_friend}")
            self.load_chat_history()
        else:
            self.current_friend = None
            self.chat_header.setText("Выберите друга для начала общения")
            self.chat_display.clear()

    def load_chat_history(self):
        scrollbar = self.chat_display.verticalScrollBar()
        # Сохраняем текущую позицию скролла
        scroll_pos = scrollbar.value()

        self.chat_display.clear()
        key = get_chat_key(self.user["nick"], self.current_friend)
        messages = self.user.get("messages")
        if messages is None:
            self.user["messages"] = {}
            messages = self.user["messages"]
        chat_history = messages.get(key, [])
        for msg in chat_history:
            time = msg.get("timestamp", "")
            sender = msg.get("sender", "")
            msg_type = msg.get("type", "text")
            align = "right" if sender == self.user["nick"] else "left"
            color = "#7289da" if sender == self.user["nick"] else "#43b581"
            bubble = "#23272a"

            if msg_type == "text":
                text = msg.get("text", "")
                html = f"""
                <div style="text-align:{align}; margin-bottom: 18px;">
                    <span style="font-weight:bold; color:{color}; font-size:14px;">{sender}</span>
                    <span style="color:#b9bbbe; font-size:11px; margin-left:10px;">{time}</span><br>
                    <span style="background-color:{bubble}; color:#e0e0e0; padding:10px 16px; border-radius:12px; display:inline-block; margin-top:4px; max-width:60%; word-wrap: break-word;">{text}</span>
                </div>
                """
                self.chat_display.append(html)

            elif msg_type == "image":
                file_path = msg.get("file", "")
                if os.path.exists(file_path):
                    html = f"""
                    <div style="text-align:{align}; margin-bottom: 18px;">
                        <span style="font-weight:bold; color:{color}; font-size:14px;">{sender}</span>
                        <span style="color:#b9bbbe; font-size:11px; margin-left:10px;">{time}</span><br>
                        <img src="{file_path}" style="max-width: 300px; max-height: 300px; border-radius: 12px; margin-top: 4px;" />
                    </div>
                    """
                    self.chat_display.append(html)
                else:
                    html = f"""
                    <div style="text-align:{align}; margin-bottom: 18px;">
                        <span style="font-weight:bold; color:{color}; font-size:14px;">{sender}</span>
                        <span style="color:#b9bbbe; font-size:11px; margin-left:10px;">{time}</span><br>
                        <span style="background-color:#ff5555; color:#fff; padding:10px 16px; border-radius:12px; display:inline-block; margin-top:4px;">[Изображение не найдено]</span>
                    </div>
                    """
                    self.chat_display.append(html)

        # Восстанавливаем позицию скролла
        scrollbar.setValue(scroll_pos)

    def send_message(self):
        if not self.current_friend:
            QMessageBox.warning(self, "Ошибка", "Выберите друга для отправки сообщения")
            return
        message = self.message_input.text().strip()
        if not message:
            return

        try:
            key = get_chat_key(self.user["nick"], self.current_friend)
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            self.user.setdefault("messages", {})
            self.user["messages"].setdefault(key, []).append({
                "sender": self.user["nick"],
                "type": "text",
                "text": message,
                "timestamp": timestamp
            })

            friend_email = None
            for email, u in self.users_db.items():
                if u.get("nick") == self.current_friend:
                    friend_email = email
                    break

            if friend_email:
                friend_data = self.users_db[friend_email]
                friend_data.setdefault("messages", {})
                friend_data["messages"].setdefault(key, []).append({
                    "sender": self.user["nick"],
                    "type": "text",
                    "text": message,
                    "timestamp": timestamp
                })
                self.users_db[friend_email] = friend_data

            self.users_db[self.user_email] = self.user
            save_users(self.users_db)

            formatted_text = f"{message} <br><span style='font-size:10px; color:#b9bbbe;'>{timestamp}</span>"
            self.chat_display.append(f"<div style='text-align:right; background-color:#5865F2; color:white; padding:8px 12px; border-radius:15px 15px 0 15px; max-width:60%; margin-left:auto; font-size:14px;'>{formatted_text}</div>")
            self.message_input.clear()
            # Автопрокрутка отключена

        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Произошла ошибка при отправке сообщения:\n{e}")
            import traceback
            traceback.print_exc()

    def attach_image(self):
        if not self.current_friend:
            QMessageBox.warning(self, "Ошибка", "Выберите друга для отправки изображения")
            return
        options = QFileDialog.Options()
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Выберите изображение", "",
            "Изображения (*.png *.jpg *.jpeg *.gif *.bmp);;Все файлы (*)", options=options
        )
        if file_path:
            try:
                images_dir = "images"
                if not os.path.exists(images_dir):
                    os.makedirs(images_dir)

                filename = os.path.basename(file_path)
                base, ext = os.path.splitext(filename)
                timestamp_str = datetime.now().strftime("%Y%m%d%H%M%S%f")
                new_filename = f"{base}_{timestamp_str}{ext}"
                dest_path = os.path.join(images_dir, new_filename)

                # --- МАСШТАБИРОВАНИЕ ---
                pixmap = QPixmap(file_path)
                if pixmap.isNull():
                    QMessageBox.warning(self, "Ошибка", "Не удалось загрузить изображение")
                    return

                # Уменьшаем в 3-4 раза (0.25 или 0.33)
                scale_factor = 0.50  # 0.25 = в 4 раза, 0.33 = в 3 раза
                new_width = int(pixmap.width() * scale_factor)
                new_height = int(pixmap.height() * scale_factor)
                scaled_pixmap = pixmap.scaled(new_width, new_height, Qt.KeepAspectRatio, Qt.SmoothTransformation)

                # Сохраняем уменьшенное изображение
                scaled_pixmap.save(dest_path)

                # --- СОХРАНЕНИЕ В ИСТОРИЮ ---
                key = get_chat_key(self.user["nick"], self.current_friend)
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

                self.user.setdefault("messages", {})
                self.user["messages"].setdefault(key, []).append({
                    "sender": self.user["nick"],
                    "type": "image",
                    "file": dest_path,
                    "timestamp": timestamp
                })

                friend_email = None
                for email, u in self.users_db.items():
                    if u.get("nick") == self.current_friend:
                        friend_email = email
                        break

                if friend_email:
                    friend_data = self.users_db[friend_email]
                    friend_data.setdefault("messages", {})
                    friend_data["messages"].setdefault(key, []).append({
                        "sender": self.user["nick"],
                        "type": "image",
                        "file": dest_path,
                        "timestamp": timestamp
                    })
                    self.users_db[friend_email] = friend_data

                self.users_db[self.user_email] = self.user
                save_users(self.users_db)

                self.load_chat_history()

            except Exception as e:
                QMessageBox.critical(self, "Ошибка", f"Ошибка при отправке изображения:\n{e}")
                import traceback
                traceback.print_exc()

    def auto_update_chat(self):
        updated_users = load_users()
        updated_user = updated_users.get(self.user_email)
        if not updated_user:
            return
        self.user = updated_user
        self.users_db = updated_users
        if self.current_friend:
            self.load_chat_history()

if __name__ == "__main__":
    port = 8080
    app.run(debug=True,host='0.0.0.0',port=port)
    app = QApplication(sys.argv)
    app.setStyleSheet("""
        QWidget {
            background-color: #1e1e2f;
            color: #cfd8dc;
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            font-size: 14px;
        }
        QLabel {
            color: #eceff1;
            font-weight: 600;
        }
        QLineEdit {
            background-color: #2a2d43;
            border: 1.5px solid #3f51b5;
            border-radius: 10px;
            padding: 10px 14px;
            color: #eceff1;
            font-size: 15px;
            selection-background-color: #7986cb;
        }
        QLineEdit:focus {
            border-color: #7986cb;
            background-color: #353a58;
        }
        QPushButton {
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                                        stop:0 #3f51b5, stop:1 #5c6bc0);
            border-radius: 12px;
            padding: 10px 20px;
            color: white;
            font-weight: 700;
            font-size: 15px;
            transition: background 0.3s ease;
            box-shadow: 0 4px 10px rgba(63,81,181,0.3);
        }
        QPushButton:hover {
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                                        stop:0 #5c6bc0, stop:1 #7986cb);
            box-shadow: 0 6px 14px rgba(63,81,181,0.5);
        }
        QPushButton:pressed {
            background: #3949ab;
            box-shadow: none;
        }
        QListWidget {
            background-color: #2a2d43;
            border-radius: 12px;
            padding: 8px;
            color: #cfd8dc;
            font-size: 15px;
            outline: none;
        }
        QListWidget::item {
            padding: 12px 10px;
            border-radius: 10px;
            margin-bottom: 6px;
            color: #cfd8dc;
            font-weight: 600;
            transition: background-color 0.25s ease;
        }
        QListWidget::item:selected {
            background-color: #3f51b5;
            color: white;
            font-weight: 700;
            box-shadow: 0 4px 8px rgba(63,81,181,0.6);
        }
        QTextEdit {
            background-color: #2a2d43;
            border-radius: 12px;
            padding: 14px;
            font-size: 15px;
            color: #eceff1;
            border: 1.5px solid #3f51b5;
            outline: none;
        }
        QTextEdit:focus {
            border-color: #7986cb;
            background-color: #353a58;
        }
        QScrollBar:vertical {
            background: transparent;
            width: 10px;
            margin: 15px 0 15px 0;
            border-radius: 5px;
        }
        QScrollBar::handle:vertical {
            background: #5c6bc0;
            min-height: 30px;
            border-radius: 5px;
        }
        QScrollBar::handle:vertical:hover {
            background: #7986cb;
        }
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
            height: 0;
        }
        QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
            background: none;
        }
        QLabel#chat_header {
            font-size: 22px;
            font-weight: 700;
            color: #e0e0e0;
            padding-bottom: 15px;
            border-bottom: 2px solid #3f51b5;
        }
        QPushButton#attach_btn {
            background: transparent;
            font-size: 22px;
            color: #7986cb;
            border: none;
            padding: 0 10px;
        }
        QPushButton#attach_btn:hover {
            color: #c5cae9;
        }
    """)
    window = LoginRegisterWindow()
    window.show()
    sys.exit(app.exec_())
