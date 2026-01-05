from .template import Template

from pathlib import Path
from shutil import copy2 as copy_file

class Config(Template):
    def __init__(self, name: str, path: Path, title: str | None = None, description: str | None = None) -> None:
        super().__init__(name, path, title, description)

    @property
    def files(self):
        return [f for f in self.path.rglob("*") if f.is_file()]
        files: list[Path] = []
        lengths: list[int] = [ 0 ]
        for f in self.path.rglob("*"):
            if not f.is_file():
                continue
            files.append(f)
            lengths.append(len(str(f)))

        return (files, max(lengths))

    def copy_to_destination(self, dst: Path, *, dotfile: bool = True, verbose: bool = False, dry_run: bool = False):
        dir_name = dotfile and f".{self.name}" or self.name
        dst = dst / dir_name

        verbose = verbose or dry_run
        files: list[tuple[Path, Path]] = []
        lengths = [ 0 ]
        for f in self.files:
            rel_path = f.relative_to(self.path)
            files.append((f, rel_path))
            lengths.append(len(str(rel_path)))

        max_len = max(lengths)
        for f, rel_path in files:
            target = dst / rel_path
            if not dry_run:
                target.parent.mkdir(parents=True, exist_ok=True)
                copy_file(f, target)
            if verbose:
                print(f"  {str(rel_path):<{max_len}} -> {target}")
