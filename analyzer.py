"""
Аналізатор текстових файлів
Варіант Б-2 — навчальна практика
Консольна утиліта для аналізу .txt файлів.
"""

import os
import re
import json
import unittest
from datetime import datetime
from collections import Counter

HISTORY_FILE = "history.json"


# ---------------------- Робота зі сховищем (JSON) ----------------------

def load_history():
    """Завантажує історію аналізів з файлу. Якщо файл відсутній або пошкоджений — повертає порожній список."""
    if not os.path.exists(HISTORY_FILE):
        return []
    try:
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            if isinstance(data, list):
                return data
            return []
    except (json.JSONDecodeError, OSError):
        print("⚠ Файл історії пошкоджено або недоступний. Створено нову історію.")
        return []


def save_history(history):
    """Зберігає історію аналізів у файл."""
    try:
        with open(HISTORY_FILE, "w", encoding="utf-8") as f:
            json.dump(history, f, ensure_ascii=False, indent=2)
    except OSError as e:
        print(f"⚠ Не вдалося зберегти історію: {e}")


def add_history_record(action, filename, result_summary):
    history = load_history()
    history.append({
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "action": action,
        "file": filename,
        "summary": result_summary
    })
    save_history(history)


# ---------------------- Основна логіка аналізу ----------------------

WORD_PATTERN = re.compile(r"[A-Za-zА-Яа-яІіЇїЄєҐґ']+")
SENTENCE_PATTERN = re.compile(r"[.!?]+")


def read_text_file(path):
    """
    Безпечно зчитує текстовий файл.
    Повертає (текст, None) при успіху або (None, повідомлення_помилки) при невдачі.
    """
    if not path or not path.strip():
        return None, "Шлях до файлу не може бути порожнім."

    path = path.strip().strip('"').strip("'")

    if not os.path.exists(path):
        return None, f"Файл не знайдено: {path}"

    if not os.path.isfile(path):
        return None, f"Вказаний шлях не є файлом: {path}"

    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read(), None
    except UnicodeDecodeError:
        try:
            with open(path, "r", encoding="cp1251") as f:
                return f.read(), None
        except Exception:
            return None, "Не вдалося прочитати файл (невідоме кодування)."
    except OSError as e:
        return None, f"Помилка читання файлу: {e}"


def count_words(text):
    return WORD_PATTERN.findall(text.lower())


def count_sentences(text):
    parts = SENTENCE_PATTERN.split(text)
    return len([p for p in parts if p.strip()])


def get_stats(text):
    words = count_words(text)
    return {
        "characters": len(text),
        "characters_no_spaces": len(text.replace(" ", "").replace("\n", "")),
        "words": len(words),
        "sentences": count_sentences(text),
    }


def top_n_words(text, n):
    words = count_words(text)
    counter = Counter(words)
    return counter.most_common(n)


def search_pattern(text, pattern, use_regex=False):
    """Шукає всі входження патерну. Повертає список (номер_рядка, рядок)."""
    matches = []
    lines = text.splitlines()

    if use_regex:
        try:
            compiled = re.compile(pattern, re.IGNORECASE)
        except re.error as e:
            return None, f"Некоректний регулярний вираз: {e}"
        for i, line in enumerate(lines, start=1):
            if compiled.search(line):
                matches.append((i, line))
    else:
        pattern_lower = pattern.lower()
        for i, line in enumerate(lines, start=1):
            if pattern_lower in line.lower():
                matches.append((i, line))

    return matches, None


def compare_files(text1, text2):
    s1, s2 = get_stats(text1), get_stats(text2)
    diff = {key: s2[key] - s1[key] for key in s1}
    return s1, s2, diff


# ---------------------- Допоміжні функції вводу ----------------------

def input_int(prompt, default=None, min_value=None):
    """Безпечне зчитування цілого числа. Підтримує значення за замовчуванням."""
    while True:
        raw = input(prompt).strip()
        if raw == "" and default is not None:
            return default
        try:
            value = int(raw)
            if min_value is not None and value < min_value:
                print(f"Число має бути не менше {min_value}. Спробуйте ще раз.")
                continue
            return value
        except ValueError:
            print("Некоректне число. Спробуйте ще раз (наприклад: 5).")


def input_nonempty(prompt):
    while True:
        value = input(prompt).strip()
        if value:
            return value
        print("Поле не може бути порожнім. Спробуйте ще раз.")


# ---------------------- Пункти меню ----------------------

def action_basic_stats():
    print("\n--- Базова статистика файлу ---")
    path = input_nonempty("Шлях до .txt файлу: ")
    text, error = read_text_file(path)
    if error:
        print(f"Помилка: {error}")
        return

    if not text.strip():
        print("⚠ Файл порожній — статистика буде нульовою.")

    stats = get_stats(text)
    print(f"\nФайл: {path}")
    print(f"Символів (всього):       {stats['characters']}")
    print(f"Символів (без пробілів):  {stats['characters_no_spaces']}")
    print(f"Слів:                     {stats['words']}")
    print(f"Речень:                   {stats['sentences']}")

    add_history_record("Базова статистика", path, stats)


def action_top_words():
    print("\n--- Топ-N найчастіших слів ---")
    path = input_nonempty("Шлях до .txt файлу: ")
    text, error = read_text_file(path)
    if error:
        print(f"Помилка: {error}")
        return

    n = input_int("Скільки слів показати (за замовчуванням 10): ", default=10, min_value=1)

    top = top_n_words(text, n)
    if not top:
        print("У файлі не знайдено слів.")
        return

    print(f"\nТоп-{n} слів у файлі '{path}':")
    for i, (word, count) in enumerate(top, start=1):
        print(f"{i}. {word} — {count}")

    add_history_record("Топ слів", path, dict(top))


def action_search():
    print("\n--- Пошук патерну у файлі ---")
    path = input_nonempty("Шлях до .txt файлу: ")
    text, error = read_text_file(path)
    if error:
        print(f"Помилка: {error}")
        return

    pattern = input_nonempty("Введіть текст або регулярний вираз для пошуку: ")
    regex_choice = input("Використати як регулярний вираз? (y/N): ").strip().lower()
    use_regex = regex_choice == "y"

    matches, error = search_pattern(text, pattern, use_regex)
    if error:
        print(f"Помилка: {error}")
        return

    if not matches:
        print("Збігів не знайдено.")
    else:
        print(f"\nЗнайдено {len(matches)} збіг(ів):")
        for line_num, line in matches:
            print(f"  Рядок {line_num}: {line.strip()}")

    add_history_record("Пошук патерну", path, {"pattern": pattern, "matches_count": len(matches)})


def action_compare_files():
    print("\n--- Порівняння двох файлів за статистикою ---")
    path1 = input_nonempty("Шлях до першого .txt файлу: ")
    text1, error1 = read_text_file(path1)
    if error1:
        print(f"Помилка (файл 1): {error1}")
        return

    path2 = input_nonempty("Шлях до другого .txt файлу: ")
    text2, error2 = read_text_file(path2)
    if error2:
        print(f"Помилка (файл 2): {error2}")
        return

    s1, s2, diff = compare_files(text1, text2)

    print(f"\n{'Показник':<25}{'Файл 1':<12}{'Файл 2':<12}{'Різниця':<10}")
    print("-" * 59)
    labels = {
        "characters": "Символів",
        "characters_no_spaces": "Символів (без проб.)",
        "words": "Слів",
        "sentences": "Речень",
    }
    for key, label in labels.items():
        sign = "+" if diff[key] >= 0 else ""
        print(f"{label:<25}{s1[key]:<12}{s2[key]:<12}{sign}{diff[key]:<10}")

    add_history_record("Порівняння файлів", f"{path1} vs {path2}", {"file1": s1, "file2": s2, "diff": diff})


def action_view_history():
    print("\n--- Історія аналізів ---")
    history = load_history()
    if not history:
        print("Історія порожня.")
        return

    for i, record in enumerate(history, start=1):
        print(f"\n{i}. [{record['timestamp']}] {record['action']}")
        print(f"   Файл: {record['file']}")
        print(f"   Результат: {record['summary']}")


def action_clear_history():
    confirm = input("Ви впевнені, що хочете очистити історію? (y/N): ").strip().lower()
    if confirm == "y":
        save_history([])
        print("Історію очищено.")
    else:
        print("Скасовано.")


# ---------------------- Автоматизовані тести (бонус) ----------------------

class AnalyzerTests(unittest.TestCase):
    """Базові автотести основних функцій аналізатора."""

    def test_count_words(self):
        text = "Привіт, світ! Це тест."
        words = count_words(text)
        self.assertEqual(words, ["привіт", "світ", "це", "тест"])

    def test_count_sentences(self):
        text = "Перше речення. Друге речення! Третє?"
        self.assertEqual(count_sentences(text), 3)

    def test_get_stats(self):
        text = "Один два три."
        stats = get_stats(text)
        self.assertEqual(stats["words"], 3)
        self.assertEqual(stats["sentences"], 1)

    def test_top_n_words(self):
        text = "кіт кіт пес кіт пес птах"
        top = top_n_words(text, 2)
        self.assertEqual(top[0], ("кіт", 3))
        self.assertEqual(top[1], ("пес", 2))

    def test_search_pattern_plain(self):
        text = "перший рядок\nдругий рядок з котом\nтретій рядок"
        matches, error = search_pattern(text, "кот", use_regex=False)
        self.assertIsNone(error)
        self.assertEqual(len(matches), 1)
        self.assertEqual(matches[0][0], 2)

    def test_search_pattern_regex_invalid(self):
        matches, error = search_pattern("текст", "[", use_regex=True)
        self.assertIsNone(matches)
        self.assertIsNotNone(error)

    def test_compare_files(self):
        s1, s2, diff = compare_files("один два", "один два три")
        self.assertEqual(diff["words"], 1)

    def test_read_nonexistent_file(self):
        text, error = read_text_file("файл_якого_не_існує_12345.txt")
        self.assertIsNone(text)
        self.assertIsNotNone(error)

    def test_read_empty_path(self):
        text, error = read_text_file("")
        self.assertIsNone(text)
        self.assertIsNotNone(error)


def run_self_tests():
    print("\n--- Запуск автоматизованих тестів ---\n")
    suite = unittest.TestLoader().loadTestsFromTestCase(AnalyzerTests)
    runner = unittest.TextTestRunner(verbosity=2)
    runner.run(suite)


# ---------------------- Головне меню ----------------------

MENU = """
========== Аналізатор текстових файлів ==========
1. Базова статистика файлу (символи / слова / речення)
2. Топ-N найчастіших слів
3. Пошук патерну у файлі
4. Порівняти два файли за статистикою
5. Переглянути історію аналізів
6. Очистити історію
7. Запустити автоматизовані тести
0. Вихід
===================================================
"""


def main():
    actions = {
        "1": action_basic_stats,
        "2": action_top_words,
        "3": action_search,
        "4": action_compare_files,
        "5": action_view_history,
        "6": action_clear_history,
        "7": run_self_tests,
    }

    while True:
        print(MENU)
        choice = input("Оберіть пункт меню: ").strip()

        if choice == "0":
            print("До побачення!")
            break

        action = actions.get(choice)
        if action:
            try:
                action()
            except Exception as e:
                # Захист від будь-яких неочікуваних помилок — програма не повинна "падати"
                print(f"⚠ Сталася непередбачена помилка: {e}")
        else:
            print("Некоректний пункт меню. Введіть число від 0 до 7.")


if __name__ == "__main__":
    main()