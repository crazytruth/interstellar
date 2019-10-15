from importlib import import_module


def load_class(kls):
    parts = kls.rsplit('.', 1)
    m = import_module(parts[0])
    return getattr(m, parts[-1])
