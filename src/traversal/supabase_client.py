from __future__ import annotations

import os
from typing import Any

try:
    from dotenv import load_dotenv
except ImportError:
    def load_dotenv() -> bool:
        return False

try:
    from supabase import Client, create_client
except ImportError:
    Client = Any  # type: ignore[misc,assignment]

    def create_client(*_args: object, **_kwargs: object) -> Any:
        raise RuntimeError(
            "The 'supabase' package is not installed. Install project dependencies "
            "before using the Supabase integration."
        )


load_dotenv()


def get_supabase_client() -> Client:
    supabase_url = os.getenv("SUPABASE_URL")
    service_role_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

    if not supabase_url:
        raise RuntimeError(
            "Missing SUPABASE_URL. Create a .env file from .env.example and set it."
        )
    if not service_role_key:
        raise RuntimeError(
            "Missing SUPABASE_SERVICE_ROLE_KEY. Create a .env file from .env.example and set it."
        )

    return create_client(supabase_url, service_role_key)
