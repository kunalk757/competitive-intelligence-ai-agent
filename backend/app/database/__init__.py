from app.database.supabase_client import news_repository, SupabaseNewsRepository
from app.database.company_repository import company_repository, CompanyRepository

__all__ = [
    "news_repository",
    "SupabaseNewsRepository",
    "company_repository",
    "CompanyRepository",
]

