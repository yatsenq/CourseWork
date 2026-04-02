import tkinter as tk
import csv
import random
import os

# ── Кольорова схема ────────────────────────────────────────────────────────────
BG      = "#1e1e2e"
BG2     = "#2a2a3e"
BG3     = "#313145"
ACCENT  = "#7c3aed"
ACCENT2 = "#a78bfa"
SUCCESS = "#22c55e"
ERROR   = "#ef4444"
WARN    = "#f59e0b"
TEXT    = "#e2e8f0"
TEXT2   = "#94a3b8"
ENTRY   = "#3b3b52"
HOVER   = "#6d28d9"

# ── Завантаження слів ──────────────────────────────────────────────────────────
BASE_DIR   = os.path.dirname(os.path.abspath(__file__))
CSV_PATH   = os.path.join(BASE_DIR, "words.csv")
words_list = []

with open(CSV_PATH, newline="", encoding="utf-8-sig") as f:
    for row in csv.DictReader(f):
        words_list.append({"english": row["english"], "ukrainian": row["ukrainian"]})


def make_button(parent, text, bg, command):
    btn = tk.Button(
        parent, text=text, command=command,
        bg=bg, fg=TEXT, font=("Segoe UI", 11, "bold"),
        relief="flat", padx=16, pady=9,
        cursor="hand2", bd=0,
        activebackground=HOVER, activeforeground=TEXT,
    )
    btn.bind("<Enter>", lambda _: btn.config(bg=HOVER))
    btn.bind("<Leave>", lambda _: btn.config(bg=bg))
    return btn


class VocabApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Словник  EN ↔ UA")
        self.root.configure(bg=BG)
        self.root.resizable(False, False)

        # центрування
        w, h = 540, 660
        sw = root.winfo_screenwidth()
        sh = root.winfo_screenheight()
        root.geometry(f"{w}x{h}+{(sw - w)//2}+{(sh - h)//2}")

        self.current_word      = {}
        self.current_direction = "en2ua"
        self.score_correct     = 0
        self.score_total       = 0
        self.streak            = 0
        self.best_streak       = 0
        self._after_id         = None

        self._build_ui()
        self._bind_keys()
        self.new_word()

    # ── Побудова UI ────────────────────────────────────────────────────────────
    def _build_ui(self):
        # Заголовок
        hdr = tk.Frame(self.root, bg=ACCENT, pady=10)
        hdr.pack(fill="x")
        tk.Label(hdr, text="📖   Словник  EN ↔ UA",
                 bg=ACCENT, fg=TEXT, font=("Segoe UI", 18, "bold")).pack()

        # Статистика
        sf = tk.Frame(self.root, bg=BG2, pady=8)
        sf.pack(fill="x")

        self.lbl_score    = tk.Label(sf, text="✅ 0   ❌ 0",
                                     bg=BG2, fg=TEXT2, font=("Segoe UI", 10))
        self.lbl_score.pack(side="left", padx=18)

        self.lbl_streak   = tk.Label(sf, text="🔥 0",
                                     bg=BG2, fg=WARN, font=("Segoe UI", 10, "bold"))
        self.lbl_streak.pack(side="left", padx=8)

        self.lbl_accuracy = tk.Label(sf, text="🎯 —",
                                     bg=BG2, fg=TEXT2, font=("Segoe UI", 10))
        self.lbl_accuracy.pack(side="right", padx=18)

        # Режим
        mf = tk.Frame(self.root, bg=BG, pady=14)
        mf.pack()
        tk.Label(mf, text="Режим:", bg=BG, fg=TEXT2,
                 font=("Segoe UI", 10)).pack(side="left", padx=(0, 10))

        self.mode_var = tk.StringVar(value="random")
        for label, val in [("🎲 Рандом", "random"),
                            ("🇬🇧 → 🇺🇦", "en2ua"),
                            ("🇺🇦 → 🇬🇧", "ua2en")]:
            tk.Radiobutton(
                mf, text=label, variable=self.mode_var, value=val,
                bg=BG, fg=TEXT, selectcolor=ACCENT,
                activebackground=BG, activeforeground=TEXT2,
                font=("Segoe UI", 10), command=self.new_word,
            ).pack(side="left", padx=6)

        # Картка слова
        card = tk.Frame(self.root, bg=BG3, padx=40, pady=28)
        card.pack(padx=30, pady=(0, 4), fill="x")

        self.lbl_lang_hint = tk.Label(card, text="ENGLISH → UKRAINIAN",
                                      bg=BG3, fg=ACCENT2,
                                      font=("Segoe UI", 9, "bold"))
        self.lbl_lang_hint.pack()

        self.lbl_word = tk.Label(card, text="", bg=BG3, fg=TEXT,
                                 font=("Segoe UI", 34, "bold"), wraplength=420)
        self.lbl_word.pack(pady=(8, 4))

        self.lbl_sub = tk.Label(card, text="Введи переклад нижче",
                                bg=BG3, fg=TEXT2,
                                font=("Segoe UI", 10, "italic"))
        self.lbl_sub.pack()

        # Поле вводу
        ef = tk.Frame(self.root, bg=BG, pady=16)
        ef.pack()
        self.entry = tk.Entry(ef, font=("Segoe UI", 18), bg=ENTRY, fg=TEXT,
                              insertbackground=TEXT, relief="flat",
                              bd=10, width=22, justify="center")
        self.entry.pack()
        self.entry.focus()

        # Фідбек
        self.lbl_feedback = tk.Label(self.root, text="", bg=BG,
                                     font=("Segoe UI", 12, "bold"))
        self.lbl_feedback.pack(pady=(0, 6))

        # Кнопки
        bf = tk.Frame(self.root, bg=BG, pady=8)
        bf.pack()
        make_button(bf, "✔  Перевірити",  ACCENT, self.check_answer).pack(side="left", padx=7)
        make_button(bf, "→  Далі",        BG3,    self.new_word     ).pack(side="left", padx=7)
        make_button(bf, "💡 Підказка",    BG3,    self.show_hint    ).pack(side="left", padx=7)
        make_button(bf, "👁  Показати",   BG3,    self.reveal       ).pack(side="left", padx=7)

        # Бар прогресу
        self.lbl_progress = tk.Label(self.root, bg=BG, fg=TEXT2,
                                     font=("Segoe UI", 8))
        self.lbl_progress.pack(anchor="e", padx=32)

        # Історія
        hf = tk.Frame(self.root, bg=BG2, pady=8)
        hf.pack(fill="x", pady=(10, 0))
        tk.Label(hf, text="Останні результати:", bg=BG2, fg=TEXT2,
                 font=("Segoe UI", 9, "bold")).pack(anchor="w", padx=14)
        self.hist_text = tk.Text(hf, height=5, bg=BG2, fg=TEXT2,
                                 font=("Segoe UI", 9), relief="flat",
                                 state="disabled", bd=0,
                                 selectbackground=BG3, spacing1=2)
        self.hist_text.pack(fill="x", padx=14, pady=(4, 6))

        # Підказка знизу
        ft = tk.Frame(self.root, bg=BG, pady=6)
        ft.pack(fill="x")
        tk.Label(ft, text="Enter — перевірити  •  Tab — далі  •  F1 — підказка  •  F2 — показати",
                 bg=BG, fg=TEXT2, font=("Segoe UI", 7)).pack()

    # ── Прив'язка клавіш ───────────────────────────────────────────────────────
    def _bind_keys(self):
        self.root.bind("<Return>", lambda _: self.check_answer())
        self.root.bind("<Tab>",    lambda _: (self.new_word(), "break"))
        self.root.bind("<F1>",     lambda _: self.show_hint())
        self.root.bind("<F2>",     lambda _: self.reveal())

    # ── Логіка ────────────────────────────────────────────────────────────────
    def new_word(self):
        if self._after_id:
            self.root.after_cancel(self._after_id)
            self._after_id = None

        self.current_word = random.choice(words_list)
        mode = self.mode_var.get()
        self.current_direction = (
            random.choice(["en2ua", "ua2en"]) if mode == "random" else mode
        )

        if self.current_direction == "en2ua":
            self.lbl_lang_hint.config(text="ENGLISH  →  UKRAINIAN")
            self.lbl_word.config(text=self.current_word["english"])
        else:
            self.lbl_lang_hint.config(text="UKRAINIAN  →  ENGLISH")
            self.lbl_word.config(text=self.current_word["ukrainian"])

        self.entry.delete(0, tk.END)
        self.entry.config(bg=ENTRY)
        self.lbl_feedback.config(text="")
        self.lbl_sub.config(text="Введи переклад нижче", fg=TEXT2)
        self._update_progress()
        self.entry.focus()

    def check_answer(self):
        answer = self.entry.get().strip().lower()
        if not answer:
            return

        correct = (self.current_word["ukrainian"]
                   if self.current_direction == "en2ua"
                   else self.current_word["english"]).lower()

        self.score_total += 1

        if answer == correct:
            self.score_correct += 1
            self.streak        += 1
            self.best_streak    = max(self.best_streak, self.streak)
            self.lbl_feedback.config(text="✅  Правильно!", fg=SUCCESS)
            self.entry.config(bg="#1a3a2a")
            self._add_history(True, answer)
        else:
            self.streak = 0
            self.lbl_feedback.config(
                text=f"❌  Неправильно!  →  {correct}", fg=ERROR)
            self.entry.config(bg="#3a1a1a")
            self._add_history(False, answer)

        self._update_stats()
        self._after_id = self.root.after(1600, self.new_word)

    def show_hint(self):
        correct = (self.current_word["ukrainian"]
                   if self.current_direction == "en2ua"
                   else self.current_word["english"])
        half = max(1, len(correct) // 2)
        self.lbl_sub.config(text=f"💡 Підказка:  {correct[:half]}…", fg=WARN)

    def reveal(self):
        correct = (self.current_word["ukrainian"]
                   if self.current_direction == "en2ua"
                   else self.current_word["english"])
        self.lbl_sub.config(text=f"👁  Відповідь:  {correct}", fg=ACCENT2)

    # ── Допоміжні ─────────────────────────────────────────────────────────────
    def _update_stats(self):
        wrong = self.score_total - self.score_correct
        self.lbl_score.config(text=f"✅ {self.score_correct}   ❌ {wrong}")
        self.lbl_streak.config(
            text=f"🔥 {self.streak}  (рекорд: {self.best_streak})",
            fg=WARN if self.streak >= 3 else TEXT2,
        )
        acc = int(self.score_correct / self.score_total * 100)
        self.lbl_accuracy.config(text=f"🎯 {acc}%")

    def _update_progress(self):
        self.lbl_progress.config(
            text=f"Слів у базі: {len(words_list)}  •  Відповіді: {self.score_total}")

    def _add_history(self, correct: bool, user_answer: str):
        icon = "✅" if correct else "❌"
        w    = self.current_word
        if self.current_direction == "en2ua":
            line = f"{icon}  {w['english']}  →  {w['ukrainian']}"
        else:
            line = f"{icon}  {w['ukrainian']}  →  {w['english']}"
        if not correct:
            line += f"   (введено: {user_answer})"

        self.hist_text.config(state="normal")
        self.hist_text.insert("1.0", line + "\n")
        rows = self.hist_text.get("1.0", "end").strip().splitlines()
        if len(rows) > 8:
            self.hist_text.delete(f"{len(rows)}.0", "end")
        self.hist_text.config(state="disabled")


# ── Запуск ─────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    root = tk.Tk()
    VocabApp(root)
    root.mainloop()
