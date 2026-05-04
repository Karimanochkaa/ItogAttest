import json
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
import os

DATA_FILE = "trainings.json"


class TrainingPlanner:
    def __init__(self, root):
        self.root = root
        self.root.title("Training Planner")
        self.root.geometry("750x450")
        self.root.resizable(False, False)

        self.trainings = []          # список словарей с тренировками
        self.load_from_file()

        # ========== ФОРМА ВВОДА ==========
        input_frame = ttk.LabelFrame(root, text="Новая тренировка", padding=10)
        input_frame.pack(fill="x", padx=10, pady=5)

        # Дата
        ttk.Label(input_frame, text="Дата (ГГГГ-ММ-ДД):").grid(row=0, column=0, sticky="w", padx=5, pady=5)
        self.date_entry = ttk.Entry(input_frame, width=20)
        self.date_entry.grid(row=0, column=1, padx=5, pady=5)

        # Тип тренировки (выпадающий список)
        ttk.Label(input_frame, text="Тип тренировки:").grid(row=1, column=0, sticky="w", padx=5, pady=5)
        self.type_var = tk.StringVar()
        self.type_combo = ttk.Combobox(input_frame, textvariable=self.type_var,
                                       values=["Бег", "Велосипед", "Плавание", "Силовая", "Йога"],
                                       width=17, state="readonly")
        self.type_combo.grid(row=1, column=1, padx=5, pady=5)
        self.type_combo.current(0)

        # Длительность
        ttk.Label(input_frame, text="Длительность (мин):").grid(row=2, column=0, sticky="w", padx=5, pady=5)
        self.duration_entry = ttk.Entry(input_frame, width=20)
        self.duration_entry.grid(row=2, column=1, padx=5, pady=5)

        # Кнопка добавления
        add_btn = ttk.Button(input_frame, text="➕ Добавить тренировку", command=self.add_training)
        add_btn.grid(row=3, column=0, columnspan=2, pady=10)

        # ========== ФИЛЬТРЫ ==========
        filter_frame = ttk.LabelFrame(root, text="Фильтрация", padding=10)
        filter_frame.pack(fill="x", padx=10, pady=5)

        ttk.Label(filter_frame, text="Фильтр по типу:").grid(row=0, column=0, sticky="w", padx=5)
        self.filter_type_var = tk.StringVar(value="Все")
        filter_type_combo = ttk.Combobox(filter_frame, textvariable=self.filter_type_var,
                                         values=["Все", "Бег", "Велосипед", "Плавание", "Силовая", "Йога"],
                                         width=15, state="readonly")
        filter_type_combo.grid(row=0, column=1, padx=5)

        ttk.Label(filter_frame, text="Фильтр по дате (ГГГГ-ММ-ДД):").grid(row=0, column=2, sticky="w", padx=5)
        self.filter_date_entry = ttk.Entry(filter_frame, width=15)
        self.filter_date_entry.grid(row=0, column=3, padx=5)

        apply_filter_btn = ttk.Button(filter_frame, text="🔍 Применить фильтр", command=self.display_trainings)
        apply_filter_btn.grid(row=0, column=4, padx=10)

        reset_filter_btn = ttk.Button(filter_frame, text="❌ Сбросить фильтр", command=self.reset_filters)
        reset_filter_btn.grid(row=0, column=5, padx=5)

        # ========== ТАБЛИЦА ==========
        columns = ("ID", "Дата", "Тип", "Длительность (мин)")
        self.tree = ttk.Treeview(root, columns=columns, show="headings", height=12)
        for col in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=150 if col != "Длительность (мин)" else 120)
        self.tree.pack(fill="both", expand=True, padx=10, pady=5)

        # Кнопка сохранения вручную
        save_btn = ttk.Button(root, text="💾 Сохранить в JSON", command=self.save_to_file)
        save_btn.pack(pady=5)

        # Первоначальное отображение
        self.display_trainings()

    # ------------------- Валидация -------------------
    def validate_date(self, date_str):
        """Проверяет формат ГГГГ-ММ-ДД и существование даты"""
        try:
            datetime.strptime(date_str, "%Y-%m-%d")
            return True
        except ValueError:
            return False

    def validate_duration(self, duration_str):
        """Проверяет, что длительность — положительное число"""
        try:
            value = float(duration_str)
            return value > 0
        except ValueError:
            return False

    # ------------------- Добавление -------------------
    def add_training(self):
        date = self.date_entry.get().strip()
        t_type = self.type_var.get()
        duration = self.duration_entry.get().strip()

        # Валидация
        if not date:
            messagebox.showerror("Ошибка", "Дата не может быть пустой")
            return
        if not self.validate_date(date):
            messagebox.showerror("Ошибка", "Неверный формат даты. Используйте ГГГГ-ММ-ДД (например, 2025-12-31)")
            return
        if not duration:
            messagebox.showerror("Ошибка", "Длительность не может быть пустой")
            return
        if not self.validate_duration(duration):
            messagebox.showerror("Ошибка", "Длительность должна быть положительным числом (например, 30 или 45.5)")
            return

        # Генерация ID
        new_id = max([t["id"] for t in self.trainings], default=0) + 1

        training = {
            "id": new_id,
            "date": date,
            "type": t_type,
            "duration": float(duration)
        }
        self.trainings.append(training)
        self.clear_inputs()
        self.display_trainings()
        self.save_to_file()   # автосохранение

    def clear_inputs(self):
        self.date_entry.delete(0, tk.END)
        self.duration_entry.delete(0, tk.END)
        self.type_combo.current(0)   # сброс на первый тип

    # ------------------- Фильтрация и отображение -------------------
    def reset_filters(self):
        self.filter_type_var.set("Все")
        self.filter_date_entry.delete(0, tk.END)
        self.display_trainings()

    def display_trainings(self):
        # Очистить таблицу
        for row in self.tree.get_children():
            self.tree.delete(row)

        filter_type = self.filter_type_var.get()
        filter_date = self.filter_date_entry.get().strip()

        filtered = self.trainings[:]
        if filter_type != "Все":
            filtered = [t for t in filtered if t["type"] == filter_type]
        if filter_date:
            filtered = [t for t in filtered if t["date"] == filter_date]

        for t in filtered:
            self.tree.insert("", tk.END, values=(t["id"], t["date"], t["type"], t["duration"]))

    # ------------------- Работа с JSON -------------------
    def save_to_file(self):
        try:
            with open(DATA_FILE, "w", encoding="utf-8") as f:
                json.dump(self.trainings, f, indent=4, ensure_ascii=False)
        except Exception as e:
            messagebox.showerror("Ошибка сохранения", f"Не удалось сохранить: {e}")

    def load_from_file(self):
        if not os.path.exists(DATA_FILE):
            self.trainings = []
            return
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                self.trainings = json.load(f)
        except (json.JSONDecodeError, Exception) as e:
            messagebox.showerror("Ошибка загрузки", f"Файл повреждён: {e}")
            self.trainings = []


if __name__ == "__main__":
    root = tk.Tk()
    app = TrainingPlanner(root)
    root.mainloop()
