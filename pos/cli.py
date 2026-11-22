from fractions import Fraction
from pathlib import Path

from .adapters import percent_text
from .application import AssessmentFacade


MENU = """
1. Добавить студента             2. Список студентов
3. Добавить критерий             4. Рубрикатор
5. Выставить / исправить оценку  6. Оценки студента
7. Отменить оценку               8. Итог студента
9. Экспорт итогов в CSV          0. Выход"""


def ask(label: str) -> str:
    return input(label + ": ").strip()


def integer(label: str) -> int:
    try:
        return int(ask(label))
    except ValueError:
        raise ValueError("Введите целое число.") from None


def read_weight() -> Fraction:
    try:
        return Fraction(ask("Вес (например, 3 или 0,5)").replace(",", "."))
    except (ValueError, ZeroDivisionError):
        raise ValueError("Введите числовой вес, например 0,5.") from None


def execute(command: str, app: AssessmentFacade) -> None:
    if command == "1":
        app.add_student(ask("ID студента"), ask("Имя"))
        print("Студент добавлен.")
    elif command == "2":
        students = app.students()
        if not students:
            print("Студентов пока нет.")
        for student in students:
            print(f"{student.id} — {student.name}")
    elif command == "3":
        app.add_criterion(ask("ID критерия"), ask("Название"), integer("Максимум"), read_weight())
        print("Критерий добавлен.")
    elif command == "4":
        criteria = app.criteria()
        if not criteria:
            print("Рубрикатор пуст.")
        for c in criteria:
            print(f"{c.id} — {c.name}, максимум {c.max_score}, вес {c.weight}")
    elif command == "5":
        app.set_score(ask("ID студента"), ask("ID критерия"), integer("Балл"))
        print("Оценка сохранена.")
    elif command == "6":
        scores = app.scores(ask("ID студента"))
        if not scores:
            print("Рубрикатор пуст.")
        for criterion, score in scores:
            mark = "пока нет оценки" if score is None else f"{score}/{criterion.max_score}"
            print(f"{criterion.name} ({criterion.id}) — {mark}")
    elif command == "7":
        app.cancel_score(ask("ID студента"), ask("ID критерия"))
        print("Оценка отменена.")
    elif command == "8":
        result = app.result(ask("ID студента"))
        if result.course_total is None:
            print("Добавьте хотя бы один критерий.")
            return
        print(f"{result.student.name} — итог курса {percent_text(result.course_total)}%")
        current = result.current_result
        print("Текущий результат:", "пока нет оценок" if current is None else percent_text(current) + "%")
    elif command == "9":
        path = Path(ask("Имя нового CSV-файла") or "results.csv")
        app.export_results(path)
        print(f"Итоги сохранены в {path.absolute()}")
    else:
        print("Выберите пункт меню от 0 до 9.")


def run(app: AssessmentFacade) -> None:
    print("ПОС · Ведомость курса. Данные хранятся до выхода из программы.")
    while True:
        try:
            print(MENU)
            command = ask("Пункт меню")
            if command == "0":
                return
            execute(command, app)
        except (EOFError, KeyboardInterrupt):
            print()
            return
        except FileExistsError:
            print("Файл уже существует. Выберите новое имя для экспорта.")
        except (ValueError, OSError) as error:
            print(f"Ошибка: {error}")
