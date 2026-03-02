"""Initial projekty schema: servers, projects and child tables

Revision ID: 001
Revises:
Create Date: 2026-03-01 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# Identyfikatory rewizji — używane przez Alembic do śledzenia historii migracji
revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Tworzy schemat 'projekty' oraz 6 tabel w poprawnej kolejności (FK-safe)."""

    # Krok 0: Utwórz schemat PostgreSQL — musi istnieć przed tabelami
    op.execute("CREATE SCHEMA IF NOT EXISTS projekty")

    # Krok 1: Tabela serwerów — brak FK, tworzona jako pierwsza
    op.create_table(
        "servers",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("hostname", sa.String(length=255), nullable=False),
        sa.Column("server_type", sa.String(length=50), nullable=False),
        sa.Column("operating_system", sa.String(length=100), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("status", sa.String(length=50), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        schema="projekty",
    )
    # Indeksy dla tabeli servers
    op.create_index(
        op.f("ix_projekty_servers_id"), "servers", ["id"], unique=False, schema="projekty"
    )
    op.create_index(
        op.f("ix_projekty_servers_name"), "servers", ["name"], unique=True, schema="projekty"
    )

    # Krok 2: Tabela projektów — FK do servers, tworzona po servers
    op.create_table(
        "projects",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("code", sa.String(length=50), nullable=False),
        sa.Column("status", sa.String(length=50), nullable=False),
        sa.Column("owner_name", sa.String(length=255), nullable=True),
        sa.Column("owner_id", sa.String(length=255), nullable=True),
        sa.Column("problem_statement", sa.Text(), nullable=True),
        sa.Column("start_date", sa.Date(), nullable=True),
        sa.Column("end_date", sa.Date(), nullable=True),
        sa.Column("dev_server_id", sa.Integer(), nullable=True),
        sa.Column("prod_server_id", sa.Integer(), nullable=True),
        sa.Column("port_range_start", sa.Integer(), nullable=True),
        sa.Column("port_range_end", sa.Integer(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["dev_server_id"],
            ["projekty.servers.id"],
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["prod_server_id"],
            ["projekty.servers.id"],
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id"),
        schema="projekty",
    )
    # Indeksy dla tabeli projects
    op.create_index(
        op.f("ix_projekty_projects_id"), "projects", ["id"], unique=False, schema="projekty"
    )
    op.create_index(
        op.f("ix_projekty_projects_name"), "projects", ["name"], unique=False, schema="projekty"
    )
    op.create_index(
        op.f("ix_projekty_projects_code"), "projects", ["code"], unique=True, schema="projekty"
    )
    op.create_index(
        op.f("ix_projekty_projects_status"),
        "projects",
        ["status"],
        unique=False,
        schema="projekty",
    )
    op.create_index(
        op.f("ix_projekty_projects_owner_id"),
        "projects",
        ["owner_id"],
        unique=False,
        schema="projekty",
    )

    # Krok 3: Tabela KPI projektów — FK do projects
    op.create_table(
        "project_kpis",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("project_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("target_value", sa.String(length=255), nullable=False),
        sa.Column("current_value", sa.String(length=255), nullable=True),
        sa.Column("unit", sa.String(length=50), nullable=True),
        sa.ForeignKeyConstraint(
            ["project_id"],
            ["projekty.projects.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
        schema="projekty",
    )

    # Krok 4: Tabela technologii projektów — FK do projects
    op.create_table(
        "project_technologies",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("project_id", sa.Integer(), nullable=False),
        sa.Column("category", sa.String(length=50), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("version", sa.String(length=50), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(
            ["project_id"],
            ["projekty.projects.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
        schema="projekty",
    )

    # Krok 5: Tabela elementów zakresu projektów — FK do projects
    op.create_table(
        "project_scope_items",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("project_id", sa.Integer(), nullable=False),
        sa.Column("category", sa.String(length=50), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("priority", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(
            ["project_id"],
            ["projekty.projects.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
        schema="projekty",
    )

    # Krok 6: Tabela portów projektów — FK do projects
    op.create_table(
        "project_ports",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("project_id", sa.Integer(), nullable=False),
        sa.Column("port_number", sa.Integer(), nullable=False),
        sa.Column("protocol", sa.String(length=20), nullable=False),
        sa.Column("service_name", sa.String(length=255), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(
            ["project_id"],
            ["projekty.projects.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
        schema="projekty",
    )


def downgrade() -> None:
    """Usuwa wszystkie tabele ze schematu 'projekty' w odwrotnej kolejności (FK-safe)."""

    # Krok 6: Usuń tabele dzieci (od ostatniej do pierwszej)
    op.drop_table("project_ports", schema="projekty")
    op.drop_table("project_scope_items", schema="projekty")
    op.drop_table("project_technologies", schema="projekty")
    op.drop_table("project_kpis", schema="projekty")

    # Krok 2: Usuń indeksy i tabelę projects
    op.drop_index(
        op.f("ix_projekty_projects_owner_id"), table_name="projects", schema="projekty"
    )
    op.drop_index(
        op.f("ix_projekty_projects_status"), table_name="projects", schema="projekty"
    )
    op.drop_index(
        op.f("ix_projekty_projects_code"), table_name="projects", schema="projekty"
    )
    op.drop_index(
        op.f("ix_projekty_projects_name"), table_name="projects", schema="projekty"
    )
    op.drop_index(
        op.f("ix_projekty_projects_id"), table_name="projects", schema="projekty"
    )
    op.drop_table("projects", schema="projekty")

    # Krok 1: Usuń indeksy i tabelę servers
    op.drop_index(
        op.f("ix_projekty_servers_name"), table_name="servers", schema="projekty"
    )
    op.drop_index(
        op.f("ix_projekty_servers_id"), table_name="servers", schema="projekty"
    )
    op.drop_table("servers", schema="projekty")
