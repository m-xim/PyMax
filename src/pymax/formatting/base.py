from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from pymax.types.domain.element import Element, ElementAttributes


class ParseMode(str, Enum):
    MARKDOWN = "markdown"
    HTML = "html"
    DISABLED = "disabled"


class TextFormat:
    @staticmethod
    def bold(start: int, length: int) -> Element:
        return TextFormat._span("STRONG", start, length)

    @staticmethod
    def italic(start: int, length: int) -> Element:
        return TextFormat._span("EMPHASIZED", start, length)

    @staticmethod
    def underline(start: int, length: int) -> Element:
        return TextFormat._span("UNDERLINE", start, length)

    @staticmethod
    def strike(start: int, length: int) -> Element:
        return TextFormat._span("STRIKETHROUGH", start, length)

    @staticmethod
    def monospace(start: int, length: int) -> Element:
        return TextFormat._span("MONOSPACED", start, length)

    @staticmethod
    def code(start: int, length: int) -> Element:
        return TextFormat._span("CODE", start, length)

    @staticmethod
    def quote(start: int, length: int) -> Element:
        return TextFormat._span("QUOTE", start, length)

    @staticmethod
    def heading(start: int, length: int) -> Element:
        return TextFormat._span("HEADING", start, length)

    @staticmethod
    def link(start: int, length: int, url: str) -> Element:
        return TextFormat._span(
            "LINK",
            start,
            length,
            ElementAttributes(url=url),
        )

    @staticmethod
    def _span(
        element_type: str,
        start: int,
        length: int,
        attributes: ElementAttributes | None = None,
    ) -> Element:
        return Element(
            type=element_type,
            from_=start,
            length=length,
            attributes=attributes,
        )


@dataclass(frozen=True, slots=True)
class FormattedText:
    text: str
    elements: list[Element]

    def as_payload(self) -> dict[str, object]:
        return {"text": self.text, "elements": self.elements}


@dataclass(slots=True)
class TextWriter:
    output: list[str] = field(default_factory=list)
    elements: list[Element] = field(default_factory=list)
    position: int = 0

    def append(self, text: str) -> None:
        self.output.append(text)
        self.position += len(text)

    def add_element(
        self,
        element_type: str,
        start: int,
        attributes: ElementAttributes | None = None,
    ) -> None:
        length = self.position - start
        if length <= 0:
            return

        self.elements.append(
            Element(
                type=element_type,
                from_=start,
                length=length,
                attributes=attributes,
            ),
        )

    def render(self) -> FormattedText:
        return FormattedText("".join(self.output), self.elements)
