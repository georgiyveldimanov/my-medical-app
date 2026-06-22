import os
import json
import re
import streamlit as st
from groq import Groq
from dotenv import load_dotenv

st.set_page_config(page_title="МИС Клинический Аудит", page_icon="🏥", layout="centered")

# 2. И только ПОСЛЕ нее вставляем наш хак для обхода заглушки Pinggy
st.markdown(
    """
    <script>
    const originalFetch = window.fetch;
    window.fetch = async function(...args) {
        if (!args[1]) args[1] = {};
        if (!args[1].headers) args[1].headers = {};
        
        args[1].headers['ngrok-skip-browser-warning'] = 'true';
        args[1].headers['X-Pinggy-No-Screen'] = 'true';
        
        return originalFetch.apply(this, args);
    };
    </script>
    """,
    unsafe_allow_html=True
)
# 1. ЗАГРУЗКА ОКРУЖЕНИЯ И ИНИЦИАЛИЗАЦИЯ
load_dotenv()

# Жестко вшитый рабочий ключ
api_key = "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"

# Инициализируем клиента Groq один раз
client = Groq(api_key=api_key)

# 2. КОНФИГУРАЦИЯ И СТИЛИЗАЦИЯ СТРАНИЦЫ (МЯГКИЙ МЕД-ТЕХ)
st.set_page_config(page_title="МИС Клинический Аудит", page_icon="🏥", layout="centered")

# Настройка стилей под мягкие жемчужно-серые и пастельные тона
st.markdown("""
    <style>
    /* Матовый жемчужно-серый фон приложения — мягкий для глаз */
    .stApp {
        background-color: #F1F3F5 !important;
    }
    
    /* Скрываем дефолтные элементы Streamlit */
    footer {visibility: hidden;}
    #MainMenu {visibility: hidden;}
    header {background-color: transparent !important;}
    
    /* Текстовые поля: чистый мягкий белый цвет с деликатной стальной границей */
    .stTextArea textarea, .stTextInput input {
        background-color: #FFFFFF !important;
        border: 1px solid #CBD5E1 !important;
        border-radius: 8px !important;
        color: #334155 !important;
        font-family: 'Inter', sans-serif !important;
        font-size: 14px !important;
        box-shadow: inset 0 1px 2px rgba(0, 0, 0, 0.02) !important;
    }
    
    /* Эффект фокуса на полях ввода: глубокий сапфировый акцент */
    .stTextArea textarea:focus, .stTextInput input:focus {
        border-color: #3B82F6 !important;
        box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.15) !important;
    }
    
    /* Лейблы к полям (благородный грифельный цвет) */
    .stWidget label {
        color: #475569 !important;
        font-weight: 600 !important;
        font-family: 'Inter', sans-serif !important;
        font-size: 14px !important;
    }
    
    /* Кнопка ФЛК: приглушенный строгий сине-стальной цвет */
    .stButton > button {
        background-color: #334155 !important;
        color: #FFFFFF !important;
        border: none !important;
        border-radius: 8px !important;
        font-weight: 600 !important;
        font-size: 14px !important;
        letter-spacing: 0.3px !important;
        padding: 12px 24px !important;
        width: 100% !important;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05) !important;
        transition: all 0.2s ease !important;
    }
    .stButton > button:hover {
        background-color: #1E293B !important;
        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1) !important;
    }
    
    /* Кастомизация всплывающего окна под общий мягкий стиль */
    div[data-role="dialog"] {
        background-color: #FFFFFF !important;
        border-radius: 12px !important;
        box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.1) !important;
    }
    </style>
""", unsafe_allow_html=True)

# Заголовок интерфейса
st.markdown("<h2 style='color: #1E293B; font-family: sans-serif; font-weight: 700; margin-bottom: 2px;'>🏥 МИС: Внутренний контроль качества медицинской помощи</h2>", unsafe_allow_html=True)
st.markdown("<p style='color: #64748B; font-size: 14px; font-family: sans-serif; margin-bottom: 25px;'>Модуль автоматизированного форматно-логического контроля (ФЛК) электронных карт</p>", unsafe_allow_html=True)
st.markdown("<hr style='border: 0; height: 1px; background: #CBD5E1; margin-bottom: 25px;'>", unsafe_allow_html=True)

# Форма ввода данных пациента
complaints = st.text_area(
    "1. Протокол осмотра (Жалобы, симптомы, объективный статус):", 
    placeholder="Внесите данные осмотра, жалобы пациента и коморбидный фон...",
    height=100
)

diagnosis = st.text_input(
    "2. Код основного заболевания (МКБ-10):", 
    placeholder="Пример: I10 — Первичная артериальная гипертензия"
)

treatment = st.text_area(
    "3. Лист назначений (Фармакотерапия, диагностические исследования):", 
    placeholder="Укажите схемы лечения, дозировки препаратов, назначенные анализы или манипуляции...",
    height=100
)

st.markdown("")

# 3. УНИВЕРСАЛЬНЫЙ МЕДИЦИНСКИЙ ПРОМПТ ДЛЯ КЛИНИЧЕСКОГО МЫШЛЕНИЯ ИИ
SYSTEM_PROMPT = """
Вы — ведущий профессор-эксперт автоматизированного клинического аудита Минздрава РФ. 
Ваша задача — провести глубокий перекрестный анализ ЭМК пациента: сопоставить Жалобы/Симптомы, Поставленный диагноз и Назначенное лечение.

КРИТИЧЕСКИ ВАЖНЫЕ ПРАВИЛА АНАЛИЗА:
1. Врачи могут ошибаться или ошибочно кодировать основной диагноз в МИС (например, случайно вбить 'Рак' или другую нозологию). Не верьте слепо полю "Диагноз", если симптомы и терапия кричат о другом!
2. Сначала детально проанализируйте ЖАЛОБЫ, СИМПТОМЫ и АНАМНЕЗ. Если у пациента затылочные боли, АД 155/95 и мушки в глазах — это классический синдром артериальной гипертензии.
3. Если выставленный диагноз кардинально противоречит клинической картине и тому, что врач РЕАЛЬНО лечит (например, в диагнозе стоит Онкология, а врач назначает гипотензивный Периндоприл и диету без соли) — вы ОБЯЗАНЫ зафиксировать ошибку кодирования диагноза в блоке критических ошибок ('critical_errors'). 
4. При этом аудит ЛЕЧЕНИЯ и упущенных стандартов проводите строго по той патологии, которую врач РЕАЛЬНО пытается лечить (в данном случае — Артериальная гипертензия). Не требуйте онкологических стандартов обследования, если терапевт купирует гипертонический синдром!
5. Внимательно проверяйте назначенные ДОЗИРОВКИ лекарств. Если дозировка превышает максимально допустимую, опасна для жизни или некорректна — обязательно вынесите это в 'critical_errors'.

Выдайте ответ СТРОГО в формате JSON без какого-либо постороннего текста вокруг:
{
  "status": "green" или "yellow" или "red",
  "critical_errors": [
    "При несоответствии диагноза симптомам пишите строго: 'Выявлено критическое несоответствие: клиническая картина и назначенная терапия соответствуют Артериальной гипертензии, однако в системе ошибочно закодирован диагноз Рак. Рекомендуется скорректировать код МКБ-10 основного заболевания.'"
  ],
  "omitted_standards": [
    "Упущенные обязательные назначения и обследования строго по РЕАЛЬНОЙ патологии (для гипертензии: Эхокардиография, биохимический анализ крови на холестерин, креатинин, калий и т.д.)"
  ],
  "compliance_approved": [
    "Что врач назначил абсолютно верно для купирования реальной проблемы (например: Назначение ингибитора АПФ Периндоприла, рекомендации по контролю АД, ограничение поваренной соли)"
  ],
  "source_title": "Точное название клинической рекомендации Минздрава РФ, по которой оценивался реальный профиль лечения (например: Клинические рекомендации по диагностике и лечению артериальной гипертонии)"
}
Никакого лишнего текста вне JSON.
"""

# 4. ФУНКЦИЯ ОТОБРАЖЕНИЯ ВСПЛЫВАЮЩЕГО ОКНА
@st.experimental_dialog("Экспертное заключение автоматизированного аудита качества медицинской помощи", width="large")
def show_audit_result(result_json):
    try:
        json_match = re.search(r"\{.*\}", result_json, re.DOTALL)
        clean_json = json_match.group(0) if json_match else result_json
        
        data = json.loads(clean_json)
        
        if data["status"] == "red":
            st.error("Выявлены критические дефекты ведения карты и тактические риски")
        elif data["status"] == "yellow":
            st.warning("Зафиксированы отклонения от утвержденных критериев качества Минздрава РФ")
        else:
            st.success("Качество ведения медицинской документации соответствует стандартам")
            
        st.markdown("---")
        
        if data.get("critical_errors"):
            st.markdown("**1. Критические несоответствия и дефекты кодирования:**")
            for err in data["critical_errors"]:
                st.markdown(f"- {err}")
            st.markdown("")
                
        if data.get("omitted_standards"):
            st.markdown("**2. Упущенные назначения и коды для интеграции (Приказ № 804н):**")
            
            services_vocabulary = {
                "холестерин": "— **A12.05.027** (Определение уровня общего холестерина в крови)",
                "липопротеин": "— **A12.05.028** (Определение уровня липопротеинов низкой плотности)",
                "креатинин": "— **A12.05.011** (Определение уровня креатинина в крови для расчета СКФ)",
                "мочевин": "— **A12.05.010** (Определение уровня мочевины в крови)",
                "эхокардио": "— **A04.10.002** (Эхокардиография / УЗИ сердца)",
                "экг": "— **A05.10.006** (Регистрация электрокардиограммы)",
                "глазного дна": "— **A02.26.003** (Офтальмоскопия / исследование глазного дна)",
                "мочи": "— **B03.016.006** (Анализ мочи общий)",
                "кров": "— **B03.016.002** (Общий анализ крови)"
            }
            
            for omit in data["omitted_standards"]:
                matched_code = ""
                omit_lower = omit.lower()
                
                for key, code_text in services_vocabulary.items():
                    if key in omit_lower:
                        matched_code = f" {code_text}"
                        break
                
                st.markdown(f"- {omit}{matched_code}")
            st.markdown("")
                
        if data["status"] != "green":
            st.markdown("**3. Clinical Risk Assessment (Клинические риски):**")
            title_lower = data.get("source_title", "").lower()
            
            if "гипертенз" in title_lower or "гипертония" in title_lower:
                st.info("Высокий риск субклинического поражения органов-мишеней: гипертрофия левого желудочка (ХСН), хроническая болезнь почек (ХБП), сосудистые катастрофы (инсульт, инфаркт миокарда).")
            elif "язв" in title_lower:
                st.info("Риск деструктивных осложнений: перфорация язвы, желудочно-кишечное кровотечение, пенетрация, малигнизация процесса при отсутствии контроля эрадикации.")
            elif "астм" in title_lower:
                st.info("Риск потери контроля над заболеванием: развитие астматического статуса, необратимое ремоделирование дыхательных путей, инвалидизация пациента.")
            else:
                st.info("Риск прогрессирования основного заболевания, затяжного течения и развития сопутствующих коморбидных усложнений.")
            st.markdown("")

        if data.get("compliance_approved"):
            st.markdown("**4. Корректно выполненные объемы помощи:**")
            for app in data["compliance_approved"]:
                st.markdown(f"- {app}")
            st.markdown("")
            
        st.markdown("---")
        
        source_title = data.get("source_title", "Клинические рекомендации Минздрава РФ")
        st.markdown("**5. Нормативно-правовое обоснование заключения**")
        
        legal_text = f"""
        > **Основание проведения контроля:** Согласно **ст. 37 Федерального закона № 323-ФЗ** «Об основах охраны здоровья граждан в Российской Федерации», медицинская помощь на территории РФ организается и оказывается в обязательном порядке **на основе клинических рекомендаций**.
        > 
        > **Клинический протокол верификации:** Проверка проведена по официальному документу Минздрава РФ: *«{source_title}»*.
        > 
        > **Экспертное примечание:** Выявленные упущенные назначения напрямую соотносятся с **Приказом Минздрава России № 203н** «Об утверждении критериев оценки качества медицинской помощи». Интегрированные коды услуг соответствуют **Приказом Минздрава России № 804н** «Об утверждении номенклатуры медицинских услуг» и готовы для быстрой вставки в электронное направление МИС.
        """
        st.markdown(legal_text)
        
    except Exception as e:
        st.error("Ошибка парсинга ответа модели. ИИ вернул некорректный формат.")
        st.text(result_json)

# 5. ОБРАБОТКА НАЖАТИЯ КНОПКИ
if st.button("📋 ОТПРАВИТЬ ЭМК НА ФОРМАТНО-ЛОГИЧЕСКИЙ КОНТРОЛЬ (ФЛК)"):
    if not diagnosis or not treatment:
        st.warning("Пожалуйста, заполните поля 'Диагноз по МКБ-10' и 'Лист назначений'.")
    else:
        with st.spinner("МИС: Выполняется автоматический перекрестный аудит на соответствие критериям качества..."):
            try:
                user_content = f"Симптомы: {complaints}\nДиагноз: {diagnosis}\nНазначения: {treatment}"
                
                response = client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=[
                        {"role": "system", "content": SYSTEM_PROMPT},
                        {"role": "user", "content": user_content}
                    ],
                    temperature=0.0,  
                    max_tokens=1024,
                    response_format={"type": "json_object"}  
                )
                
                result_text = response.choices[0].message.content
                show_audit_result(result_text)
                
            except Exception as e:
                st.error(f"Произошла ошибка при обращении к серверу Groq: {e}")




        

   