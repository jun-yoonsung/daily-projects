"""간단한 HTML 태그 짝 검사기 (표준 라이브러리 html.parser 사용)."""

from html.parser import HTMLParser

VOID = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "source", "track", "wbr"}


class _Checker(HTMLParser):
    def __init__(self):
        super().__init__()
        self.stack = []
        self.errors = []

    def handle_starttag(self, tag, attrs):
        if tag not in VOID:
            self.stack.append((tag, self.getpos()))

    def handle_endtag(self, tag):
        if tag in VOID:
            return
        if not self.stack:
            self.errors.append(f"짝 없는 </{tag}> at {self.getpos()}")
            return
        top, pos = self.stack.pop()
        if top != tag:
            self.errors.append(f"<{top}> {pos} 가 </{tag}> {self.getpos()} 로 닫힘")


def check_html(text: str) -> list[str]:
    c = _Checker()
    c.feed(text)
    c.close()
    return c.errors + [f"닫히지 않은 <{t}> {p}" for t, p in c.stack]
