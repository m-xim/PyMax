from __future__ import annotations

from dataclasses import dataclass, field
from typing import ClassVar

from pymax.formatting.base import FormattedText, TextWriter
from pymax.types.domain.element import ElementAttributes

MAX_HEADING_LEVEL = 6


@dataclass(frozen=True, slots=True)
class _Marker:
    token: str
    element_type: str


@dataclass(slots=True)
class _ActiveMarker:
    marker: _Marker
    start: int


@dataclass(slots=True)
class _MarkdownParser:
    source: str
    writer: TextWriter = field(default_factory=TextWriter)
    index: int = 0

    INLINE_MARKERS: ClassVar[tuple[_Marker, ...]] = (
        _Marker("**", "STRONG"),
        _Marker("__", "STRONG"),
        _Marker("~~", "STRIKETHROUGH"),
        _Marker("++", "UNDERLINE"),
        _Marker("`", "MONOSPACED"),
        _Marker("_", "EMPHASIZED"),
        _Marker("*", "EMPHASIZED"),
    )

    def parse(self) -> FormattedText:
        while self.index < len(self.source):
            if self._parse_fenced_code():
                continue
            if self._parse_prefixed_line("#", "HEADING"):
                continue
            if self._parse_prefixed_line(">", "QUOTE"):
                continue
            self._parse_inline_line()

        return self.writer.render()

    @property
    def position(self) -> int:
        return self.writer.position

    @property
    def line_start(self) -> bool:
        return self.index == 0 or self.source[self.index - 1] == "\n"

    def _append(self, text: str) -> None:
        self.writer.append(text)

    def _append_element(
        self,
        element_type: str,
        start: int,
        attributes: ElementAttributes | None = None,
    ) -> None:
        self.writer.add_element(element_type, start, attributes)

    def _line_end(self, start: int) -> int:
        line_end = self.source.find("\n", start)
        if line_end == -1:
            return len(self.source)
        return line_end

    def _consume_line_break(self) -> None:
        if self.index < len(self.source) and self.source[self.index] == "\n":
            self._append("\n")
            self.index += 1

    def _parse_inline_line(self) -> None:
        line_end = self._line_end(self.index)
        self._append_inline(self.source[self.index : line_end])
        self.index = line_end
        self._consume_line_break()

    def _parse_prefixed_line(self, prefix: str, element_type: str) -> bool:
        if not self.line_start or not self.source.startswith(
            prefix, self.index
        ):
            return False

        content_start = self._prefixed_content_start(prefix)
        if content_start is None:
            return False

        line_end = self._line_end(content_start)
        start = self.position
        self._append_inline(self.source[content_start:line_end])
        self._append_element(element_type, start)
        self.index = line_end
        self._consume_line_break()
        return True

    def _prefixed_content_start(self, prefix: str) -> int | None:
        if prefix != "#":
            marker_end = self.index + len(prefix)
            if (
                marker_end < len(self.source)
                and self.source[marker_end] == " "
            ):
                return marker_end + 1
            return marker_end

        marker_end = self.index
        while marker_end < len(self.source) and self.source[marker_end] == "#":
            marker_end += 1

        if (
            marker_end == self.index
            or marker_end - self.index > MAX_HEADING_LEVEL
            or marker_end >= len(self.source)
            or self.source[marker_end] != " "
        ):
            return None
        return marker_end + 1

    def _parse_fenced_code(self) -> bool:
        fence = "```"
        if not self.line_start or not self.source.startswith(
            fence, self.index
        ):
            return False

        opening_line_end = self.source.find("\n", self.index + len(fence))
        if opening_line_end == -1:
            return False

        content_start = opening_line_end + 1
        closing_start = self.source.find("\n```", content_start)
        if closing_start == -1:
            return False

        code = self.source[content_start:closing_start]
        if not code:
            return False

        start = self.position
        self._append(code)
        self._append_element("CODE", start)

        closing_line_end = self._line_end(closing_start + 1)
        self.index = closing_line_end
        self._consume_line_break()
        return True

    def _append_inline(self, text: str) -> None:
        active: list[_ActiveMarker] = []
        index = 0

        while index < len(text):
            parsed_link = self._parse_link(text, index)
            if parsed_link is not None:
                label, url, next_index = parsed_link
                start = self.position
                self._append(label)
                self._append_element(
                    "LINK",
                    start,
                    ElementAttributes(url=url),
                )
                index = next_index
                continue

            marker = self._marker_at(text, index)
            if marker is not None:
                active_marker = self._find_active(active, marker)
                if active_marker is None:
                    if self._has_closing_marker(text, index, marker.token):
                        active.append(
                            _ActiveMarker(marker, self.position),
                        )
                        index += len(marker.token)
                        continue
                else:
                    self._append_element(
                        marker.element_type,
                        active_marker.start,
                    )
                    active.remove(active_marker)
                    index += len(marker.token)
                    continue

            self._append(text[index])
            index += 1

    def _marker_at(self, text: str, index: int) -> _Marker | None:
        return next(
            (
                marker
                for marker in self.INLINE_MARKERS
                if text.startswith(marker.token, index)
            ),
            None,
        )

    def _has_closing_marker(
        self,
        text: str,
        index: int,
        token: str,
    ) -> bool:
        closing_index = text.find(token, index + len(token))
        return closing_index > index + len(token)

    def _find_active(
        self,
        active: list[_ActiveMarker],
        marker: _Marker,
    ) -> _ActiveMarker | None:
        return next(
            (
                active_marker
                for active_marker in reversed(active)
                if active_marker.marker == marker
            ),
            None,
        )

    def _parse_link(
        self,
        text: str,
        index: int,
    ) -> tuple[str, str, int] | None:
        if not text.startswith("[", index):
            return None

        label_end = text.find("]", index + 1)
        if label_end == -1 or label_end + 1 >= len(text):
            return None
        if text[label_end + 1] != "(":
            return None

        url_start = label_end + 2
        url_end = text.find(")", url_start)
        if url_end == -1:
            return None

        label = text[index + 1 : label_end]
        url = text[url_start:url_end]
        if not label or not url:
            return None
        return label, url, url_end + 1


def format_markdown(text: str) -> FormattedText:
    return _MarkdownParser(text).parse()
