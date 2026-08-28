"""
Wrapper gọi LLM cho các bước 3 (phát hiện văn hóa), 4 (dịch sát nghĩa),
5 (bản địa hóa hài) và 6 (QA dịch ngược).

Hỗ trợ 2 nhà cung cấp, chọn qua .env (LLM_PROVIDER=gemini | anthropic).
Tách riêng hàm generate() để dễ thay/thêm provider khác sau này (OpenAI, model local...).
"""
import json
from .config import settings


def _extract_json(text: str):
    """LLM đôi khi trả về kèm ```json ... ``` hoặc text thừa quanh JSON — dọn trước khi parse."""
    text = text.strip()
    if text.startswith("```"):
        text = text.strip("`")
        if text.lower().startswith("json"):
            text = text[4:]
    text = text.strip()
    return json.loads(text)


def generate(system_prompt: str, user_prompt: str) -> str:
    provider = settings.LLM_PROVIDER.lower()
    if provider == "gemini":
        return _generate_gemini(system_prompt, user_prompt)
    elif provider == "anthropic":
        return _generate_anthropic(system_prompt, user_prompt)
    elif provider == "openai_compatible":
        return _generate_openai_compatible(system_prompt, user_prompt)
    else:
        raise ValueError(f"LLM_PROVIDER không hợp lệ: {provider}")


def _generate_gemini(system_prompt: str, user_prompt: str) -> str:
    import google.generativeai as genai

    genai.configure(api_key=settings.GEMINI_API_KEY)
    model = genai.GenerativeModel(
        model_name=settings.GEMINI_MODEL,
        system_instruction=system_prompt,
    )
    resp = model.generate_content(user_prompt)
    return resp.text


def _generate_anthropic(system_prompt: str, user_prompt: str) -> str:
    import anthropic

    client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)
    resp = client.messages.create(
        model=settings.ANTHROPIC_MODEL,
        max_tokens=4000,
        system=system_prompt,
        messages=[{"role": "user", "content": user_prompt}],
    )
    return "".join(block.text for block in resp.content if block.type == "text")


def _generate_openai_compatible(system_prompt: str, user_prompt: str) -> str:
    """
    Gọi 1 proxy/reseller API theo chuẩn OpenAI-compatible (VD: shopaikey.com).

    ⚠️ Lưu ý bảo mật: nội dung transcript của bạn sẽ đi qua server của bên thứ 3 này,
    không phải trực tiếp tới Google/Anthropic. Chỉ dùng nếu bạn đã chấp nhận rủi ro đó
    (đã trao đổi và xác nhận trong quá trình build tool).

    Cần điền OPENAI_COMPAT_BASE_URL chính xác theo tài liệu của nhà cung cấp trong .env,
    ví dụ dạng: https://shopaikey.com/v1
    """
    import requests

    if not settings.OPENAI_COMPAT_BASE_URL:
        raise ValueError(
            "Chưa cấu hình OPENAI_COMPAT_BASE_URL trong .env — "
            "vào tài liệu/dashboard của nhà cung cấp để lấy đúng endpoint."
        )

    url = settings.OPENAI_COMPAT_BASE_URL.rstrip("/") + "/chat/completions"
    headers = {
        "Authorization": f"Bearer {settings.OPENAI_COMPAT_API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": settings.OPENAI_COMPAT_MODEL,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "temperature": 0.7,
    }

    resp = requests.post(url, headers=headers, json=payload, timeout=60)
    if resp.status_code != 200:
        raise RuntimeError(
            f"Gọi API openai_compatible thất bại (HTTP {resp.status_code}): {resp.text[:500]}"
        )

    data = resp.json()
    try:
        return data["choices"][0]["message"]["content"]
    except (KeyError, IndexError) as e:
        raise RuntimeError(f"Response không đúng định dạng OpenAI chuẩn: {data}") from e


def generate_json(system_prompt: str, user_prompt: str):
    """Gọi LLM và ép kết quả về JSON. Dùng cho các bước cần output có cấu trúc."""
    raw = generate(system_prompt, user_prompt)
    return _extract_json(raw)
