from __future__ import annotations

from pymax.formatting.base import FormattedText, TextWriter
from pymax.types.domain.element import ElementAttributes


class Text:
    element_type: str | None = None

    def __init__(self, *parts: str | Text) -> None:
        self.parts = parts

    def render(self) -> FormattedText:
        writer = TextWriter()
        self.render_into(writer)
        return writer.render()

    def as_payload(self) -> dict[str, object]:
        return self.render().as_payload()

    def render_into(self, writer: TextWriter) -> None:
        start = writer.position

        for part in self.parts:
            if isinstance(part, Text):
                part.render_into(writer)
            else:
                writer.append(str(part))

        if self.element_type is not None:
            writer.add_element(self.element_type, start, self._attributes())

    def _attributes(self) -> ElementAttributes | None:
        return None

    def __add__(self, other: str | Text) -> Text:
        return Text(self, other)

    def __radd__(self, other: str) -> Text:
        return Text(other, self)


class Bold(Text):
    element_type = "STRONG"


class Italic(Text):
    element_type = "EMPHASIZED"


class Underline(Text):
    element_type = "UNDERLINE"


class Strike(Text):
    element_type = "STRIKETHROUGH"


class Code(Text):
    element_type = "MONOSPACED"


class Pre(Text):
    element_type = "CODE"


class Quote(Text):
    element_type = "QUOTE"


class Heading(Text):
    element_type = "HEADING"


class Link(Text):
    element_type = "LINK"

    def __init__(self, *parts: str | Text, url: str) -> None:
        super().__init__(*parts)
        self.url = url

    def _attributes(self) -> ElementAttributes:
        return ElementAttributes(url=self.url)
