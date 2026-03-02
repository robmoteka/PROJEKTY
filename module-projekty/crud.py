"""
Operacje CRUD dla modułu Projekty.

Każda funkcja przyjmuje sesję SQLAlchemy jako pierwszy argument —
zarządzanie sesją (commit/rollback) należy do wywołującego (endpoint FastAPI).
Wzorzec identyczny z module-issues/crud.py.
"""

from __future__ import annotations

from sqlalchemy.orm import Session, joinedload

from models import Project, ProjectKPI, ProjectPort, ProjectScopeItem, ProjectTechnology, Server
from schemas import (
    KPICreate,
    KPIUpdate,
    PortCreate,
    PortUpdate,
    ProjectCreate,
    ProjectUpdate,
    ScopeItemCreate,
    ScopeItemUpdate,
    ServerCreate,
    ServerUpdate,
    TechnologyCreate,
    TechnologyUpdate,
)

# ---------------------------------------------------------------------------
# CRUD Serwerów
# ---------------------------------------------------------------------------


def get_servers(
    db: Session,
    skip: int = 0,
    limit: int = 50,
    server_type: str | None = None,
    status: str | None = None,
) -> list[Server]:
    """
    Pobiera listę serwerów z opcjonalnym filtrowaniem po typie i statusie.

    Args:
        db: Sesja SQLAlchemy przekazana przez FastAPI Depends.
        skip: Liczba rekordów do pominięcia (offset paginacji).
        limit: Maksymalna liczba zwracanych rekordów.
        server_type: Opcjonalny filtr — zwraca tylko serwery danego typu.
        status: Opcjonalny filtr — zwraca tylko serwery o podanym statusie.

    Returns:
        Lista obiektów Server spełniających kryteria.
    """
    # Budujemy zapytanie bazowe — sortujemy alfabetycznie po nazwie
    query = db.query(Server).order_by(Server.name)
    # Stosujemy filtr typu serwera jeśli podany
    if server_type is not None:
        query = query.filter(Server.server_type == server_type)
    # Stosujemy filtr statusu jeśli podany
    if status is not None:
        query = query.filter(Server.status == status)
    return query.offset(skip).limit(limit).all()


def get_server_by_id(db: Session, server_id: int) -> Server | None:
    """
    Pobiera serwer po ID.

    Args:
        db: Sesja SQLAlchemy.
        server_id: Identyfikator serwera.

    Returns:
        Obiekt Server lub None jeśli nie istnieje.
    """
    return db.query(Server).filter(Server.id == server_id).first()


def create_server(db: Session, server_data: ServerCreate) -> Server:
    """
    Tworzy nowy serwer w bazie danych.

    Args:
        db: Sesja SQLAlchemy.
        server_data: Zwalidowane dane wejściowe z formularza/API.

    Returns:
        Nowo utworzony obiekt Server z wypełnionym ID.
    """
    # Tworzymy obiekt modelu — konwertujemy enumy do wartości string
    db_server = Server(
        name=server_data.name,
        hostname=server_data.hostname,
        server_type=server_data.server_type.value,
        operating_system=server_data.operating_system,
        description=server_data.description,
        status=server_data.status.value,
    )
    db.add(db_server)
    db.commit()
    # Odświeżamy obiekt, żeby pobrać wygenerowane wartości (id, created_at, updated_at)
    db.refresh(db_server)
    return db_server


def update_server(db: Session, server_id: int, server_data: ServerUpdate) -> Server | None:
    """
    Aktualizuje serwer — partial update (tylko podane pola).

    Args:
        db: Sesja SQLAlchemy.
        server_id: Identyfikator serwera do aktualizacji.
        server_data: Dane do aktualizacji — pola None są ignorowane.

    Returns:
        Zaktualizowany obiekt Server lub None jeśli serwer nie istnieje.
    """
    # Pobieramy istniejący serwer
    db_server = get_server_by_id(db, server_id)
    if db_server is None:
        return None
    # Iterujemy po polach i aktualizujemy tylko te, które zostały ustawione
    update_data = server_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        # Konwertujemy enumy Pydantic na wartości string przed zapisem
        if hasattr(value, "value"):
            value = value.value
        setattr(db_server, field, value)
    db.commit()
    # Pobieramy zaktualizowany obiekt świeżym zapytaniem
    return get_server_by_id(db, server_id)


def delete_server(db: Session, server_id: int) -> bool:
    """
    Usuwa serwer z bazy danych.

    Args:
        db: Sesja SQLAlchemy.
        server_id: Identyfikator serwera do usunięcia.

    Returns:
        True jeśli serwer został usunięty, False jeśli nie istniał.
    """
    db_server = get_server_by_id(db, server_id)
    if db_server is None:
        return False
    db.delete(db_server)
    db.commit()
    return True


# ---------------------------------------------------------------------------
# CRUD Projektów
# ---------------------------------------------------------------------------


def get_projects(
    db: Session,
    skip: int = 0,
    limit: int = 50,
    status: str | None = None,
) -> list[Project]:
    """
    Pobiera listę projektów z opcjonalnym filtrem statusu i paginacją.

    Args:
        db: Sesja SQLAlchemy przekazana przez FastAPI Depends.
        skip: Liczba rekordów do pominięcia (offset paginacji).
        limit: Maksymalna liczba zwracanych rekordów.
        status: Opcjonalny filtr — zwraca tylko projekty o podanym statusie.

    Returns:
        Lista obiektów Project posortowanych od najnowszych.
    """
    # Budujemy zapytanie bazowe — sortujemy od najnowszych
    query = db.query(Project).order_by(Project.created_at.desc())
    # Stosujemy filtr statusu jeśli podany
    if status is not None:
        query = query.filter(Project.status == status)
    return query.offset(skip).limit(limit).all()


def get_project_by_id(db: Session, project_id: int) -> Project | None:
    """
    Pobiera projekt po ID z eager-loaded relacjami (unika N+1 queries).

    Ładuje kpis, technologies, scope_items, ports, dev_server, prod_server
    w jednym zapytaniu przez joinedload.

    Args:
        db: Sesja SQLAlchemy.
        project_id: Identyfikator projektu.

    Returns:
        Obiekt Project z załadowanymi relacjami lub None jeśli nie istnieje.
    """
    return (
        db.query(Project)
        .options(
            joinedload(Project.kpis),
            joinedload(Project.technologies),
            joinedload(Project.scope_items),
            joinedload(Project.ports),
            joinedload(Project.dev_server),
            joinedload(Project.prod_server),
        )
        .filter(Project.id == project_id)
        .first()
    )


def get_project_by_code(db: Session, code: str) -> Project | None:
    """
    Pobiera projekt po unikalnym kodzie.

    Args:
        db: Sesja SQLAlchemy.
        code: Unikalny kod projektu, np. "PROJECT-X-2026".

    Returns:
        Obiekt Project lub None jeśli nie istnieje.
    """
    return db.query(Project).filter(Project.code == code).first()


def create_project(db: Session, project_data: ProjectCreate) -> Project:
    """
    Tworzy nowy projekt w bazie danych.

    Args:
        db: Sesja SQLAlchemy.
        project_data: Zwalidowane dane wejściowe z formularza/API.

    Returns:
        Nowo utworzony obiekt Project z wypełnionym ID.
    """
    # Tworzymy obiekt modelu — konwertujemy enum status do wartości string
    db_project = Project(
        name=project_data.name,
        code=project_data.code,
        status=project_data.status.value,
        owner_name=project_data.owner_name,
        owner_id=project_data.owner_id,
        problem_statement=project_data.problem_statement,
        start_date=project_data.start_date,
        end_date=project_data.end_date,
        dev_server_id=project_data.dev_server_id,
        prod_server_id=project_data.prod_server_id,
        port_range_start=project_data.port_range_start,
        port_range_end=project_data.port_range_end,
    )
    db.add(db_project)
    db.commit()
    # Odświeżamy obiekt i pobieramy z relacjami przez dedykowaną funkcję
    db.refresh(db_project)
    return get_project_by_id(db, db_project.id)  # type: ignore[return-value]


def update_project(db: Session, project_id: int, project_data: ProjectUpdate) -> Project | None:
    """
    Aktualizuje projekt — partial update (tylko podane pola).

    Args:
        db: Sesja SQLAlchemy.
        project_id: Identyfikator projektu do aktualizacji.
        project_data: Dane do aktualizacji — pola None są ignorowane.

    Returns:
        Zaktualizowany obiekt Project z relacjami lub None jeśli nie istnieje.
    """
    # Pobieramy istniejący projekt (bez joinedload — wystarczy podstawowy rekord)
    db_project = db.query(Project).filter(Project.id == project_id).first()
    if db_project is None:
        return None
    # Iterujemy po polach i aktualizujemy tylko te, które zostały ustawione
    update_data = project_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        # Konwertujemy enumy Pydantic na wartości string przed zapisem
        if hasattr(value, "value"):
            value = value.value
        setattr(db_project, field, value)
    db.commit()
    # Pobieramy zaktualizowany projekt z eager-loaded relacjami
    return get_project_by_id(db, project_id)


def delete_project(db: Session, project_id: int) -> bool:
    """
    Usuwa projekt z bazy danych.

    Cascade automatycznie usunie powiązane KPI, technologie, zakres i porty.

    Args:
        db: Sesja SQLAlchemy.
        project_id: Identyfikator projektu do usunięcia.

    Returns:
        True jeśli projekt został usunięty, False jeśli nie istniał.
    """
    db_project = db.query(Project).filter(Project.id == project_id).first()
    if db_project is None:
        return False
    db.delete(db_project)
    db.commit()
    return True


# ---------------------------------------------------------------------------
# CRUD KPI
# ---------------------------------------------------------------------------


def get_kpi_by_id(db: Session, kpi_id: int) -> ProjectKPI | None:
    """
    Pobiera wskaźnik KPI po ID.

    Args:
        db: Sesja SQLAlchemy.
        kpi_id: Identyfikator KPI.

    Returns:
        Obiekt ProjectKPI lub None jeśli nie istnieje.
    """
    return db.query(ProjectKPI).filter(ProjectKPI.id == kpi_id).first()


def create_kpi(db: Session, project_id: int, kpi_data: KPICreate) -> ProjectKPI:
    """
    Tworzy nowy wskaźnik KPI przypisany do projektu.

    Args:
        db: Sesja SQLAlchemy.
        project_id: Identyfikator projektu nadrzędnego.
        kpi_data: Zwalidowane dane wejściowe.

    Returns:
        Nowo utworzony obiekt ProjectKPI z wypełnionym ID.
    """
    # Tworzymy obiekt KPI przypisany do projektu
    db_kpi = ProjectKPI(
        project_id=project_id,
        name=kpi_data.name,
        target_value=kpi_data.target_value,
        current_value=kpi_data.current_value,
        unit=kpi_data.unit,
    )
    db.add(db_kpi)
    db.commit()
    db.refresh(db_kpi)
    return db_kpi


def update_kpi(db: Session, kpi_id: int, kpi_data: KPIUpdate) -> ProjectKPI | None:
    """
    Aktualizuje wskaźnik KPI — partial update.

    Args:
        db: Sesja SQLAlchemy.
        kpi_id: Identyfikator KPI do aktualizacji.
        kpi_data: Dane do aktualizacji — pola None są ignorowane.

    Returns:
        Zaktualizowany obiekt ProjectKPI lub None jeśli nie istnieje.
    """
    db_kpi = get_kpi_by_id(db, kpi_id)
    if db_kpi is None:
        return None
    update_data = kpi_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        # Konwertujemy enumy Pydantic na wartości string przed zapisem
        if hasattr(value, "value"):
            value = value.value
        setattr(db_kpi, field, value)
    db.commit()
    return get_kpi_by_id(db, kpi_id)


def delete_kpi(db: Session, kpi_id: int) -> bool:
    """
    Usuwa wskaźnik KPI z bazy danych.

    Args:
        db: Sesja SQLAlchemy.
        kpi_id: Identyfikator KPI do usunięcia.

    Returns:
        True jeśli KPI zostało usunięte, False jeśli nie istniało.
    """
    db_kpi = get_kpi_by_id(db, kpi_id)
    if db_kpi is None:
        return False
    db.delete(db_kpi)
    db.commit()
    return True


# ---------------------------------------------------------------------------
# CRUD Technologii
# ---------------------------------------------------------------------------


def get_technology_by_id(db: Session, tech_id: int) -> ProjectTechnology | None:
    """
    Pobiera technologię po ID.

    Args:
        db: Sesja SQLAlchemy.
        tech_id: Identyfikator technologii.

    Returns:
        Obiekt ProjectTechnology lub None jeśli nie istnieje.
    """
    return db.query(ProjectTechnology).filter(ProjectTechnology.id == tech_id).first()


def create_technology(
    db: Session, project_id: int, tech_data: TechnologyCreate
) -> ProjectTechnology:
    """
    Dodaje technologię do stosu projektu.

    Args:
        db: Sesja SQLAlchemy.
        project_id: Identyfikator projektu nadrzędnego.
        tech_data: Zwalidowane dane wejściowe.

    Returns:
        Nowo utworzony obiekt ProjectTechnology z wypełnionym ID.
    """
    # Tworzymy obiekt technologii przypisany do projektu
    db_tech = ProjectTechnology(
        project_id=project_id,
        category=tech_data.category.value,
        name=tech_data.name,
        version=tech_data.version,
        description=tech_data.description,
    )
    db.add(db_tech)
    db.commit()
    db.refresh(db_tech)
    return db_tech


def update_technology(
    db: Session, tech_id: int, tech_data: TechnologyUpdate
) -> ProjectTechnology | None:
    """
    Aktualizuje technologię — partial update.

    Args:
        db: Sesja SQLAlchemy.
        tech_id: Identyfikator technologii do aktualizacji.
        tech_data: Dane do aktualizacji — pola None są ignorowane.

    Returns:
        Zaktualizowany obiekt ProjectTechnology lub None jeśli nie istnieje.
    """
    db_tech = get_technology_by_id(db, tech_id)
    if db_tech is None:
        return None
    update_data = tech_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        # Konwertujemy enumy Pydantic na wartości string przed zapisem
        if hasattr(value, "value"):
            value = value.value
        setattr(db_tech, field, value)
    db.commit()
    return get_technology_by_id(db, tech_id)


def delete_technology(db: Session, tech_id: int) -> bool:
    """
    Usuwa technologię z bazy danych.

    Args:
        db: Sesja SQLAlchemy.
        tech_id: Identyfikator technologii do usunięcia.

    Returns:
        True jeśli technologia została usunięta, False jeśli nie istniała.
    """
    db_tech = get_technology_by_id(db, tech_id)
    if db_tech is None:
        return False
    db.delete(db_tech)
    db.commit()
    return True


# ---------------------------------------------------------------------------
# CRUD Zakresu (Scope Items)
# ---------------------------------------------------------------------------


def get_scope_item_by_id(db: Session, item_id: int) -> ProjectScopeItem | None:
    """
    Pobiera element zakresu po ID.

    Args:
        db: Sesja SQLAlchemy.
        item_id: Identyfikator elementu zakresu.

    Returns:
        Obiekt ProjectScopeItem lub None jeśli nie istnieje.
    """
    return db.query(ProjectScopeItem).filter(ProjectScopeItem.id == item_id).first()


def create_scope_item(
    db: Session, project_id: int, item_data: ScopeItemCreate
) -> ProjectScopeItem:
    """
    Dodaje element zakresu do projektu.

    Args:
        db: Sesja SQLAlchemy.
        project_id: Identyfikator projektu nadrzędnego.
        item_data: Zwalidowane dane wejściowe.

    Returns:
        Nowo utworzony obiekt ProjectScopeItem z wypełnionym ID.
    """
    # Tworzymy obiekt elementu zakresu przypisany do projektu
    db_item = ProjectScopeItem(
        project_id=project_id,
        category=item_data.category.value,
        description=item_data.description,
        priority=item_data.priority,
    )
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    return db_item


def update_scope_item(
    db: Session, item_id: int, item_data: ScopeItemUpdate
) -> ProjectScopeItem | None:
    """
    Aktualizuje element zakresu — partial update.

    Args:
        db: Sesja SQLAlchemy.
        item_id: Identyfikator elementu zakresu do aktualizacji.
        item_data: Dane do aktualizacji — pola None są ignorowane.

    Returns:
        Zaktualizowany obiekt ProjectScopeItem lub None jeśli nie istnieje.
    """
    db_item = get_scope_item_by_id(db, item_id)
    if db_item is None:
        return None
    update_data = item_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        # Konwertujemy enumy Pydantic na wartości string przed zapisem
        if hasattr(value, "value"):
            value = value.value
        setattr(db_item, field, value)
    db.commit()
    return get_scope_item_by_id(db, item_id)


def delete_scope_item(db: Session, item_id: int) -> bool:
    """
    Usuwa element zakresu z bazy danych.

    Args:
        db: Sesja SQLAlchemy.
        item_id: Identyfikator elementu zakresu do usunięcia.

    Returns:
        True jeśli element został usunięty, False jeśli nie istniał.
    """
    db_item = get_scope_item_by_id(db, item_id)
    if db_item is None:
        return False
    db.delete(db_item)
    db.commit()
    return True


# ---------------------------------------------------------------------------
# CRUD Portów
# ---------------------------------------------------------------------------


def get_port_by_id(db: Session, port_id: int) -> ProjectPort | None:
    """
    Pobiera port sieciowy po ID.

    Args:
        db: Sesja SQLAlchemy.
        port_id: Identyfikator portu.

    Returns:
        Obiekt ProjectPort lub None jeśli nie istnieje.
    """
    return db.query(ProjectPort).filter(ProjectPort.id == port_id).first()


def get_project_ports(db: Session, project_id: int) -> list[ProjectPort]:
    """
    Pobiera wszystkie porty sieciowe przypisane do projektu.

    Args:
        db: Sesja SQLAlchemy.
        project_id: Identyfikator projektu.

    Returns:
        Lista obiektów ProjectPort posortowanych po numerze portu.
    """
    return (
        db.query(ProjectPort)
        .filter(ProjectPort.project_id == project_id)
        .order_by(ProjectPort.port_number)
        .all()
    )


def create_port(db: Session, project_id: int, port_data: PortCreate) -> ProjectPort:
    """
    Przypisuje port sieciowy do projektu.

    Args:
        db: Sesja SQLAlchemy.
        project_id: Identyfikator projektu nadrzędnego.
        port_data: Zwalidowane dane wejściowe.

    Returns:
        Nowo utworzony obiekt ProjectPort z wypełnionym ID.
    """
    # Tworzymy obiekt portu przypisany do projektu
    db_port = ProjectPort(
        project_id=project_id,
        port_number=port_data.port_number,
        protocol=port_data.protocol.value,
        service_name=port_data.service_name,
        description=port_data.description,
    )
    db.add(db_port)
    db.commit()
    db.refresh(db_port)
    return db_port


def update_port(db: Session, port_id: int, port_data: PortUpdate) -> ProjectPort | None:
    """
    Aktualizuje port sieciowy — partial update.

    Args:
        db: Sesja SQLAlchemy.
        port_id: Identyfikator portu do aktualizacji.
        port_data: Dane do aktualizacji — pola None są ignorowane.

    Returns:
        Zaktualizowany obiekt ProjectPort lub None jeśli nie istnieje.
    """
    db_port = get_port_by_id(db, port_id)
    if db_port is None:
        return None
    update_data = port_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        # Konwertujemy enumy Pydantic na wartości string przed zapisem
        if hasattr(value, "value"):
            value = value.value
        setattr(db_port, field, value)
    db.commit()
    return get_port_by_id(db, port_id)


def delete_port(db: Session, port_id: int) -> bool:
    """
    Usuwa port sieciowy z bazy danych.

    Args:
        db: Sesja SQLAlchemy.
        port_id: Identyfikator portu do usunięcia.

    Returns:
        True jeśli port został usunięty, False jeśli nie istniał.
    """
    db_port = get_port_by_id(db, port_id)
    if db_port is None:
        return False
    db.delete(db_port)
    db.commit()
    return True
