from .groups.cache.g_manifest import g_manifest
from .init import initialize
from .prune import prune_store
from .run import run
from .show_langs import show_langs
from .show_resources import show_resources


COMMANDS = [
    show_langs,
    show_resources,
    initialize,
    prune_store,
    g_manifest,
    run
]
