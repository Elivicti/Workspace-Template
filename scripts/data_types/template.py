from pathlib import Path

class Template:
    TEMPLATE_ROOT: Path = Path(__file__).parent.parent

    def __init__(self, name: str, path: Path, title: str | None = None, description: str | None = None) -> None:
        self._name = name
        self._path = Path(path)
        self._title = title or path.name
        self._description = description or ""

    @property
    def name(self): return self._name
    @property
    def path(self): return self._path
    @property
    def title(self): return self._title
    @property
    def description(self): return self._description
