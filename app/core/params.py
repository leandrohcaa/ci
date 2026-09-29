from typing import Annotated

from fastapi import Path

POSTGRES_INT_MAX = 2_147_483_647

PositiveId = Annotated[int, Path(gt=0, le=POSTGRES_INT_MAX)]
