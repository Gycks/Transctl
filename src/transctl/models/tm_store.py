import logging
import os
import time
from dataclasses import dataclass
from typing import Optional

from transctl.console_formater import ConsoleFormatter
from transctl.models.policies import PrunePolicy

from sqlalchemy import Engine, Integer, String, Text, create_engine, delete, func, select, text
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column


class Base(DeclarativeBase):
    pass


class TM(Base):
    __tablename__ = "tm"

    lang: Mapped[str] = mapped_column(String, primary_key=True)
    hash_: Mapped[str] = mapped_column(String, primary_key=True)

    translation: Mapped[str] = mapped_column(Text, nullable=False)

    created_at: Mapped[int] = mapped_column(Integer, nullable=False)
    last_used_at: Mapped[int] = mapped_column(Integer, nullable=False)


@dataclass
class TMStore:
    """
    Translation Memory Store.

    Attributes:
        db_path (str): The file path to the SQLite database.
    """

    db_path: str
    engine: Optional[Engine] = None

    def __post_init__(self) -> None:
        self.engine = create_engine(f"sqlite:///{self.db_path}", future=True)

        with self.engine.connect() as conn:
            conn.exec_driver_sql("PRAGMA journal_mode=WAL;")
            conn.exec_driver_sql("PRAGMA synchronous=NORMAL;")
            conn.exec_driver_sql("PRAGMA foreign_keys=ON;")
            conn.exec_driver_sql("PRAGMA auto_vacuum=INCREMENTAL;")
            conn.commit()

        Base.metadata.create_all(self.engine)

    @staticmethod
    def _now() -> int:
        return int(time.time())

    def lookup(self, session: Session, lang: str, hash_: str) -> Optional[str]:
        """
        Looks up a translation in the TM store by language and hash. If found, updates the last_used_at timestamp.

        Args:
            session (Session): An active SQLAlchemy session.
            lang (str): The target language code.
            hash_ (str): The hash of the source text.

        Returns:
            Optional[str]: The translation if found, otherwise None.
        """

        row = session.get(TM, {"lang": lang, "hash_": hash_})
        if not row:
            return None
        row.last_used_at = self._now()
        return row.translation

    def upsert(self, session: Session, lang: str, hash_: str, translation: str) -> None:
        """
        Inserts or updates a translation in the TM store. If an entry with the same language and hash already exists, it updates the translation and last_used_at timestamp. Otherwise, it creates a new entry.

        Args:
            session (Session): An active SQLAlchemy session.
            lang (str): The target language code.
            hash_ (str): The hash of the source text.
            translation (str): The translated text to store.
        """

        now = self._now()
        row = session.get(TM, {"lang": lang, "hash_": hash_})
        if row:
            row.translation = translation
            row.last_used_at = now
        else:
            session.add(
                TM(
                    lang=lang,
                    hash_=hash_,
                    translation=translation,
                    created_at=now,
                    last_used_at=now,
                )
            )

    def prune(self, session: Session, policy: PrunePolicy) -> None:
        """
        Prunes the Store based on the provided policy.
        
        Args:
            session (Session): An active SQLAlchemy session.
            policy (PrunePolicy): The pruning policy to apply.
        """

        logger: logging.Logger = logging.getLogger(__name__)
        logger.info(ConsoleFormatter.info("Pruning TM Store..."))

        should_prune = False

        # Condition A: db file too large
        if policy.max_db_mb is not None and os.path.exists(self.db_path):
            size_mb = os.path.getsize(self.db_path) / (1024 * 1024)
            if size_mb > policy.max_db_mb:
                should_prune = True

        # Condition B: row count too high (only compute if needed)
        row_count = None
        if policy.max_rows is not None:
            row_count = session.scalar(select(func.count()).select_from(TM)) or 0
            if row_count > policy.max_rows:
                should_prune = True

        # Condition C: TTL is set (we can prune expired entries each run, but only if any exist)
        # Cheap-ish check: do we have *any* expired entry?
        if policy.ttl_days is not None:
            cutoff = self._now() - policy.ttl_days * 24 * 3600
            expired_exists = session.scalar(
                select(func.count()).select_from(TM).where(TM.last_used_at < cutoff)
            )
            if expired_exists and expired_exists > 0:
                should_prune = True

        if not should_prune:
            logger.info(ConsoleFormatter.success("No matching policy found. Nothing to prune."))
            return 

        # ---- Run Pruning actions ----
        now = self._now()

        # 1) TTL prune
        if policy.ttl_days is not None:
            cutoff = now - policy.ttl_days * 24 * 3600
            session.execute(delete(TM).where(TM.last_used_at < cutoff))

        # 2) Enforce max rows (LRU)
        if policy.max_rows is not None:
            # recompute after TTL deletion
            row_count = session.scalar(select(func.count()).select_from(TM)) or 0
            if row_count > policy.max_rows:
                to_delete = row_count - policy.max_rows

                oldest = session.execute(
                    select(TM.lang, TM.hash_)
                    .order_by(TM.last_used_at.asc())
                    .limit(to_delete)
                ).all()

                for lang, hash_ in oldest:
                    session.execute(
                        delete(TM).where(TM.lang == lang, TM.hash_ == hash_)
                    )

        session.commit()

        # 3) Reclaim disk space
        if policy.vacuum:
            session.execute(text("PRAGMA incremental_vacuum;"))
            session.commit()

        logger.info(ConsoleFormatter.success("TM Store pruned successfully."))
