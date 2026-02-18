from pathlib import Path
import logging

from src.core.configuration_manager import ConfigurationManager
from src.utils.i_o import load_json
from src.utils.utils_suit import compute_hash
from src.models.translation_manifest import TranslationManifest, TREntry
from src.models.app_config import AppConfig
from src.utils.utils_suit import sanitize_path
from src.console_formater import ConsoleFormatter


class TranslationRunManifest:
    """
    Manage a cached JSON manifest of translation inputs and their computed output hashes.

    The manifest is stored as a JSON file inside the configured working directory (see ``ConfigurationManager.get_working_directory``).

    Thread-safety / concurrency
    - This class performs simple file reads/writes and does not provide cross-process
      locking. If multiple processes may update the manifest concurrently, external
      synchronization is required.

    Attributes
        _working_dir (Path): working directory returned by ConfigurationManager.
        _cache_dir (Path): full path to the manifest JSON file inside the working dir.
        _manifest (TranslationManifest | None): in-memory manifest; None if not loaded.
        _active_source (str): content-hash of the currently bound source (empty string if none).
        _active_source_details (TREntry | None): TREntry for the active source if present in manifest.
    """

    def __init__(self, cfg: ConfigurationManager):
        """
        Initialize the manifest manager and attempt to load the cached JSON file.
        """

        self.logger: logging.Logger = logging.getLogger(__name__)
        self.cfg: ConfigurationManager = cfg
        self._working_dir = cfg.get_working_directory()
        self._cache_dir = self._working_dir.joinpath("translation_manifest.json")
        self._manifest: TranslationManifest | None = None

        if self._cache_dir.exists():
            self._manifest = TranslationManifest.model_validate(load_json(self._cache_dir))

        self._active_source: str = ""
        self._active_source_details: TREntry | None = None

        self.update_required: bool = False

    def bind_source(self, origin_path: Path):
        """
        Bind a source file so subsequent validations refer to it.

        Args
            origin_path (Path): path to the source file to bind.

        Raises
            OSError: if the file cannot be read.
        """
        content: str = origin_path.read_text(encoding='utf-8')
        self._active_source = compute_hash(content)

        if self._manifest is None:
            return

        self._active_source_details = self._manifest.sources.get(self._active_source, None)

    def is_output_valid(self, target_path: Path) -> bool:
        """
        Return whether a given target file is valid for the currently bound source.

        A target is considered valid if all of the following are true:
        - A source has been bound via :meth:`bind_source` and that source exists in the
          loaded manifest (``_active_source_details`` is not ``None``).
        - ``target_path`` exists on disk and is readable.
        - The computed hash of the target's content equals the expected hash recorded
          in the active source's TREntry.outputs mapping.

        Args
            target_path (Path): path to the target/translated file to validate.

        Returns
            bool: True if the file exists and its content hash matches the expected
            value from the manifest for the active source; False otherwise.
        """
        if self._active_source_details is None:
            return False

        if not target_path.exists():
            return False

        content: str = target_path.read_text(encoding='utf-8')
        return compute_hash(content) == self._active_source_details.outputs.get(str(target_path), None)

    def _write_manifest(self, manifest: TranslationManifest):
        """
        Persist a TranslationManifest to the configured cache file as JSON.

        Args
            manifest (TranslationManifest): manifest instance to serialize and save.

        Side effects
            - Overwrites the file at ``self._cache_dir`` with the JSON representation
              of ``manifest``.

        Raises
            OSError: if the file cannot be written.
        """

        self._cache_dir.write_text(manifest.model_dump_json(indent=2), encoding="utf-8")

    def rebuild_from_config(self, force: bool = False):
        """
        Build a new manifest from an application configuration and persist it.

        Walks configured resources in ``config`` and for each resource collects the
        current source file content hash and the hashes of any existing target files
        for the configured ``targets`` languages. Only files that exist on disk are
        included (missing files are skipped).

        Parameters
            config (AppConfig): application configuration containing resources and
                targets. If ``config.resources`` is falsy, the method does nothing.

        Side effects
            - Writes the newly built manifest to disk using :meth:`_write_manifest`.
        """

        self.logger.info(ConsoleFormatter.info("Building translation manifest..."))

        if not self.update_required and not force:
            self.logger.info(ConsoleFormatter.success("Success."))
            return

        new_manifest = TranslationManifest(version=1, sources={})

        if not self.cfg.configuration.resources:
            self.logger.info(ConsoleFormatter.success("Success."))
            return

        targets = list(self.cfg.configuration.targets or [])
        for _, resources in self.cfg.configuration.resources.items():
            for resource in resources:
                tag = resource.tag
                for input_path, output_path in resource.bucket:
                    input_path = Path(input_path)
                    if not input_path.exists():
                        continue

                    # source hash
                    source_content = input_path.read_text(encoding="utf-8")
                    source_hash = compute_hash(source_content)

                    # ensure entry
                    entry = new_manifest.sources.get(source_hash)
                    if entry is None:
                        entry = TREntry(source_path=str(input_path), outputs={})
                        new_manifest.sources[source_hash] = entry

                    # lazy output ("expected") computation
                    for lang in targets:
                        out_path = Path(sanitize_path(str(output_path), tag, lang))
                        if not out_path.exists():
                            continue

                        out_content = out_path.read_text(encoding="utf-8")
                        entry.outputs[str(out_path)] = compute_hash(out_content)

        self._write_manifest(new_manifest)
        self.logger.info(ConsoleFormatter.success("Success."))

    def purge(self) -> None:
        """
        Clear the manifest by writing an empty manifest (version 1) to disk.
        """

        self.logger.warning(ConsoleFormatter.warning("Purging translation manifest..."))

        empty = TranslationManifest(version=1, sources={})
        self._write_manifest(empty)

        self.logger.info(ConsoleFormatter.success("Translation manifest purged successfully."))
