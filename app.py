import html
import logging

import gradio as gr

from src.config import SETTINGS
from src.logging_utils import configure_logging
from src.recommender import recommender_service

configure_logging()
logger = logging.getLogger(__name__)


CSS = """
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

* { box-sizing: border-box; }

html, body, .gradio-container {
  min-height: 100vh;
  margin: 0;
  font-family: 'Manrope', sans-serif;
  background: radial-gradient(circle at top, #ffffff 0%, #f6f8ff 32%, #eef3fb 68%, #e6edf8 100%);
  color: var(--text);
}

.gradio-container { padding: 0 !important; }

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

.search-row {
  display: grid;
  grid-template-columns: 1fr 160px;
  gap: 12px;
  align-items: center;
}

.search-row .gr-button {
  height: 48px;
  font-weight: 600;
}

.search-row .gr-text-input textarea,
.search-row .gr-text-input input {
  min-height: 48px;
  font-size: 1rem;
}

.search-meta {
  display: grid;
  grid-template-columns: 1fr;
  gap: 12px;
  align-items: center;
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

.spinner {
  width: 28px;
  height: 28px;
  border: 3px solid var(--accent-soft);
  border-top-color: var(--accent);
  border-radius: 50%;
  animation: spin 0.9s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

@media (max-width: 720px) {
  #app-shell { padding: 28px 16px 36px; }
  .hero { padding: 36px 18px 30px; }
  .search-row { grid-template-columns: 1fr; }
}
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
        cards.append(
            "<article class='result-card'>"
            f"<h3 class='result-title'>{html.escape(item.title)}</h3>"
            f"<div class='result-author'>{authors}</div>"
            f"<div class='result-description'>{description}</div>"
            "</article>"
        )

    return (
        "<div class='results-panel'><div class='results-grid'>" + "\n".join(cards) + "</div></div>",
        "<div class='status success'>Recommendations ready.</div>",
    )


def build_app() -> gr.Blocks:
    with gr.Blocks(css=CSS, title="SemanticShelf • AI Book Recommender", fill_height=True) as demo:
        with gr.Column(elem_id="app-shell"):
            gr.HTML(
                """
                <section class='hero'>
                  <h1>SemanticShelf</h1>
                  <p>AI Semantic Book Recommendation Engine</p>
                </section>
                """
            )

            with gr.Column(elem_classes=["search-wrap"]):
                with gr.Row(elem_classes=["search-row"]):
                    query = gr.Textbox(
                        show_label=False,
                        placeholder="Search books by topic, theme, genre, or idea...",
                        lines=1,
                    )
                    search_btn = gr.Button("Search", variant="primary")
                with gr.Row(elem_classes=["search-meta"]):
                    top_k = gr.Slider(
                        minimum=1,
                        maximum=SETTINGS.top_k_max,
                        value=SETTINGS.default_results,
                        step=1,
                        label="Result count",
                    )
                    clear_btn = gr.Button("Clear", variant="secondary")
                status = gr.HTML("<div class='status'>Ready when you are.</div>")

            results = gr.HTML(
                "<div class='results-panel'><div class='empty-state'>"
                "Enter a topic to see recommendations.</div></div>"
            )

            search_btn.click(
                lambda: (
                    "<div class='results-panel'><div class='loading-state'>"
                    "<div class='spinner'></div><div>Searching the shelves...</div>"
                    "</div></div>",
                    "<div class='status loading'>Searching...</div>",
                ),
                inputs=None,
                outputs=[results, status],
                queue=False,
            )

            search_btn.click(fn=_render_results, inputs=[query, top_k], outputs=[results, status], queue=True, show_progress=True)
            query.submit(fn=_render_results, inputs=[query, top_k], outputs=[results, status], queue=True, show_progress=True)

            clear_btn.click(
                fn=lambda: (
                    "",
                    SETTINGS.default_results,
                    "<div class='results-panel'><div class='empty-state'>"
                    "Enter a topic to see recommendations.</div></div>",
                    "<div class='status'>Cleared.</div>",
                ),
                outputs=[query, top_k, results, status],
                queue=False,
            )

    return demo


if __name__ == "__main__":
    logger.info("Initializing recommender service...")
    recommender_service.initialize()
    app = build_app()
    app.launch(
        server_name=SETTINGS.app_host,
        server_port=SETTINGS.app_port,
        share=SETTINGS.app_share,
        debug=SETTINGS.app_debug,
    )
