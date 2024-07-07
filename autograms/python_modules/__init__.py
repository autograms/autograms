import pkgutil
import importlib


__path__ = pkgutil.extend_path(__path__, __name__)
submodules = {}


for loader, module_name, is_pkg in pkgutil.walk_packages(__path__, __name__ + '.'):
    if is_pkg:
        module = importlib.import_module(module_name)
        submodule_name = module_name.split('.')[-1]
        submodules[submodule_name] = module