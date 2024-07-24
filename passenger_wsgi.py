import importlib.util
import importlib.machinery
import os
import sys


sys.path.insert(0, os.path.dirname(__file__))

# https://discuss.python.org/t/how-do-i-migrate-from-imp/27885/12
# https://docs.python.org/3.12/whatsnew/3.12.html
def load_source(modname, filename):
    loader = importlib.machinery.SourceFileLoader(modname, filename)
    spec = importlib.util.spec_from_file_location(modname, filename, loader=loader)
    module = importlib.util.module_from_spec(spec)
    # The module is always executed and not cached in sys.modules.
    # Uncomment the following line to cache the module.
    # sys.modules[module.__name__] = module
    loader.exec_module(module)
    return module


wsgi = load_source('wsgi', 'src/main.py')
application = wsgi.app
