from typing import Any

from sqlalchemy.types import UserDefinedType


class LtreeType(UserDefinedType[str]):
    """Maps to Postgres LTREE. Stored and returned as plain str paths."""

    cache_ok = True

    def get_col_spec(self, **kw: Any) -> str:
        return "LTREE"
