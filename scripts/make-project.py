from pathlib import Path
import shutil
from sys import stderr
from shutil import copy2 as copy_file
from abc import ABC, abstractmethod
from dataclasses import dataclass
import json, re

from typing import Generator, Mapping, NoReturn, override

class Template(ABC):
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

    @abstractmethod
    def brief(self, **align_args) -> str:
        pass

    @abstractmethod
    def detail(self, **align_args) -> str:
        pass

class InvalidConfiguration(RuntimeError): ...


from typing import Any

try:
    from jsonschema import validate # type: ignore
    def validate_json(data: dict[str, Any], schema: Path):
        with open(schema, "r") as f:
            validate(instance=data, schema=json.load(f))
except ImportError:
    def validate_json(data: dict[str, Any], schema: Path):
        pass

@dataclass
class FileInfo:
    directory: Path
    file: Path

    @property
    def full_path(self):
        return self.directory / self.file

    @property
    def workspace_path(self):
        return self.directory.name / self.file

class VariantInfo:
    def __init__(self, name: str, workspace_dir: Path, *, path: Path | str, alias: list[str] | None = None, inherits: str = "", **extra) -> None:
        self._name = name
        self._workspace_dir = workspace_dir
        self._path: Path = Path(path)
        self._alias: list[str] = alias or []
        self._inherits = inherits
        self._extra = extra

        if self.inherits == self.name or self.inherits in self.alias:
            self._inherits = ""

    @property
    def name(self): return self._name
    @property
    def alias(self): return self._alias
    @property
    def path(self): return self._path
    @property
    def full_path(self): return self._workspace_dir / self.path
    @property
    def inherits(self): return self._inherits

    @property
    def raw_files(self):
        for f in self.full_path.rglob("*"):
            if not f.is_file():
                continue
            yield FileInfo(directory=self.full_path, file=f.relative_to(self.full_path))

    def brief(self, *, name_align: int = 0, path_align: int = 0):
        rel_path = f"{self._workspace_dir.name}/{self.path.name:<{path_align}}"
        alias_str = self.alias and f"({','.join(self.alias)})" or ""
        return f"{self.name:<{name_align}} {rel_path} {alias_str}"

class Workspace(Template):
    def __init__(self, name: str, path: Path, schema: Path | None) -> None:
        super().__init__(name=name, path=path, description="")
        self._default: str = ""
        self._variants: list[VariantInfo] = []
        self._schema = schema
        self._project_file_patterns: list[str] = []
        self._delete_marker: str = ".#delete"

        self._get_workspace_info()

    def _get_workspace_info(self):
        data: dict[str, Any] = {}
        if self._schema and self._schema.is_file():
            with open(self.path / "meta.json", "r") as f:
                data = json.load(f)
                validate_json(data=data, schema=self._schema)

        for k, v in data.items():
            attr_name = f"_{k}"
            if not hasattr(self, attr_name):
                continue
            attr = getattr(self, attr_name)
            if isinstance(attr, str) and isinstance(v, str):
                setattr(self, attr_name, v)
            elif isinstance(attr, list) and isinstance(v, list):
                setattr(self, attr_name, v)

        if not self._delete_marker:
            self._delete_marker = ".#delete"

        if not self._delete_marker.startswith("."):
            self._delete_marker = f".{self._delete_marker}"

        variants: dict[str, Any] = data["variants"]
        for name, v in variants.items():
            var = VariantInfo(name, self.path, **v)
            if not var.full_path.is_dir() or len(list(var.raw_files)) == 0:
                print(f"WARN: ignoring {self._name}:{name} because it's not a directory or contains no file", file=stderr)
                continue
            self._variants.append(var)

        if not self.default:
            return
        try:
            self.get_variant(self._default)
        except RuntimeError:
            self._default = ""
            raise InvalidConfiguration(f"{self._name}: invalid default variant")

    def get_variant(self, name: str | None):
        if name is None:
            name = self.default
        for v in self.variants:
            if name == v.name or name in v.alias:
                return v
        raise RuntimeError(f"{self._name}: variant with name '{name}' does not exist")

    @property
    def variants(self): return self._variants
    @property
    def default(self): return self._default

    @override
    def brief(self, *, name_align: int = 0, path_align: int = 0, **_):
        return f"{self.name:<{name_align}} {self.path.name:<{path_align}} ({','.join(v.name for v in self.variants)})"

    @override
    def detail(self, **align_args):
        return "\n".join([
            f"[{type(self).__name__}]: {self.name}\n",
            f"{self.title}",
            f"{self.description or '<No Description>'}\n",
            f"path:",
            f"  {self.path.parent.name}/{self.path.name}\n",
            f"variants:",
        ] + [ f"{v.name == self.default and ' *' or '  '}{v.brief(**align_args)}" for v in self.variants ])

    def variant_detail(self, variant: str | None = None):
        var = self.get_variant(variant)
        lines: list[str] = [ f"[{type(self).__name__} Variant]: {self.name}:{var.name}\n", ]
        if var.alias:
            lines += [
                f"alias:",
                f"{'\n'.join([f'  {v}' for v in var.alias])}\n",
            ]
        lines += [
            f"path:",
            f"  {self.path.parent.name}/{self.path.name}/{var.path}\n",
            f"files:",
            f"{'\n'.join([f'  {f.directory.name}/{f.file}' for f in self.get_files(var)])}"
        ]
        return "\n".join(lines)

    def _get_files_impl(
        self,
        variant: str | VariantInfo | None = None, level: int = 0
    ) -> Generator[FileInfo, None, None]:
        if not variant:
            variant = self._default;
        if not variant:
            raise RuntimeError(f"{self._name}: template has no default variant")

        if not isinstance(variant, VariantInfo):
            variant = self.get_variant(variant)

        seen_file: set[Path] = set()
        if level > 5:
            print(f"WARN: workspace variant inheritance reached maximum depth, there may be a loop")
            return

        for file in variant.raw_files:
            if file.file.suffix == self._delete_marker:
                seen_file.add(file.file.with_suffix(""))
            else:
                seen_file.add(file.file)
                yield file

        if not variant.inherits:
            return

        try:
            for file in self._get_files_impl(variant.inherits, level + 1):
                if file.file in seen_file:
                    continue
                yield file
        except RuntimeError:
            pass

    def get_files(self, variant: str | VariantInfo | None = None):
        return self._get_files_impl(variant)

    def create_workspace(self, path: Path | str, variant: str | VariantInfo | None = None, *, project_name: str | None = None, verbose: bool = False, dry_run: bool = False):
        if not isinstance(path, Path):
            path = Path(path)
        if path.exists() and not path.is_dir():
            raise RuntimeError(f"{self._name}: failed to create workspace, '{path}' is not a directory")

        if not project_name:
            project_name = path.name

        verbose = verbose or dry_run

        files: list[FileInfo]= []
        max_len = 0
        for f in self.get_files(variant):
            max_len = max(len(str(f.file)), max_len)
            files.append(f)

        for f in files:
            target = path / str(f.file).replace(f"#{self.name}#", project_name)
            if dry_run:
                print(f"  {str(f.file):<{max_len}} -> {target}")
                continue

            target.parent.mkdir(parents=True, exist_ok=True)
            copy_file(f.full_path, target)

            try:
                for pattern in self._project_file_patterns:
                    if not re.search(pattern, target.name):
                        continue

                    with open(target, "r", encoding="utf-8") as fs:
                        buf = fs.read()
                    with open(target, "wt+", encoding="utf-8") as fs:
                        fs.write(buf.replace(f"#{self.name}#", project_name))
                    break
            except:
                print(f"WARN:", file=stderr)


            if verbose:
                print(f"  {str(f.file):<{max_len}} -> {target}")

class Config(Template):
    def __init__(self, name: str, path: Path, title: str | None = None, description: str | None = None) -> None:
        super().__init__(name, path, title, description)

    @property
    def files(self):
        return (f for f in self.path.rglob("*") if f.is_file())

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

    @override
    def brief(self, *, name_align: int = 0, path_align: int = 0, **_) -> str:
        return f"{self.name:<{name_align}} {self.path.name:<{path_align}}"

    @override
    def detail(self, **_) -> str:
        return "\n".join([
            f"[{type(self).__name__}]: {self.name}\n",
            f"{self.title}",
            f"{self.description or '<No Description>'}\n",
            f"path:",
            f"  {self.path.parent.name}/{self.path.name}\n",
            f"files:",
        ] + [ f"  {self.path.name}/{f.name}" for f in self.files ])


def get_workspaces(root: Path, name_pattern: str, schema: Path | None = None):
    """
    get workspace templates from given path

    :param name_match: regex expression to match directory name, must contain at least one capture group
    """
    ret: dict[str, Workspace] = {}
    for dir in root.iterdir():
        if not dir.is_dir():
            continue
        match = re.search(name_pattern, dir.name)
        if not match: continue

        name = match.group(1)
        ret[name] = Workspace(name, dir.absolute(), schema)

    return ret

def get_configs(root: Path, name_pattern: str):
    """
    get config templates from given path

    :param name_match: regex expression to match directory name, must contain at least one capture group
    """
    ret: dict[str, Config] = {}
    for dir in root.iterdir():
        if not dir.is_dir():
            continue

        match = re.search(name_pattern, dir.name)
        if not match: continue

        name = match.group(1)
        ret[name] = Config(name, dir.absolute())

    return ret


def parse_cmd_args():
    from argparse import ArgumentParser

    parser = ArgumentParser(description="Create a new project from a template")
    required_group = parser.add_mutually_exclusive_group(required=True)

    required_group.add_argument(
        "name", type=str,
        nargs="?",
        help="the name of the project"
    )
    required_group.add_argument(
        "-l", "--list", type=str,
        nargs="?",
        const="all", default=None,
        help="list available templates and configs",
        metavar="NAME"
    )

    parser.add_argument(
        "-p", "--path", type=Path,
        default=Path.cwd(),
        help="the path to create the project in, if path does not exists it will be created"
    )
    parser.add_argument(
        "-t", "--template", type=str,
        help="the template to create, the format is name:variant, if variant is omitted, default is used"
    )
    parser.add_argument(
        "-c", "--config", type=str,
        help="the config to use"
    )
    parser.add_argument(
        "--always-nest", action="store_true",
        help="create project in subfolder even if project name matches path name"
    )

    parser.add_argument(
        "-V", "--verbose", action="store_true",
        default=False,
        help=""
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        default=False,
        help=""
    )

    @dataclass
    class Args:
        always_nest: bool
        template: str
        variant: str | None
        config: str | None

        path: Path
        name: str

        verbose: bool = False
        dry_run: bool = False

    args = parser.parse_args()

    if args.list:
        lst: str = args.list
        return lst

    if not args.template:
        parser.error("argument -t/--template is required")
    template_info: list[str] = args.template.split(":")

    ret = Args(
        always_nest=args.always_nest,
        template=template_info[0],
        variant=template_info[1] if len(template_info) > 1 else None,
        config=args.config,
        path=args.path,
        name=args.name,
        dry_run=args.dry_run,
        verbose=args.verbose
    )
    return ret

if __name__ == "__main__":
    def error_exit(*args, code: int = 1, **kwargs) -> NoReturn:
        kwargs["file"] = stderr
        print(*args, **kwargs)
        exit(code)

    def is_empty_dir(path: Path) -> bool:
        path = Path(path)
        if not path.exists():
            return True
        return next(path.iterdir(), None) is None

    def query_yes_no(question: str, default: bool | None = True):
        if default is None:
            prompt = "[y/n]"
        elif default == True:
            prompt = "[Y/n]"
        elif default == False:
            prompt = "[y/N]"
        else:
            raise ValueError(f"invalid default answer: \"{default}\"")

        try:
            while True:
                print(f"{question} {prompt} ", end="")
                choice = input().lower()
                if not choice and default is None:
                    print("Invalid response. Type \"yes\" or \"no\" (or \"y\" or \"n\").\n")
                    continue
                if not choice:
                    return default
                return choice in "yes"
        except:
            return False

    TEMPLATE_ROOT: Path = Path(__file__).parent.parent

    workspaces = get_workspaces(TEMPLATE_ROOT, r"(.+?)-workspace", TEMPLATE_ROOT / "schemas" / "template.json")
    configs = get_configs(TEMPLATE_ROOT, r"config\.(.+)")

    def list_templates(name: str):
        all_templates: dict[str, Mapping[str, Template]] = {
            "workspaces": workspaces,
            "configs": configs
        }
        align = { "name_align": 12, "path_align": 15 }
        if name == "all":
            print(f"template root: {TEMPLATE_ROOT}")
            for category, template_map in all_templates.items():
                print(f"\n{category}:")
                for _, t in template_map.items():
                    print(f"  {t.brief(**align)}")
            return

        try:
            template_name, variant_name = name.split(":")
        except ValueError:
            template_name, variant_name = name, None

        for _, template_map in all_templates.items():
            template = template_map.get(template_name, None)
            if isinstance(template, Workspace):
                print(variant_name and template.variant_detail(variant_name) or template.detail(**align))
                return
            if isinstance(template, Config):
                print(template.detail(**align))
                return

        raise RuntimeError(f"'{name}' is not known for any type of template")

    args = parse_cmd_args()

    if isinstance(args, str):
        try:
            list_templates(args)
        except RuntimeError as e:
            error_exit(f"ERROR: {e}")
        exit(0)

    template = workspaces.get(args.template)
    if not template:
        error_exit(f"ERROR: workspace template with name '{args.template}' does not exit")

    try:
        variant = template.get_variant(args.variant)
    except RuntimeError as e:
        error_exit(f"ERROR: {e}")

    if args.config and not args.config in configs:
        error_exit(f"ERROR: config template with name '{args.config}' does not exit")

    if args.always_nest or args.path.name != args.name:
        args.path /= args.name

    print(
                         f"Project Name: {args.name}\n",
                         f"Template: {workspaces[args.template].name}\n",
        args.variant and f"Variant:  {args.variant}\n" or "",
        args.config  and f"Config:   {configs[args.config].name}\n" or "",
        "\n",
        f"Creating project in {args.path.absolute()}",
        sep=""
    )

    if not is_empty_dir(args.path):
        print(f"WARN: {args.path} is not empty, files may be overwritten", file=stderr)
        if not query_yes_no("Do you want to continue?", default=False):
            print("Abort.", file=stderr)
            exit(0)

    print(f"INFO: Copying '{template.path.relative_to(TEMPLATE_ROOT)}'")
    template.create_workspace(args.path, variant=variant, verbose=args.verbose, dry_run=args.dry_run)

    if args.config and (config := configs.get(args.config)):
        print(f"INFO: Copying '{config.path.relative_to(TEMPLATE_ROOT)}'")
        config.copy_to_destination(args.path, verbose=args.verbose, dry_run=args.dry_run)

    print("Done.")
