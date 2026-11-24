"""View model pro frontend (ADR-0006, mapa obrazovek „Kostra view modelu“).

Frontend dostane hotová data a jen je zobrazí a naformátuje (`cs-CZ`). Délky jsou
celé milimetry, peníze řetězec `Decimal`, výtěžnost poměr 0–1. Interní detaily
(cesty v zakázce, revize výsledku, trasování) sem nepatří.
"""

from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict

from decision_engine.core.model.calculation import SolutionStatus
from decision_engine.core.model.cutting_1d import Objective


class _View(BaseModel):
    model_config = ConfigDict(frozen=True)


class AiView(_View):
    extraction_available: bool


class SessionView(_View):
    id: str
    ai: AiView


class CapabilityView(_View):
    id: str
    label: str


type StepState = Literal["pending", "active", "done", "stale", "unavailable"]


class StepView(_View):
    id: Literal["input", "review", "result"]
    label: str
    state: StepState


class ProjectView(_View):
    name: str
    revision: int | None
    step: Literal["input", "review", "result"]
    steps: tuple[StepView, ...]
    has_content: bool
    can_edit: bool
    """Potvrzenou zakázku lze ručně upravit („Upravit údaje“): žádný návrh, nic neběží."""
    can_save: bool
    """Potvrzenou zakázku lze uložit do souboru (UC-06)."""
    save_note: str | None
    """Upozornění k uložení, např. že rozpracovaný návrh nebude součástí souboru (UC-06 A2)."""
    unsaved_changes: bool
    """Zahozením by se ztratila práce: neuložená zakázka nebo rozpracovaný návrh (UC-15)."""
    unsaved_badge: bool
    """Ukázat štítek „neuloženo“: jen u potvrzené zakázky, kterou jde uložit."""
    can_start_new: bool
    """Novou zakázku lze začít (nic neběží)."""


class PendingOperationView(_View):
    kind: Literal["extraction", "solving"]
    label: str


class MessageView(_View):
    id: int
    role: Literal["user", "assistant"]
    kind: Literal["text", "error"]
    text: str
    retry_text: str | None = None
    """U chyby AI zpráva, kterou „Zkusit znovu“ pošle znovu."""


class TextCell(_View):
    value: str | None
    unconfirmed: bool
    error: str | None


class IntCell(_View):
    value: int | None
    unconfirmed: bool
    error: str | None


class DecimalCell(_View):
    """Délka v mm s nejvýš jedním desetinným místem (prořez, ořez; ADR-0011)."""

    value: Decimal | None
    unconfirmed: bool
    error: str | None


class MoneyCell(_View):
    value: Decimal | None
    unconfirmed: bool
    error: str | None


class PartRow(_View):
    id: str
    name: TextCell
    length_mm: IntCell
    quantity: IntCell


class StockRow(_View):
    id: str
    length_mm: IntCell
    price: MoneyCell


class ParametersView(_View):
    kerf_mm: DecimalCell
    trim_mm: DecimalCell
    min_remnant_mm: IntCell
    time_limit_s: IntCell


class ObjectiveOption(_View):
    value: Objective
    label: str
    hint: str
    disabled_reason: str | None


class FieldErrorView(_View):
    field: str
    """Čitelné umístění chyby („Díl 2, délka“)."""
    message: str
    target: str | None
    """Klíč pole ve formuláři (`parts.1.length_mm`), na které vede odkaz v souhrnu chyb."""


class ProposalView(_View):
    is_change: bool
    """Úprava existující zakázky (jinak nová zakázka)."""
    origin: Literal["ai", "manual", "file"]
    """Návrh z extrakce AI, z ručního zadání či úpravy, nebo ze souboru."""
    name: TextCell
    material: TextCell
    parts: tuple[PartRow, ...]
    stock: tuple[StockRow, ...]
    parameters: ParametersView
    objective: Objective | None
    objective_unconfirmed: bool
    objective_options: tuple[ObjectiveOption, ...]
    errors: tuple[FieldErrorView, ...]
    can_confirm: bool
    confirm_disabled_reason: str | None


class BarsByLength(_View):
    length_mm: int
    count: int


class MetricsView(_View):
    bars_used: int
    bars_by_length: tuple[BarsByLength, ...]
    """Počet spotřebovaných tyčí podle délky, od nejdelší."""
    parts_length_mm: int
    consumed_length_mm: int
    remnant_length_mm: Decimal
    remnant_count: int
    waste_length_mm: Decimal
    yield_ratio: float


class PieceView(_View):
    part_id: str
    name: str
    length_mm: int
    start_mm: Decimal


class BarView(_View):
    numbers: tuple[int, ...]
    """Čísla tyčí se stejným řezáním (stejné číslování jako v SVG)."""
    length_mm: int
    pieces: tuple[PieceView, ...]
    cuts_mm: tuple[Decimal, ...]
    """Polohy řezů od začátku tyče."""
    tail: Literal["none", "remnant", "waste"]
    tail_length_mm: Decimal


class UnplacedView(_View):
    part_id: str
    name: str
    length_mm: int
    quantity: int
    reason: str


class ResultView(_View):
    status: SolutionStatus
    status_label: str
    stale: bool
    stale_reason: str | None
    svg: str
    metrics: MetricsView
    bars: tuple[BarView, ...]
    unplaced: tuple[UnplacedView, ...]


class ViewModel(_View):
    """Celý stav relace pro UI."""

    session: SessionView
    capabilities: tuple[CapabilityView, ...]
    project: ProjectView
    pending_operation: PendingOperationView | None
    messages: tuple[MessageView, ...]
    proposal: ProposalView | None
    result: ResultView | None
    import_error: str | None
    """Proč se poslední soubor nepodařilo načíst; zakázka zůstala beze změny (UC-06 E1)."""
