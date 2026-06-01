from dataclasses import dataclass
from html.parser import HTMLParser
from typing import ClassVar

from pymax.formatting.base import FormattedText, TextWriter
from pymax.types.domain.element import ElementAttributes


@dataclass(slots=True)
class _HtmlEntity:
    tag: str
    element_type: str
    start: int
    attributes: ElementAttributes | None = None


class _ElementHtmlParser(HTMLParser):
    TAG_TYPES: ClassVar[dict[str, str]] = {
        "a": "LINK",
        "b": "STRONG",
        "blockquote": "QUOTE",
        "code": "MONOSPACED",
        "del": "STRIKETHROUGH",
        "em": "EMPHASIZED",
        "h1": "HEADING",
        "h2": "HEADING",
        "h3": "HEADING",
        "h4": "HEADING",
        "h5": "HEADING",
        "h6": "HEADING",
        "i": "EMPHASIZED",
        "ins": "UNDERLINE",
        "pre": "CODE",
        "s": "STRIKETHROUGH",
        "strong": "STRONG",
        "u": "UNDERLINE",
    }

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.writer = TextWriter()
        self.active: list[_HtmlEntity] = []

    @property
    def position(self) -> int:
        return self.writer.position

    def formatted_text(self) -> FormattedText:
        return self.writer.render()

    def handle_starttag(
        self,
        tag: str,
        attrs: list[tuple[str, str | None]],
    ) -> None:
        tag = tag.lower()
        element_type = self.TAG_TYPES.get(tag)
        if element_type is None:
            return

        attributes = None
        if element_type == "LINK":
            href = self._attr(attrs, "href")
            if href is None:
                return
            attributes = ElementAttributes(url=href)

        self.active.append(
            _HtmlEntity(tag, element_type, self.position, attributes),
        )

    def handle_endtag(self, tag: str) -> None:
        active_entity = self._pop_active(tag.lower())
        if active_entity is None:
            return

        self.writer.add_element(
            active_entity.element_type,
            active_entity.start,
            active_entity.attributes,
        )

    def handle_data(self, data: str) -> None:
        self.writer.append(data)

    def _pop_active(self, tag: str) -> _HtmlEntity | None:
        for index in range(len(self.active) - 1, -1, -1):
            if self.active[index].tag == tag:
                return self.active.pop(index)
        return None

    def _attr(
        self,
        attrs: list[tuple[str, str | None]],
        name: str,
    ) -> str | None:
        return next(
            (
                value
                for attr_name, value in attrs
                if attr_name.lower() == name and value
            ),
            None,
        )


def format_html(text: str) -> FormattedText:
    parser = _ElementHtmlParser()
    parser.feed(text)
    parser.close()
    return parser.formatted_text()
