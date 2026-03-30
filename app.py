import html
import logging

import streamlit as st

from src.config import SETTINGS
from src.logging_utils import configure_logging
from src.recommender import recommender_service

configure_logging()
logger = logging.getLogger(__name__)


CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Manrope:wght@400;500;600;700&display=swap');

:root {
  --bg-1: #f6f7fb;
  --bg-2: #e9eff8;
  --surface: #ffffff;
  --text: #0f172a;
  --muted: #5b6b82;
  --accent: #1b6ef3;
  --accent-soft: rgba(27, 110, 243, 0.12);
  --border: #d6deea;
  --shadow: 0 18px 40px rgba(15, 23, 42, 0.12);
}

html, body, .stApp {
  min-height: 100vh;
  margin: 0;
  font-family: 'Manrope', sans-serif;
  background: radial-gradient(circle at top, #ffffff 0%, #f6f8ff 32%, #eef3fb 68%, #e6edf8 100%);
  color: var(--text);
}

#app-shell {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  max-width: 1200px;
  margin: 0 auto;
  padding: 40px 20px 48px;
  gap: 24px;
}

.hero {
  text-align: center;
  padding: 52px 24px 40px;
  background: linear-gradient(140deg, rgba(27, 110, 243, 0.08) 0%, rgba(27, 110, 243, 0.02) 70%);
  border: 1px solid var(--border);
  border-radius: 24px;
  box-shadow: var(--shadow);
}

.hero h1 {
  margin: 0;
  font-size: clamp(2.2rem, 4vw, 3.1rem);
  letter-spacing: -0.02em;
}

.hero p {
  margin: 10px auto 0;
  max-width: 640px;
  color: var(--muted);
  font-size: 1.05rem;
}

.search-wrap {
  margin: 32px auto 0;
  max-width: 720px;
  display: grid;
  gap: 16px;
}

.status {
  text-align: center;
  color: var(--muted);
  font-size: 0.95rem;
}

.status.loading { color: var(--accent); }
.status.error { color: #c2272d; }
.status.success { color: #1f8b5f; }

.results-panel {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 18px;
  padding: 24px;
  box-shadow: var(--shadow);
}

.results-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
  gap: 18px;
}

.result-card {
  border: 1px solid var(--border);
  border-radius: 16px;
  padding: 18px 18px 20px;
  background: #ffffff;
  box-shadow: 0 12px 24px rgba(15, 23, 42, 0.08);
  display: grid;
  gap: 8px;
}

.result-title {
  font-size: 1.06rem;
  margin: 0;
}

.result-author {
  color: var(--muted);
  font-size: 0.92rem;
}

.result-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  font-size: 0.82rem;
  color: var(--muted);
}

.result-badge {
  padding: 2px 8px;
  border-radius: 999px;
  background: var(--accent-soft);
  color: var(--accent);
  font-weight: 600;
}

.result-description {
  color: #23324d;
  font-size: 0.93rem;
  line-height: 1.5;
}

.empty-state,
.loading-state {
  display: grid;
  place-items: center;
  gap: 10px;
  padding: 36px 10px;
  color: var(--muted);
  text-align: center;
}

@media (max-width: 720px) {
  #app-shell { padding: 28px 16px 36px; }
  .hero { padding: 36px 18px 30px; }
}
</style>
"""


def _truncate_text(text: str, max_len: int = 220) -> str:
    if len(text) <= max_len:
        return text
    trimmed = text[: max_len - 1].rsplit(" ", 1)[0]
    return f"{trimmed}..."


def _render_results(query: str, top_k: int) -> tuple[str, str]:
    if not query or not query.strip():
        return (
            "<div class='results-panel'><div class='empty-state'>"
            "Enter a topic to see recommendations.</div></div>",
            "<div class='status'>Awaiting your query.</div>",
        )

    try:
        recommendations = recommender_service.recommend_books(query=query, n_results=top_k)
    except ValueError as exc:
        return (
            "<div class='results-panel'><div class='empty-state'><strong>Input error:</strong> "
            f"{html.escape(str(exc))}</div></div>",
            "<div class='status error'>Fix the input and try again.</div>",
        )
    except Exception as exc:
        logger.exception("Failed to fetch recommendations")
        return (
            "<div class='results-panel'><div class='empty-state'><strong>Server error:</strong> "
            f"{html.escape(str(exc))}</div></div>",
            "<div class='status error'>Unexpected error; check logs.</div>",
        )

    if not recommendations:
        return (
            "<div class='results-panel'><div class='empty-state'>"
            "No recommendations found. Try another theme.</div></div>",
            "<div class='status'>No matches found.</div>",
        )

    cards: list[str] = []
    for item in recommendations:
        description = html.escape(_truncate_text(item.description or ""))
        authors = html.escape(item.authors or "Unknown author")
        categories = html.escape(item.categories or "Uncategorized")
        score = f"{item.score:.3f}"
        cards.append(
            "<article class='result-card'>"
            f"<h3 class='result-title'>{html.escape(item.title)}</h3>"
            f"<div class='result-author'>{authors}</div>"
            f"<div class='result-meta'><span>{categories}</span>"
            f"<span class='result-badge'>Score {score}</span></div>"
            f"<div class='result-description'>{description}</div>"
            "</article>"
        )

    return (
        "<div class='results-panel'><div class='results-grid'>" + "\n".join(cards) + "</div></div>",
        "<div class='status success'>Recommendations ready.</div>",
    )


@st.cache_resource(show_spinner=False)
def _ensure_initialized() -> None:
    recommender_service.initialize()


def _empty_results() -> str:
    return (
        "<div class='results-panel'><div class='empty-state'>"
        "Enter a topic to see recommendations.</div></div>"
    )


def main() -> None:
    st.set_page_config(
        page_title="SemanticShelf • AI Book Recommender",
        page_icon="📚",
        layout="wide",
    )
    st.markdown(CSS, unsafe_allow_html=True)

    if "query" not in st.session_state:
        st.session_state.query = ""
    if "top_k" not in st.session_state:
        st.session_state.top_k = SETTINGS.default_results
    if "results_html" not in st.session_state:
        st.session_state.results_html = _empty_results()
    if "status_html" not in st.session_state:
        st.session_state.status_html = "<div class='status'>Ready when you are.</div>"

    with st.spinner("Initializing recommender..."):
        _ensure_initialized()

    with st.container():
        st.markdown(
            """
            <div id='app-shell'>
              <section class='hero'>
                <h1>SemanticShelf</h1>
                <p>AI Semantic Book Recommendation Engine</p>
              </section>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with st.container():
        st.markdown("<div class='search-wrap'>", unsafe_allow_html=True)
        with st.form("search_form"):
            query = st.text_input(
                "Search books",
                value=st.session_state.query,
                placeholder="Search books by topic, theme, genre, or idea...",
                label_visibility="collapsed",
            )
            top_k = st.slider(
                "Result count",
                min_value=1,
                max_value=SETTINGS.top_k_max,
                value=st.session_state.top_k,
                step=1,
            )
            submitted = st.form_submit_button("Search")
        clear_clicked = st.button("Clear")
        st.markdown("</div>", unsafe_allow_html=True)

    if clear_clicked:
        st.session_state.query = ""
        st.session_state.top_k = SETTINGS.default_results
        st.session_state.results_html = _empty_results()
        st.session_state.status_html = "<div class='status'>Cleared.</div>"
        st.rerun()

    if submitted:
        st.session_state.query = query
        st.session_state.top_k = top_k
        with st.spinner("Searching the shelves..."):
            results_html, status_html = _render_results(query, top_k)
        st.session_state.results_html = results_html
        st.session_state.status_html = status_html

    st.markdown(st.session_state.status_html, unsafe_allow_html=True)
    st.markdown(st.session_state.results_html, unsafe_allow_html=True)


if __name__ == "__main__":
    main()
