import streamlit as st

from translator import LANGUAGES, MAX_CHARS, TranslationError, translate

st.set_page_config(page_title="AI 번역기", page_icon="🌐", layout="centered")

LABELS = {"영어": "EN · 영어", "일본어": "JA · 일본어", "중국어": "ZH · 중국어"}

st.markdown(
    """
<style>
/* 버튼 3개를 모바일에서도 한 줄로 유지 */
div[data-testid="stHorizontalBlock"] { flex-wrap: nowrap !important; gap: 0.5rem; }
div[data-testid="stHorizontalBlock"] > div[data-testid="stColumn"] { min-width: 0 !important; flex: 1 1 0 !important; }

/* 번역 버튼 */
div[data-testid="stColumn"] button {
    border-radius: 12px;
    font-weight: 600;
    padding: 0.6rem 0.25rem;
    white-space: nowrap;
    transition: transform .12s ease, box-shadow .12s ease, border-color .12s ease;
}
div[data-testid="stColumn"] button:hover {
    transform: translateY(-2px);
    box-shadow: 0 4px 12px rgba(79, 70, 229, .25);
    border-color: #4F46E5;
}

.app-subtitle { opacity: .7; margin-top: -0.5rem; margin-bottom: 1.25rem; }
.char-count { text-align: right; font-size: .85rem; opacity: .7; margin: -0.5rem 0 .5rem; }
.char-count.warn { color: #D97706; opacity: 1; font-weight: 600; }
.char-count.full { color: #DC2626; opacity: 1; font-weight: 700; }
.result-title { font-weight: 700; font-size: 1.05rem; margin-bottom: .25rem; }
.result-lang { opacity: .7; font-size: .85rem; margin-bottom: .5rem; }
.result-empty { opacity: .6; padding: 1.25rem 0; text-align: center; }
</style>
""",
    unsafe_allow_html=True,
)

st.title("🌐 AI 번역기")
st.markdown('<div class="app-subtitle">텍스트를 입력하고 번역할 언어를 선택하세요.</div>', unsafe_allow_html=True)

with st.container(border=True):
    text = st.text_area(
        "번역할 텍스트",
        height=180,
        placeholder="번역할 텍스트를 입력하세요",
        label_visibility="collapsed",
    )
    count = len(text)
    css = "full" if count > MAX_CHARS else "warn" if count >= MAX_CHARS * 0.9 else ""
    st.markdown(f'<div class="char-count {css}">{count:,} / {MAX_CHARS:,}자</div>', unsafe_allow_html=True)
    if count > MAX_CHARS:
        st.warning(f"입력이 {MAX_CHARS:,}자를 초과했습니다. {count - MAX_CHARS:,}자를 줄여주세요.")

    clicked = None
    for col, label in zip(st.columns(len(LANGUAGES)), LANGUAGES):
        if col.button(LABELS[label], use_container_width=True, key=f"btn_{label}"):
            clicked = label

if clicked:
    if not text.strip():
        st.session_state.pop("result", None)
        st.warning("번역할 텍스트를 입력해주세요.")
    else:
        try:
            with st.spinner(f"{clicked}로 번역하는 중..."):
                st.session_state["result"] = (clicked, text, translate(text, clicked))
        except TranslationError as e:
            st.session_state.pop("result", None)
            st.error(str(e))

with st.container(border=True):
    st.markdown('<div class="result-title">번역 결과</div>', unsafe_allow_html=True)
    result = st.session_state.get("result")
    if result and result[1] == text:  # 입력이 바뀌면 이전 결과는 숨긴다
        language, _, translated = result
        st.markdown(f'<div class="result-lang">{LABELS[language]}로 번역됨</div>', unsafe_allow_html=True)
        st.code(translated, language=None, wrap_lines=True)
    else:
        st.markdown('<div class="result-empty">번역 결과가 여기에 표시됩니다.</div>', unsafe_allow_html=True)
