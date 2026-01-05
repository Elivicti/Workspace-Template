from sys import stderr
from pathlib import Path
from shutil import copy2 as copy_file
import json

from .exceptions import *
from .template import Template

from typing import Any

try:
    from jsonschema import validate # type: ignore
    def validate_json(data: dict[str, Any], schema: Path):
        with open(schema, "r") as f:
            validate(instance=data, schema=json.load(f))
except ImportError:
    def validate_json(data: dict[str, Any], schema: Path):
        pass

class Variant:
    def __init__(self, name: str, workspace_dir: Path, data: dict[str, Any]) -> None:
        self._name = name
        self._path: Path = Path()
        self._alias: list[str] = []
        self._inherits = ""

        for k, v in data.items():
            attr_name = f"_{k}"
            if not hasattr(self, attr_name):
                continue
            attr = getattr(self, attr_name)
            value_type = type(v)
            if isinstance(attr, Path) and isinstance(v, str):
                setattr(self, attr_name, workspace_dir / Path(v))
            elif type(attr) == value_type:
                setattr(self, attr_name, v)

        if self.inherits == self.name or self.inherits in self.alias:
            self._inherits = ""

    @property
    def name(self): return self._name
    @property
    def alias(self): return self._alias
    @property
    def path(self): return self._path
    @property
    def inherits(self): return self._inherits;

    @property
    def files(self): return (p for p in self._path.rglob("*") if p.is_file())

class Workspace(Template):
    def __init__(self, name: str, path: Path) -> None:
        super().__init__(name=name, path=path, description="")
        self._default: str = ""
        self._variants: list[Variant] = []

        self._get_workspace_info()


    def _get_workspace_info(self):
        data: dict[str, Any] = {}
        with open(self._path / "meta.json", "r") as f:
            data = json.load(f)
            validate_json(data=data, schema=Workspace.TEMPLATE_ROOT / "schemas" / "template.json")

        for k, v in data.items():
            attr_name = f"_{k}"
            if hasattr(self, attr_name) and isinstance(getattr(self, attr_name), str) and isinstance(v, str):
                setattr(self, attr_name, v)

        variants: dict[str, Any] = data["variants"]
        for name, v in variants.items():
            var = Variant(name, self._path, v)
            if not var.path.is_dir() or len(list(var.files)) == 0:
                print(f"WARN: ignoring {self._name}:{name} because it's not a directory or contains no file", file=stderr)
                continue
            self._variants.append(var)

        if not self._default:
            return
        try:
            self.get_variant(self._default)
        except RuntimeError:
            raise InvalidConfiguration(f"{self._name}: invalid default variant")

    def get_variant(self, name: str | None):
        if name is None:
            name = self.default
        for v in self._variants:
            if name == v.name or name in v.alias:
                return v
        raise RuntimeError(f"{self._name}: variant with name '{name}' does not exist")

    @property
    def variants(self): return self._variants
    @property
    def default(self): return self._default

    def _get_files_impl(self, variant: str | Variant | None = None, level: int = 0):
        if not variant:
            variant = self._default;
        if not variant:
            raise RuntimeError(f"{self._name}: template has no default variant")

        if not isinstance(variant, Variant):
            variant = self.get_variant(variant)

        file_record: dict[Path, Path] = {}
        for f in variant.files:
            file_record[f.relative_to(variant.path)] = f

        if not variant.inherits or level >= 5:
            return (variant, file_record)

        try:
            parent, files = self._get_files_impl(variant.inherits, level + 1)
            for _, f in files.items():
                rel_path = f.relative_to(parent.path)
                if not rel_path in file_record:
                    file_record[rel_path] = f
        except RuntimeError:
            pass
        return (variant, file_record)

    def get_files(self, variant: str | Variant | None = None):
        _, files = self._get_files_impl(variant)
        return (files, max([len(str(f)) for f in files]))

    def create_workspace(self, path: Path | str, variant: str | Variant | None = None, *, verbose: bool = False, dry_run: bool = False):
        if not isinstance(path, Path):
            path = Path(path)
        if path.exists() and not path.is_dir():
            raise RuntimeError(f"{self._name}: failed to create workspace, '{path}' is not a directory")

        verbose = verbose or dry_run

        files, max_len = self.get_files(variant)
        for rel_path, f in files.items():
            target = path / rel_path
            if not dry_run:
                (path / rel_path.parent).mkdir(parents=True, exist_ok=True)
                copy_file(f, target)
            if verbose:
                print(f"  {str(rel_path):<{max_len}} -> {target}")



