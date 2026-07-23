"""Schema definitions for all 15 test types."""
from fastapi import APIRouter

from ..services.params import TEST_TYPES

router = APIRouter(prefix="/api/test-types", tags=["test-types"])


@router.get("")
async def get_test_types():
    """Return all test type definitions with parameter schemas."""
    return TEST_TYPES
