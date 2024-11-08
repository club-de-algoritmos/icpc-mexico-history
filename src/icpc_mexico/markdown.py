import enum
import os
from typing import TextIO, List


class MarkdownFile:
    def __init__(self, filename: str):
        self._filename = filename
        self._file = None

    def __enter__(self):
        if os.path.exists(self._filename):
            print(f'Markdown file {self._filename} already exists, it will ve overwritten')

        self._file = open(self._filename, 'w')
        return Markdown(self._file, 0)

    def __exit__(self, *args):
        self._file.close()


class MarkdownContext(enum.Enum):
    SECTION = 'section'
    COLLAPSIBLE = 'collapsible'


class Markdown:
    def __init__(self, file: TextIO, indent: int):
        self._file = file
        self._indent = indent
        self._context = []

    def _write_line(self, line: str = '') -> None:
        self._file.write(f'{line}\n')

    def _get_current_context(self) -> MarkdownContext:
        return self._context[-1]

    def __enter__(self):
        if self._get_current_context() == MarkdownContext.SECTION:
            self._indent += 1

    def __exit__(self, *args):
        if self._get_current_context() == MarkdownContext.SECTION:
            self._indent -= 1
        if self._get_current_context() == MarkdownContext.COLLAPSIBLE:
            self._write_line('</details>')
        self._write_line()
        self._context.pop()

    def paragraph(self, text: str) -> None:
        self._write_line(text)
        self._write_line()

    def section(self, title: str):
        section_indent = self._indent + 1
        self._context.append(MarkdownContext.SECTION)
        self._write_line(f'{"#" * section_indent} {title}')
        self._write_line()
        return self

    def bullet_point(self, text: str, indent: int = 0) -> None:
        self._write_line(f'{" " * 4 * indent}- {text}')

    def numbered_bullet_point(self, text: str, indent: int = 0) -> None:
        self._write_line(f'{" " * 4 * indent}1. {text}')

    def collapsible(self, summary: str) -> None:
        self._context.append(MarkdownContext.COLLAPSIBLE)
        self._write_line('<details>')
        self._write_line(f'<summary>{summary}</summary>')
        self._write_line()

    def table(self, headers: List[str], rows: List[List[str]]) -> None:
        def row_to_str(row_items: List[str]) -> str:
            return f"| {' | '.join(row_items)} |"

        self._write_line(row_to_str(headers))
        self._write_line(row_to_str(['---'] * len(headers)))
        for row in rows:
            self._write_line(row_to_str(row))
