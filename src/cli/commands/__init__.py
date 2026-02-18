from .show_langs import show_langs
from .show_resources import show_resources
from .init import initialize
from .prune import prune_store
from .groups.cache.g_manifest import g_manifest
from .run import run


COMMANDS = [
    show_langs,
    show_resources,
    initialize,
    prune_store,
    g_manifest,
    run
]
