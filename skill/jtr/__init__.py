"""JTR Generator - JIS規格準拠の日本の履歴書PDF生成パッケージ"""

from .pdf_generator import generate_resume_pdf
from .resume_data import load_resume_data

__all__ = ["generate_resume_pdf", "load_resume_data"]
