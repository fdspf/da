"""
Информационная система «ЗАРПЛАТА» — Вариант 2
Фреймворк: Streamlit
Запуск локально: streamlit run app.py
"""

import json
import os
import csv
import io
import datetime
import streamlit as st

# ─── Константы ────────────────────────────────────────────────
NDFL_RATE  = 0.13
SICK_RATE  = 0.50
CHILD_DED  = 1400
WORK_DAYS  = 22
DB_FILE    = "employees.json"

# ─── Расчёт зарплаты ──────────────────────────────────────────
def calc_payroll(emp: dict) -> dict:
    worked       = max(WORK_DAYS - emp["sick_days"], 0)
    day_rate     = emp["salary"] / WORK_DAYS
    base_pay     = day_rate * worked
    sick_pay     = day_rate * emp["sick_days"] * SICK_RATE
    gross        = base_pay + sick_pay + emp["bonus"]
    child_deduct = min(emp["children"] * CHILD_DED, gross)
    taxable      = max(gross - child_deduct, 0)
    ndfl         = round(taxable * NDFL_RATE, 2)
    net_pay      = round(gross - ndfl, 2)
    return {
        "gross"  : round(gross, 2),
        "ndfl"   : ndfl,
        "net_pay": net_pay,
    }

# ─── База данных (session_state + JSON) ───────────────────────
def load_db() -> list[dict]:
    if os.path.exists(DB_FILE):
        with open(DB_FILE, encoding="utf-8") as f:
            return json.load(f)
    return [
        {"tab_num":1,"fio":"Петрова Анна Сергеевна",     "position":"Главный бухгалтер","salary":85000,"married":True, "children":2,"sick_days":0, "bonus":10000},
        {"tab_num":2,"fio":"Иванов Пётр Николаевич",      "position":"Бухгалтер",        "salary":52000,"married":True, "children":1,"sick_days":5, "bonus":5000},
        {"tab_num":3,"fio":"Сидорова Мария Дмитриевна",   "position":"Экономист",        "salary":60000,"married":False,"children":0,"sick_days":0, "bonus":0},
        {"tab_num":4,"fio":"Козлов Алексей Владимирович", "position":"Программист",      "salary":95000,"married":True, "children":3,"sick_days":3, "bonus":20000},
        {"tab_num":5,"fio":"Новикова Елена Игоревна",     "position":"Кадровый специалист","salary":45000,"married":False,"children":1,"sick_days":10,"bonus":2000},
    ]

def save_db(employees: list[dict]):
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(employees, f, ensure_ascii=False, indent=2)

def next_tab(employees: list[dict]) -> int:
    return max((e["tab_num"] for e in employees), default=0) + 1

# ─── Инициализация session_state ──────────────────────────────
if "employees" not in st.session_state:
    st.session_state.employees = load_db()
if "page" not in st.session_state:
    st.session_state.page = "main"   # main | add | edit | statement
if "edit_idx" not in st.session_state:
    st.session_state.edit_idx = None

employees = st.session_state.employees

# ─── Стили ────────────────────────────────────────────────────
st.markdown("""
<style>
.block-container{padding-top:1.2rem}
.stButton>button{border-radius:8px}
thead tr th{background:#f0f2f6!important;font-size:13px!important}
.metric-card{background:#f8f9fa;border-radius:10px;padding:14px 18px;
             border:1px solid #e0e0e0;text-align:center}
.metric-label{font-size:12px;color:#666;margin-bottom:4px}
.metric-value{font-size:22px;font-weight:600;color:#0F6E56}
.metric-value.red{color:#c0392b}
</style>
""", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════
#  СТРАНИЦА: ГЛАВНАЯ (список сотрудников)
# ═══════════════════════════════════════════════════════════════
def page_main():
    st.title("📋 ИС «Зарплата» — Вариант 2")

    # ── Панель кнопок ─────────────────────────────────────────
    c1, c2, c3, c4, c5 = st.columns([1.2, 1.4, 1.1, 1.4, 3])
    with c1:
        if st.button("➕ Добавить", use_container_width=True):
            st.session_state.page = "add"
            st.rerun()
    with c3:
        if st.button("🗑 Удалить", use_container_width=True):
            st.session_state.page = "delete"
            st.rerun()
    with c4:
        if st.button("📊 Ведомость", use_container_width=True):
            st.session_state.page = "statement"
            st.rerun()

    st.divider()

    if not employees:
        st.info("Список сотрудников пуст. Нажмите «Добавить».")
        return

    # ── Таблица сотрудников ───────────────────────────────────
    rows = []
    for i, e in enumerate(employees):
        r = calc_payroll(e)
        rows.append({
            "№": i + 1,
            "Таб.": e["tab_num"],
            "ФИО": e["fio"],
            "Должность": e["position"],
            "Оклад, ₽": f"{e['salary']:,.0f}",
            "Дети": e["children"],
            "Болезнь (дн.)": e["sick_days"] if e["sick_days"] else "—",
            "Надбавки, ₽": f"{e['bonus']:,.0f}" if e["bonus"] else "—",
            "К выплате, ₽": f"{r['net_pay']:,.2f}",
        })

    st.dataframe(rows, use_container_width=True, hide_index=True)

    # ── Выбор сотрудника для редактирования ───────────────────
    st.subheader("✏️ Редактировать сотрудника")
    names = [f"{e['tab_num']} — {e['fio']}" for e in employees]
    chosen = st.selectbox("Выберите сотрудника:", names, label_visibility="collapsed")
    idx = names.index(chosen)

    col_edit, _ = st.columns([1, 5])
    with col_edit:
        if st.button("Открыть форму редактирования", use_container_width=True):
            st.session_state.edit_idx = idx
            st.session_state.page = "edit"
            st.rerun()

    # ── Итоговые метрики ──────────────────────────────────────
    st.divider()
    st.subheader("📈 Итоги по всем сотрудникам")
    total_gross = sum(calc_payroll(e)["gross"]   for e in employees)
    total_ndfl  = sum(calc_payroll(e)["ndfl"]    for e in employees)
    total_net   = sum(calc_payroll(e)["net_pay"] for e in employees)

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("👥 Сотрудников",   len(employees))
    m2.metric("💰 Начислено, ₽",  f"{total_gross:,.2f}")
    m3.metric("🧾 НДФЛ, ₽",       f"{total_ndfl:,.2f}")
    m4.metric("✅ К выплате, ₽",   f"{total_net:,.2f}")


# ═══════════════════════════════════════════════════════════════
#  СТРАНИЦА: ДОБАВИТЬ / РЕДАКТИРОВАТЬ
# ═══════════════════════════════════════════════════════════════
def page_form(edit_idx: int | None = None):
    emp = employees[edit_idx] if edit_idx is not None else None
    st.title("➕ Добавить сотрудника" if emp is None else "✏️ Редактировать сотрудника")

    with st.form("emp_form"):
        c1, c2 = st.columns(2)
        tab_num  = c1.number_input("Табельный номер *", min_value=1,
                                    value=int(emp["tab_num"]) if emp else next_tab(employees))
        salary   = c2.number_input("Оклад, ₽ *", min_value=0.0, step=500.0,
                                    value=float(emp["salary"]) if emp else 0.0)
        fio      = st.text_input("ФИО *", value=emp["fio"] if emp else "")
        position = st.text_input("Должность *", value=emp["position"] if emp else "")

        c3, c4, c5 = st.columns(3)
        children  = c3.number_input("Число детей", min_value=0,
                                     value=int(emp["children"]) if emp else 0)
        sick_days = c4.number_input("Дней болезни", min_value=0, max_value=WORK_DAYS,
                                     value=int(emp["sick_days"]) if emp else 0)
        bonus     = c5.number_input("Надбавки / премии, ₽", min_value=0.0, step=100.0,
                                     value=float(emp["bonus"]) if emp else 0.0)
        married   = st.checkbox("Женат / замужем",
                                 value=bool(emp["married"]) if emp else False)

        # Предпросмотр расчёта
        if salary > 0:
            preview = calc_payroll({
                "salary": salary, "sick_days": sick_days,
                "bonus": bonus, "children": children
            })
            st.info(
                f"**Предпросмотр расчёта:**  "
                f"Начислено: **{preview['gross']:,.2f} ₽**  |  "
                f"НДФЛ: **{preview['ndfl']:,.2f} ₽**  |  "
                f"К выплате: **{preview['net_pay']:,.2f} ₽**"
            )

        col_save, col_cancel, _ = st.columns([1, 1, 4])
        submitted = col_save.form_submit_button("✔ Сохранить",
                                                 use_container_width=True,
                                                 type="primary")
        cancelled = col_cancel.form_submit_button("✖ Отмена",
                                                   use_container_width=True)

    if cancelled:
        st.session_state.page = "main"
        st.rerun()

    if submitted:
        if not fio.strip() or not position.strip():
            st.error("Заполните поля ФИО и Должность.")
            return
        if salary <= 0:
            st.error("Оклад должен быть больше нуля.")
            return
        if emp is None and any(e["tab_num"] == tab_num for e in employees):
            st.error(f"Табельный номер {tab_num} уже существует.")
            return

        new_emp = {
            "tab_num": int(tab_num), "fio": fio.strip(),
            "position": position.strip(), "salary": float(salary),
            "married": married, "children": int(children),
            "sick_days": int(sick_days), "bonus": float(bonus),
        }
        if edit_idx is not None:
            employees[edit_idx] = new_emp
        else:
            employees.append(new_emp)

        save_db(employees)
        st.session_state.page = "main"
        st.rerun()


# ═══════════════════════════════════════════════════════════════
#  СТРАНИЦА: УДАЛИТЬ
# ═══════════════════════════════════════════════════════════════
def page_delete():
    st.title("🗑 Удалить сотрудника")
    if not employees:
        st.info("Список пуст.")
        if st.button("← Назад"):
            st.session_state.page = "main"
            st.rerun()
        return

    names = [f"{e['tab_num']} — {e['fio']}" for e in employees]
    chosen = st.selectbox("Выберите сотрудника для удаления:", names)
    idx    = names.index(chosen)
    emp    = employees[idx]

    st.warning(
        f"**{emp['fio']}**  |  {emp['position']}  |  Оклад: {emp['salary']:,.0f} ₽"
    )

    c1, c2, _ = st.columns([1, 1, 4])
    if c1.button("✔ Удалить", type="primary", use_container_width=True):
        employees.pop(idx)
        save_db(employees)
        st.success("Сотрудник удалён.")
        st.session_state.page = "main"
        st.rerun()
    if c2.button("✖ Отмена", use_container_width=True):
        st.session_state.page = "main"
        st.rerun()


# ═══════════════════════════════════════════════════════════════
#  СТРАНИЦА: РАСЧЁТНАЯ ВЕДОМОСТЬ
# ═══════════════════════════════════════════════════════════════
def page_statement():
    now    = datetime.datetime.now()
    months = ["январь","февраль","март","апрель","май","июнь",
              "июль","август","сентябрь","октябрь","ноябрь","декабрь"]
    st.title(f"📊 Расчётная ведомость — {months[now.month - 1]} {now.year}")
    st.caption(
        f"Ставка НДФЛ: {int(NDFL_RATE*100)}%  ·  "
        f"Больничные: {int(SICK_RATE*100)}% от оклада  ·  "
        f"Вычет на ребёнка: {CHILD_DED:,} ₽  ·  "
        f"Рабочих дней: {WORK_DAYS}"
    )

    if not employees:
        st.info("Список сотрудников пуст.")
        if st.button("← Назад"):
            st.session_state.page = "main"
            st.rerun()
        return

    rows = []
    t_gross = t_ndfl = t_net = 0.0
    for e in employees:
        r = calc_payroll(e)
        t_gross += r["gross"]
        t_ndfl  += r["ndfl"]
        t_net   += r["net_pay"]
        rows.append({
            "Таб.№"       : e["tab_num"],
            "ФИО"         : e["fio"],
            "Должность"   : e["position"],
            "Оклад, ₽"    : f"{e['salary']:,.2f}",
            "Начислено, ₽": f"{r['gross']:,.2f}",
            "НДФЛ, ₽"     : f"{r['ndfl']:,.2f}",
            "К выплате, ₽": f"{r['net_pay']:,.2f}",
        })

    st.dataframe(rows, use_container_width=True, hide_index=True)

    # Итоговая строка
    st.markdown(
        f"**ИТОГО:**  Начислено: `{t_gross:,.2f} ₽`  |  "
        f"НДФЛ: `{t_ndfl:,.2f} ₽`  |  "
        f"К выплате: `{t_net:,.2f} ₽`"
    )

    st.divider()

    # ── Метрики ───────────────────────────────────────────────
    m1, m2, m3 = st.columns(3)
    m1.metric("💰 Итого начислено", f"{t_gross:,.2f} ₽")
    m2.metric("🧾 Итого НДФЛ",      f"{t_ndfl:,.2f} ₽")
    m3.metric("✅ Итого к выплате",  f"{t_net:,.2f} ₽")

    # ── Экспорт CSV ───────────────────────────────────────────
    buf = io.StringIO()
    writer = csv.writer(buf, delimiter=";")
    writer.writerow(["Таб.№","ФИО","Должность","Оклад","Начислено","НДФЛ","К выплате"])
    for e in employees:
        r = calc_payroll(e)
        writer.writerow([e["tab_num"], e["fio"], e["position"],
                         e["salary"], r["gross"], r["ndfl"], r["net_pay"]])

    st.download_button(
        label="⬇ Скачать CSV",
        data="\ufeff" + buf.getvalue(),
        file_name=f"zarplata_{now.strftime('%Y_%m')}.csv",
        mime="text/csv",
    )

    if st.button("← Назад к списку"):
        st.session_state.page = "main"
        st.rerun()


# ═══════════════════════════════════════════════════════════════
#  Боковое меню навигации
# ═══════════════════════════════════════════════════════════════
with st.sidebar:
    st.markdown("## 📁 Навигация")
    if st.button("🏠 Список сотрудников", use_container_width=True):
        st.session_state.page = "main"
        st.rerun()
    if st.button("➕ Добавить сотрудника", use_container_width=True):
        st.session_state.page = "add"
        st.rerun()
    if st.button("📊 Расчётная ведомость", use_container_width=True):
        st.session_state.page = "statement"
        st.rerun()
    if st.button("🗑 Удалить сотрудника", use_container_width=True):
        st.session_state.page = "delete"
        st.rerun()

    st.divider()
    st.caption(
        f"ИС «Зарплата» · Вариант 2\n\n"
        f"НДФЛ: {int(NDFL_RATE*100)}%\n"
        f"Больничные: {int(SICK_RATE*100)}%\n"
        f"Вычет/ребёнок: {CHILD_DED:,} ₽"
    )

# ═══════════════════════════════════════════════════════════════
#  Роутер страниц
# ═══════════════════════════════════════════════════════════════
page = st.session_state.page
if page == "main":
    page_main()
elif page == "add":
    page_form(edit_idx=None)
elif page == "edit":
    page_form(edit_idx=st.session_state.edit_idx)
elif page == "delete":
    page_delete()
elif page == "statement":
    page_statement()
