import enum
from typing import TextIO


class MarkdownFile:
    def __init__(self, filename: str):
        self.filename = filename
        self.file = None

    def __enter__(self):
        self.file = open(self.filename, 'w')
        return Markdown(self.file, 0)

    def __exit__(self, *args):
        self.file.close()


class MarkdownContext(enum.Enum):
    SECTION = 'section'
    COLLAPSIBLE = 'collapsible'


class Markdown:
    def __init__(self, file: TextIO, indent: int):
        self.file = file
        self.indent = indent
        self.context = []

    def _write_line(self, line: str = '') -> None:
        self.file.write(f'{line}\n')

    def _get_current_context(self) -> MarkdownContext:
        return self.context[-1]

    def __enter__(self):
        if self._get_current_context() == MarkdownContext.SECTION:
            self.indent += 1

    def __exit__(self, *args):
        if self._get_current_context() == MarkdownContext.SECTION:
            self.indent -= 1
        if self._get_current_context() == MarkdownContext.COLLAPSIBLE:
            self._write_line('</details>')
        self._write_line()
        self.context.pop()

    def paragraph(self, text: str) -> None:
        self._write_line(text)
        self._write_line()

    def section(self, title: str):
        section_indent = self.indent + 1
        self.context.append(MarkdownContext.SECTION)
        self._write_line(f'{"#" * section_indent} {title}')
        self._write_line()
        return self

    def bullet_point(self, text: str, indent: int = 0) -> None:
        self._write_line(f'{" " * 2 * indent}- {text}')

    def collapsible(self, summary: str):
        self.context.append(MarkdownContext.COLLAPSIBLE)
        self._write_line('<details>')
        self._write_line(f'<summary>{summary}</summary>')
        self._write_line()
        return self
