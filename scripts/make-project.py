
if __name__ != '__main__':
	raise ImportError('This script is not meant to be imported')

from pathlib import Path
from argparse import ArgumentParser
import shutil

TEMPLATE_ROOT = Path(__file__).parent.parent

configs: dict[str, Path] = {}
workspaces: dict[str, Path] = {}

for dir in TEMPLATE_ROOT.iterdir():
	if not dir.is_dir():
		continue
	if dir.match('config.*'):
		name = dir.name.split('.')[1]
		configs[name] = dir.absolute()
	elif dir.match('*-workspace'):
		name = dir.name.split('-')[0]
		workspaces[name] = dir.absolute()

def print_info():
	print("availible configs:")
	for key, p in configs.items():
		print('  ', key, p.relative_to(TEMPLATE_ROOT.parent))
	print()
	print("availible workspace templates:")
	for key, p in workspaces.items():
		print('  ', key, p.relative_to(TEMPLATE_ROOT.parent))


parser = ArgumentParser(description='Create a new project from a template')
required_group = parser.add_mutually_exclusive_group(required=True)


required_group.add_argument(
	'name', type=str,
	nargs='?',
	help='the name of the project'
)
required_group.add_argument(
	'-l', '--list', action='store_true',
	help='list available templates and configs'
)

parser.add_argument(
	'-p', '--path', type=Path,
	default=Path.cwd(),
	help='the path to create the project in, if path does not exists it will be created'
)
parser.add_argument(
	'-t', '--template', type=str,
	help='the template to create'
)
parser.add_argument(
	'-c', '--config', type=str,
	help='the config to use'
)
parser.add_argument(
	"--always-nest", action='store_true',
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

def is_empty_dir(path: Path) -> bool:
	path = Path(path)
	if not path.exists():
		return True
	return next(path.iterdir(), None) is None

def query_yes_no(question: str, default: bool | None = True):
	"""Ask a yes/no question via input() and return their answer.

	"question" is a string that is presented to the user.
	"default" is the presumed answer if the user just hits <Enter>.
			It must be "yes" (the default), "no" or None (meaning
			an answer is required of the user).

	The "answer" return value is True for "yes" or False for "no".
	"""

	if default is None:
		prompt = "[y/n]"
	elif default == True:
		prompt = "[Y/n]"
	elif default == False:
		prompt = "[y/N]"
	else:
		raise ValueError("invalid default answer: '%s'" % default)

	try:
		while True:
			print(f"{question} {prompt} ", end="")
			choice = input().lower()
			if not choice and default is None:
				print("Invalid response. Type 'yes' or 'no' " "(or 'y' or 'n').\n")
				continue
			if not choice:
				return default
			return choice in "yes"
	except:
		return False

always_nest: bool = args.always_nest
template: str = args.template
config: str = args.config
path: Path = Path(args.path).absolute()
name: str = args.name

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
if config:
	print(f"Using config:   {configs[config].name}")
print()
print(f"Creating project in {path}")

if not is_empty_dir(path):
	print(f"Warning: {path} is not empty, files may be overwritten")
	if not query_yes_no("Do you want to continue?", default=False):
		print("Abort.")
		exit(0)

def copy_dir(from_path: Path, to_path: Path, quiet: bool = False):
	if not quiet:
		print(f"{from_path.relative_to(TEMPLATE_ROOT.parent)} -> {to_path}")
	shutil.copytree(from_path, to_path, dirs_exist_ok=True)

copy_dir(workspaces[template], path)
copy_dir(configs[config],      path / f".{config}")

def ovewrite_template_name(path: Path):
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
					f.write(all_text.replace(workspaces[template].name, name))
		except UnicodeDecodeError:
			continue

ovewrite_template_name(path)
print("Done.")