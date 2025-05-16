from pathlib import Path
from typing import Optional, Iterable, Any
import shutil

def is_empty_dir(path: Path) -> bool:
	path = Path(path)
	if not path.exists():
		return True
	return next(path.iterdir(), None) is None

class InvalidConfiguration(RuntimeError):
	pass

class Variant:
	def __init__(self, name: str, path: Path, alias: Optional[set[str]] = None):
		if alias and not isinstance(alias, set):
			alias = set(alias)

		self.name  = str(name)
		self.path_ = Path(path)
		self.alias = alias or set()
		self.root_path = Path(".")

	@property
	def names(self):
		return { self.name }.union(self.alias)
	@property
	def path(self):
		return self.root_path / self.path_

	def copy_to(self, path: Path, overwrite_non_empty=False):
		if not overwrite_non_empty and not is_empty_dir(path):
			raise RuntimeError(f"attemping to overwrite non empty directory: {path}")
		shutil.copytree(self.path, path, dirs_exist_ok=True)

class Template:
	def __init__(
		self,
		name: str,
		path: Path,
		default: str,
		variants: Iterable[Variant] | dict[str, Any],
		title: Optional[str] = None,
		description: Optional[str] = None,
	):
		self.name     = str(name)
		self.path     = Path(path)
		self.default  = str(default)
		self.variants: dict[str, Variant] = {}
		self.title       = title or self.name
		self.description = description or ""

		if isinstance(variants, dict):
			vars = [Variant(k, **v) for k, v in variants.items()]
			variants = vars

		self._make_variants(variants)
		self._check_variants()

	def _make_variants(self, variants: Iterable[Variant]):
		for variant in variants:
			variant.root_path = self.path
			self.variants[variant.name] = variant
			if not variant.path.is_dir():
				raise InvalidConfiguration(
					f"{variant.path} is not a directory"
				)

	def _check_variants(self):
		if len(self.variants) < 1:
			raise InvalidConfiguration(
				"workspace must have at lease one variant"
			)
		if not self.default in self.variants:
			raise InvalidConfiguration(
				f"""invalid default, expecting any of [{
					",".join(self.variants.keys())
				}], got \"{self.default}\""""
			)

	def get_variant(self, key: Optional[str]):
		if not key:
			return self.default_variant
		if v := self.variants.get(key):
			return v
		for _, v in self.variants.items():
			if key in v.names:
				return v
		raise RuntimeError(f"variant \"{key}\" not found")

	@property
	def default_variant(self):
		return self.variants[self.default]



if __name__ != "__main__":
	raise ImportError("this script is not meant to be imported")

HAS_JSONSCHEMA = True
try:
	from jsonschema import validate
except ImportError:
	HAS_JSONSCHEMA = False

def validate_json(data: dict[str, Any], schema: Path):
	if not HAS_JSONSCHEMA:
		return
	with open(schema, "r") as f:
		validate(instance=data, schema=json.load(f))

from argparse import ArgumentParser
import json

def make_template(var: dict[str, Any], name: str, path: Path):
	meta_file = path / "meta.json"
	if meta_file.exists():
		with open(meta_file, "r") as f:
			data: dict[str, Any] = json.load(f)
			schema = Path(data.pop("$schema"))
			validate_json(data, path / schema)
	else:
		data: dict[str, Any] = {
			"default": name,
			"variants": {
				name: { "path": path }
			}
		}
	var[name] = Template(
		name=name,
		path=dir.absolute(),
		**data
	)

TEMPLATE_ROOT = Path(__file__).parent.parent

configs: dict[str, Template] = {}
workspaces: dict[str, Template] = {}

for dir in TEMPLATE_ROOT.iterdir():
	if not dir.is_dir():
		continue
	if dir.match("config.*"):
		name = dir.name.split(".")[1]
		make_template(configs, name, dir.absolute())
	elif dir.match("*-workspace"):
		name = dir.name.split("-")[0]
		make_template(workspaces, name, dir.absolute())

def truncate(s: str, max_len: int, postfix: Optional[str] = "..."):
	if not s or len(s) <= max_len:
		return s
	return f"{s[0:max_len]}{postfix or ''}"

def print_info():
	def p_info(name: str, data: dict[str, Template], newline="\n"):
		print(name)
		for key, t in data.items():
			print(
				"  ",
				f"{key:<10s}",
				f"{truncate(t.description, 25) or str(t.path.relative_to(TEMPLATE_ROOT)):<15s}",
				f"({','.join(t.variants)})"
			)
		print(newline, end="")

	print(f"template root: {TEMPLATE_ROOT}", end="\n\n")
	p_info("configs:",    configs)
	p_info("workspaces:", workspaces, newline="")


parser = ArgumentParser(description="Create a new project from a template")
required_group = parser.add_mutually_exclusive_group(required=True)


required_group.add_argument(
	"name", type=str,
	nargs="?",
	help="the name of the project"
)
required_group.add_argument(
	"-l", "--list", action="store_true",
	help="list available templates and configs"
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

args = parser.parse_args()

if args.list:
	print_info()
	exit(0)

def check_template(template_name: str | None):
	if not template_name:
		parser.error("argument -t/--template is required")
	if not template_name in workspaces.keys():
		parser.error(f"{template_name} is not a valid workspace template")
def check_config(config_name: str | None):
	if not config_name:
		return
	if not config_name in configs.keys():
		parser.error(f"{config_name} is not a valid config")
def check_path(path: Path):
	if path.exists() and not path.is_dir():
		parser.error(f"{path.absolute()} is not a directory")

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

always_nest: bool = args.always_nest
template: str = args.template
variant: str = None

config: str = args.config
path: Path = Path(args.path).absolute()
name: str = args.name

try:
	template, variant = template.split(":")
except ValueError:
	pass

check_template(template)
check_config(config)
check_path(path)

# print("-------------------------------")
# print(f"{Path.cwd()}")
# print(args)
# print("-------------------------------\n")

if name != path.name or always_nest:
	path = path / name

print(f"Project name:   {name}")
print(f"Using template: {workspaces[template].name}")
if variant:
	print(f"Using variant:  {variant}")
if config:
	print(f"Using config:   {configs[config].name}")
print()
print(f"Creating project in {path}")

if not is_empty_dir(path):
	print(f"Warning: {path} is not empty, files may be overwritten")
	if not query_yes_no("Do you want to continue?", default=False):
		print("Abort.")
		exit(0)

def copy_dir(var: Variant, to_path: Path, quiet: bool = False):
	if not quiet:
		print(f"{var.path.relative_to(TEMPLATE_ROOT.parent)} -> {to_path}")
	var.copy_to(to_path, overwrite_non_empty=True)

copy_dir(workspaces[template].get_variant(variant), path)
if config:
	copy_dir(configs[config].default_variant, path / f".{config}")

def ovewrite_template_name(path: Path):
	if path.name.startswith("."):
		return
	for file in path.iterdir():
		if file.is_dir():
			ovewrite_template_name(file)
		if not file.is_file():
			continue
		try:
			with open(file, "r+t") as f:
				all_text = f.read()
				if workspaces[template].name in all_text:
					f.seek(0)
					f.truncate()
					f.write(all_text.replace(
						f"#{workspaces[template].name}#",
						name
					))
		except UnicodeDecodeError:
			continue

ovewrite_template_name(path)
print("Done.")