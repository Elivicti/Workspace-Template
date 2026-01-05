from .template import Template
from .workspace_template import Workspace

from sys import stderr
from pathlib import Path
from typing import Callable, Any, Mapping, NoReturn

def truncate(s: str, max_len: int, postfix: str | None = "..."):
    if not s or len(s) <= max_len:
        return s
    return f"{s[0:max_len]}{postfix or ''}"

def print_templates(
    category: str,
    templates: Mapping[str, Template],
    *,
    extra_info_getter: Callable[[Template], tuple[Any, ...]] | None = None):
    print(f"{category}:")
    for key, t in templates.items():
        extra = ()
        if extra_info_getter:
            extra = extra_info_getter(t)
        print(
            "  ",
            f"{key:<10s}",
            f"{truncate(t.description, 25) or str(t.path.relative_to(Template.TEMPLATE_ROOT)):<15s}",
            *extra
        )

def print_single_template(all_templates: dict[str, Mapping[str, Template]], name: str, extra_info_getter: Callable[[Template], tuple[Any, ...]] | None = None):
    item: Template | None = None
    found_any_template = False
    for _, template_map in all_templates.items():
        item = template_map.get(name)
        if not item:
            continue
        found_any_template = True
        extra = ()
        if extra_info_getter:
            extra = extra_info_getter(item)
        print(
            f"[{type(item).__name__}]: {name}\n\n"
            f"{item.title}\n"
            f"{item.description or '<no description>'}\n\n"
            "path:\n"
            f"  {Template.TEMPLATE_ROOT.name}/{item.path.name}\n",
            *extra,
            end="",
            sep=""
        )

    if not found_any_template:
        raise RuntimeError(f"template with name \"{name}\" not found")

def get_detailed_extra_template_info(t: Template):
    extra: list[str] = []
    if isinstance(t, Workspace):
        extra.append("\n")
        extra.append("variants:\n")
        for v in t.variants:
            indent = (v.name == t.default) and " *" or "  "
            alias  =  v.alias and f" (alias: {','.join(v.alias)})" or ""
            extra.append(f"{indent}{v.name:<12s} {t.path.name}/{v.path.name:<15s}{alias}\n")

    return tuple(extra)

def get_extra_template_info(t: Template):
    if isinstance(t, Workspace):
        return (f"({','.join([v.name for v in t.variants ])})", )
    return ()


def list_template(all_templates: dict[str, Mapping[str, Template]], name: str):
    if name != "all":
        print_single_template(all_templates, name, get_detailed_extra_template_info)
        return

    print(f"template root: {Template.TEMPLATE_ROOT}", end="\n")
    for category, template_map in all_templates.items():
        print()
        print_templates(
            category, template_map,
            extra_info_getter=get_extra_template_info
        )

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
