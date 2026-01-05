from data_types.template import Template
from data_types.workspace_template import Workspace
from data_types.config_template import Config
from data_types.helpers import list_template, error_exit, is_empty_dir, query_yes_no

from sys import stderr
from pathlib import Path
from dataclasses import dataclass

Template.TEMPLATE_ROOT = Path(__file__).parent.parent


workspaces: dict[str, Workspace] = {}
configs: dict[str, Config] = {}

for dir in Template.TEMPLATE_ROOT.iterdir():
    if not dir.is_dir():
        continue
    if dir.match("config.*"):
        name = dir.name.split(".")[1]
        configs[name] = Config(name, dir.absolute())

    elif dir.match("*-workspace"):
        name = dir.name.split("-")[0]
        workspaces[name] = Workspace(name, dir.absolute())


def parse_args():
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
        list_template({
            "workspaces": workspaces,
            "configs": configs
        }, args.list)
        exit(0)

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

args = parse_args()

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

print(f"INFO: Copying '{template.path.relative_to(Template.TEMPLATE_ROOT)}'")
template.create_workspace(args.path, variant=variant, verbose=args.verbose, dry_run=args.dry_run)

if args.config and (config := configs.get(args.config)):
    print(f"INFO: Copying '{config.path.relative_to(Template.TEMPLATE_ROOT)}'")
    config.copy_to_destination(args.path, verbose=args.verbose, dry_run=args.dry_run)

print("Done.")
