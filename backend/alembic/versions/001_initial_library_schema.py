"""Initial library schema."""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "001_initial_library_schema"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "books",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(length=512), nullable=False),
        sa.Column("author", sa.String(length=512), nullable=True),
        sa.Column("source_filename", sa.String(length=1024), nullable=True),
        sa.Column("source_type", sa.String(length=16), nullable=False),
        sa.Column("page_count", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "chapters",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("book_id", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(length=512), nullable=False),
        sa.Column("sort_order", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["book_id"], ["books.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "text_chunks",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("chapter_id", sa.Integer(), nullable=False),
        sa.Column("chunk_index", sa.Integer(), nullable=False),
        sa.Column("text", sa.Text(), nullable=False),
        sa.ForeignKeyConstraint(["chapter_id"], ["chapters.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("chapter_id", "chunk_index", name="uq_text_chunks_chapter_index"),
    )
    op.create_table(
        "reading_progress",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("book_id", sa.Integer(), nullable=False),
        sa.Column("chapter_id", sa.Integer(), nullable=False),
        sa.Column("chunk_id", sa.Integer(), nullable=True),
        sa.Column("char_offset", sa.Integer(), nullable=False),
        sa.Column("voice", sa.String(length=64), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["book_id"], ["books.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["chapter_id"], ["chapters.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["chunk_id"], ["text_chunks.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("book_id", name="uq_reading_progress_book"),
    )
    op.create_table(
        "audio_cache_index",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("chunk_id", sa.Integer(), nullable=False),
        sa.Column("voice", sa.String(length=64), nullable=False),
        sa.Column("cache_path", sa.String(length=2048), nullable=True),
        sa.Column("object_key", sa.String(length=1024), nullable=True),
        sa.Column("file_size_bytes", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["chunk_id"], ["text_chunks.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("chunk_id", "voice", name="uq_audio_cache_chunk_voice"),
    )
    op.create_index("ix_audio_cache_object_key", "audio_cache_index", ["object_key"])


def downgrade() -> None:
    op.drop_index("ix_audio_cache_object_key", table_name="audio_cache_index")
    op.drop_table("audio_cache_index")
    op.drop_table("reading_progress")
    op.drop_table("text_chunks")
    op.drop_table("chapters")
    op.drop_table("books")
