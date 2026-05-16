
import ast
import re
from urllib.parse import urlparse

from langchain_core.messages import AIMessage

from tools import web_search, web_scrape


def _message_text(messages):
    if not messages:
        return ""
    message = messages[-1]
    if isinstance(message, tuple):
        return str(message[-1])
    return str(getattr(message, "content", message))


class ToolAgent:
    def __init__(self, tool, mode):
        self.tool = tool
        self.mode = mode

    def invoke(self, inputs):
        prompt = _message_text(inputs.get("messages", []))
        if self.mode == "search":
            content = self.tool.invoke(prompt)
        else:
            content = _scrape_first_available(prompt, self.tool)
        return {"messages": [AIMessage(content=content)]}


def _first_url(text):
    match = re.search(r"https?://[^\s\]')\"<>]+", text)
    if match:
        return match.group(0).rstrip(".,")
    return text.strip()


def _all_urls(text):
    return [url.rstrip(".,") for url in re.findall(r"https?://[^\s\]')\"<>]+", text)]


def _scrape_first_available(text, scrape_tool):
    urls = _all_urls(text)
    if not urls:
        return scrape_tool.invoke(_first_url(text))

    last_content = ""
    for url in urls[:5]:
        content = scrape_tool.invoke(url)
        last_content = content
        if _is_useful_scrape(content):
            return content
    return last_content


def _is_useful_scrape(content):
    lowered = content.lower()
    blocked_markers = [
        "access denied",
        "enable javascript",
        "enable javascript and cookies",
        "just a moment",
        "cookies to continue",
        "checking your browser",
        "captcha",
        "403 forbidden",
    ]
    if lowered.startswith("error scraping"):
        return False
    if any(marker in lowered for marker in blocked_markers):
        return False
    return len(content.split()) >= 80


def _extract_results(research):
    marker = "SEARCH RESULTS:"
    end_marker = "DETAILED SCRAPED CONTENT:"
    start = research.find(marker)
    end = research.find(end_marker)
    if start == -1:
        return []

    raw = research[start + len(marker): end if end != -1 else None].strip()
    try:
        data = ast.literal_eval(raw)
    except Exception:
        return []

    if isinstance(data, dict):
        return data.get("results", [])
    return []


def _clean_text(text):
    text = str(text or "")
    text = re.sub(r"https?://\S+", " ", text)
    text = re.sub(r"\[\s*\d+\s*\]", " ", text)
    text = re.sub(r"\[\s*(?:citation needed|edit|source)\s*\]", " ", text, flags=re.I)
    text = re.sub(r"\b(?:and\s+)?see\s+for\s+more\b", " ", text, flags=re.I)
    text = re.sub(r"\b(?:read|learn)\s+more\b", " ", text, flags=re.I)
    text = re.sub(r"\s+", " ", text)
    return text.strip(" -|")


def _clean_title(text):
    text = _clean_text(text)
    return text[:90] + ("..." if len(text) > 90 else "")


def _is_bad_sentence(sentence):
    lowered = sentence.lower()
    if "http://" in lowered or "https://" in lowered:
        return True
    if re.search(r"\[\s*\d+\s*\]", sentence):
        return True
    noisy_markers = [
        "cookie",
        "privacy policy",
        "terms of use",
        "subscribe",
        "sign in",
        "log in",
        "advertisement",
        "skip to",
        "javascript",
    ]
    return any(marker in lowered for marker in noisy_markers)


def _sentences(text):
    cleaned = []
    seen = set()
    for sentence in re.split(r"(?<=[.!?])\s+", text or ""):
        if _is_bad_sentence(sentence):
            continue
        sentence = _clean_text(sentence)
        key = sentence.lower()
        if len(sentence) <= 45 or key in seen:
            continue
        seen.add(key)
        cleaned.append(sentence)
    return cleaned[:10]


def _source_label(result, index):
    title = _clean_title(result.get("title") or "")
    if title:
        return title
    url = result.get("url") or ""
    domain = urlparse(url).netloc.replace("www.", "")
    return domain or f"Source {index}"


def _expand_finding(topic, title, content, scraped_sentences, index):
    content = _clean_text(content)
    source_sentence = scraped_sentences[(index - 1) % len(scraped_sentences)] if scraped_sentences else ""
    title = _clean_title(title)

    parts = [
        f"{title}: {content}" if content else f"{title}: This source adds context to the research topic.",
        f"For {topic}, this matters because it links the core idea with real usage, adoption, and practical decision making.",
    ]

    if source_sentence:
        parts.append(f"Supporting context: {source_sentence}")

    parts.append("This makes the point useful as a compact research signal rather than just a definition.")
    return " ".join(parts)


class WriterChain:
    def invoke(self, inputs):
        topic = inputs["topic"]
        research = inputs["research"]
        results = _extract_results(research)
        scraped = research.split("DETAILED SCRAPED CONTENT:", 1)[-1].strip()
        scraped_sentences = _sentences(scraped)
        source_titles = [_source_label(result, index) for index, result in enumerate(results[:5], start=1)]
        source_summary = ", ".join(source_titles[:3]) if source_titles else "the gathered sources"
        intro_detail = " ".join(scraped_sentences[:3])

        lines = [
            f"Research Report: {topic}",
            "",
            "Introduction",
            (
                f"This report gives a focused overview of {topic}, based on the search results and scraped source content. "
                f"The strongest signals came from {source_summary}, which help explain the current direction of the topic. "
                f"{intro_detail if intro_detail else 'The collected material points to a topic with active development, practical use cases, and important future implications.'} "
                f"The goal is to keep the summary clear while still giving enough detail to understand the main patterns, benefits, and open questions."
            ),
            "",
            "Key Findings",
        ]

        findings = []
        if results:
            for index, result in enumerate(results[:2], start=1):
                title = _source_label(result, index)
                content = result.get("content") or result.get("raw_content") or ""
                findings.append(_expand_finding(topic, title, content, scraped_sentences, index))

        for index, sentence in enumerate(scraped_sentences, start=len(findings) + 1):
            if len(findings) >= 2:
                break
            findings.append(_expand_finding(topic, f"Additional evidence {index}", sentence, scraped_sentences, index))

        while len(findings) < 2:
            findings.append(
                _expand_finding(
                    topic,
                    f"Research pattern {len(findings) + 1}",
                    f"{topic} continues to show important developments across tools, workflows, business adoption, and practical automation use cases.",
                    scraped_sentences,
                    len(findings) + 1,
                )
            )

        for index, finding in enumerate(findings[:2], start=1):
            lines.append(f"{index}. {finding}")

        lines.extend([
            "",
            "Conclusion",
            (
                f"The collected material shows that {topic} is an active area with practical uses, evolving tools, and important questions around reliability. "
                f"The sources suggest real value, especially when the topic is connected to workflows, automation, and decision support. "
                f"At the same time, the claims should be compared across sources instead of relying on one page. "
                f"Overall, {topic} is worth tracking because it has both present-day usefulness and longer-term strategic importance."
            ),
            "",
            "Sources",
        ])

        if results:
            lines.extend(f"- {result.get('url')}" for result in results[:5] if result.get("url"))
        else:
            lines.append("- No source URLs found in the gathered research.")

        return "\n".join(lines)


class CriticChain:
    def invoke(self, inputs):
        report = inputs["report"]
        has_sources = "http" in report
        return "\n".join([
            "- Strengths: The report is structured and includes the main research sections.",
            "- Weaknesses: It may need deeper synthesis if source content is limited.",
            f"- Suggestions: {'Verify each URL and add source-specific citations.' if has_sources else 'Add source URLs and citations.'}",
            "One line verdict: Good draft, but improve citations and evidence depth.",
        ])


def build_search_agent():
    return ToolAgent(web_search, "search")


def build_reader_agent():
    return ToolAgent(web_scrape, "reader")


writer_chain = WriterChain()
critic_chain = CriticChain()
