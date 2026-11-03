from flask import Flask, request, jsonify
from flask_cors import CORS
from gigachat import GigaChat
from gigachat.models import Chat, Messages, MessagesRole
import os
import json

app = Flask(__name__)
CORS(app)

giga = GigaChat(
    base_url="https://api.giga.chat/v1",
    credentials=os.getenv("API_KEY"),
    scope="GIGACHAT_API_PERS",
    verify_ssl_certs=False,
    model="GigaChat-2"
)

SYSTEM_PROMPT = """Ты — профессиональный копирайтер и SEO-специалист B2B-магазина измерительных приборов.
Твоя задача — создать черновик карточки товара СТРОГО на основе предоставленных данных.

КРИТИЧЕСКИЕ ПРАВИЛА:
1. НЕ ВЫДУМЫВАЙ новые технические характеристики, материалы или сферы применения, которых нет в данных.
2. Если какого-то технического параметра нет, пиши "Данных нет".
3. В commercial_block описывай ТОЛЬКО то, что прямо следует из описания и характеристик.

ТРЕБОВАНИЯ К ПОЛЯМ:
- seo_title: строго до 70 символов.
- seo_description: СТРОГО от 800 до 1200 символов с пробелами. Это обязательное требование! 
  Чтобы достичь нужной длины, не выдумывая факты, используй следующий подход:
  * Абзац 1: Подробно опиши назначение прибора (используя текст из description).
  * Абзац 2: Детально разбери каждую характеристику из specs. Например, если указан "диапазон 0-1,6 МПа", напиши: "Диапазон измерений составляет от 0 до 1,6 МПа, что позволяет использовать прибор для контроля широкого спектра сред".
  * Абзац 3: Опиши, как характеристики связаны между собой (например, класс точности 1,5 обеспечивает высокую точность при данном диапазоне).
  * Абзац 4: Сделай вывод о том, для каких задач подходит прибор, основываясь на его технических параметрах.
- key_features: маркированный список из 3-6 пунктов, ровно по характеристикам из specs.
- search_queries: 3-5 коротких поисковых запросов.
- commercial_block: 2-3 предложения для менеджера на основе фактов.
- missing_fields: массив строк с названиями полей, которых не хватает.

ФОРМАТ ОТВЕТА (строго JSON, без markdown-обёрток):
{
  "seo_title": "...",
  "seo_description": "...",
  "key_features": ["..."],
  "search_queries": ["..."],
  "commercial_block": "...",
  "missing_fields": []
}"""
@app.route('/api/generate', methods=['POST'])
def generate():
    api_key = os.getenv("API_KEY")
    if not api_key:
        return jsonify({
            "detail": "API-ключ не настроен. Добавьте API_KEY в файл .env"
        }), 503

    data = request.get_json(silent=True)
    if data is None or not isinstance(data, dict):
        return jsonify({"detail": "Тело запроса не является валидным JSON-объектом."}), 400

    # ... (проверка input_missing остаётся без изменений)
    input_missing = []
    if not data.get("name"): input_missing.append("name")
    if not data.get("manufacturer"): input_missing.append("manufacturer")
    if not data.get("specs") or not isinstance(data.get("specs"), dict) or len(data["specs"]) == 0: input_missing.append("specs")
    if not data.get("description"): input_missing.append("description")

    user_content = (
        "Данные товара (используй ТОЛЬКО их):\n"
        f"{json.dumps(data, ensure_ascii=False, indent=2)}\n\n"
        "Создай JSON по шаблону. Напоминаю: seo_description строго от 800 до 1200 символов. "
        "Не придумывай ничего, чего нет в данных."
    )

    chat_request = Chat(
        messages=[
            Messages(role=MessagesRole.SYSTEM, content=SYSTEM_PROMPT),
            Messages(role=MessagesRole.USER, content=user_content)
        ],
        temperature=0.1,  # Чем ниже, тем меньше "творчества" и выдумок
        max_tokens=2500
    )

    try:
        response = giga.chat(chat_request)
        raw = response.choices[0].message.content.strip()

        # Чистим markdown
        if raw.startswith("```json"): raw = raw[7:]
        if raw.startswith("```"): raw = raw[3:]
        if raw.endswith("```"): raw = raw[:-3]
        raw = raw.strip()

        result = json.loads(raw)

        required = ["seo_title", "seo_description", "key_features", "search_queries", "commercial_block"]
        missing_keys = [k for k in required if k not in result]
        if missing_keys:
            return jsonify({
                "detail": f"Модель вернула неполный JSON. Отсутствуют поля: {', '.join(missing_keys)}",
                "raw_response": raw[:800]
            }), 502

        model_missing = result.get("missing_fields", [])
        if not isinstance(model_missing, list): model_missing = []
        result["missing_fields"] = list(set(model_missing + input_missing))

        # Проверка длины SEO-описания (можно добавить предупреждение)
        desc_len = len(result.get("seo_description", ""))
        if desc_len < 800:
            result["missing_fields"].append(f"SEO-описание слишком короткое ({desc_len} символов, нужно 800-1200)")

        return jsonify(result)

    except json.JSONDecodeError:
        return jsonify({
            "detail": "Модель вернула невалидный JSON. Попробуйте ещё раз.",
            "raw_response": raw[:800]
        }), 502
    except Exception as e:
        return jsonify({"detail": f"Ошибка GigaChat: {str(e)}"}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)