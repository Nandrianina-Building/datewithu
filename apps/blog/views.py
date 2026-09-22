import re

from django.shortcuts import get_object_or_404, render
from django.utils import timezone
from django.utils.safestring import mark_safe

from .models import Article


def _simple_markdown(text):
    """Rendu Markdown minimal (titres ##, listes -, gras **texte**) — pas
    besoin d'une dépendance externe pour le peu de mise en forme utilisée
    dans les articles du magazine."""
    import html

    text = html.escape(text)
    lines = text.split("\n")
    html_lines = []
    in_list = False
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("## "):
            if in_list:
                html_lines.append("</ul>")
                in_list = False
            html_lines.append(f"<h2>{stripped[3:]}</h2>")
        elif stripped.startswith("- "):
            if not in_list:
                html_lines.append("<ul>")
                in_list = True
            html_lines.append(f"<li>{stripped[2:]}</li>")
        elif not stripped:
            if in_list:
                html_lines.append("</ul>")
                in_list = False
        else:
            if in_list:
                html_lines.append("</ul>")
                in_list = False
            html_lines.append(f"<p>{stripped}</p>")
    if in_list:
        html_lines.append("</ul>")
    rendered = "\n".join(html_lines)
    rendered = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", rendered)
    return mark_safe(rendered)


def article_list_view(request):
    articles = Article.objects.filter(is_published=True, published_at__lte=timezone.now())
    return render(request, "blog/list.html", {"articles": articles})


def article_detail_view(request, slug):
    article = get_object_or_404(Article, slug=slug, is_published=True)
    return render(request, "blog/detail.html", {
        "article": article,
        "content_html": _simple_markdown(article.content),
    })
