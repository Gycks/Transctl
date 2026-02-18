from typing import Optional

from pydantic import BaseModel


class PrunePolicy(BaseModel):
    """
    Policy for pruning the translation memory database.

    Attributes:
        ttl_days: The number of days after which a translation memory entry is considered stale and eligible for pruning.
        max_rows: The maximum number of rows allowed in the translation memory database.
        max_db_mb: The maximum size of the database in megabytes.
        vacuum: Whether to perform a VACUUM operation after pruning to reclaim space.
    """

    ttl_days: Optional[int] = 180
    max_rows: Optional[int] = 200_000
    max_db_mb: Optional[int] = 200
    vacuum: bool = True
