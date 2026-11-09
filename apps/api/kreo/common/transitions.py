"""
Machine à états générique.

Chaque domaine déclare ses transitions sous la forme
{(from, to): {"roles": {...}, "guard": callable | None}}.
Toute transition absente est refusée en 409.
"""

from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

from .exceptions import TransitionError


@dataclass(frozen=True)
class Transition:
    source: tuple[str, ...]
    target: str
    roles: frozenset[str]
    guard: Callable[..., None] | None = None
    description: str = ""


@dataclass
class StateMachine:
    name: str
    transitions: list[Transition] = field(default_factory=list)

    def add(self, source, target, roles, guard=None, description=""):
        if isinstance(source, str):
            source = (source,)
        self.transitions.append(
            Transition(tuple(source), target, frozenset(roles), guard, description)
        )
        return self

    def find(self, current: str, target: str) -> Transition | None:
        for t in self.transitions:
            if current in t.source and t.target == target:
                return t
        return None

    def check(self, current: str, target: str, actor_roles: set[str], **context: Any) -> Transition:
        transition = self.find(current, target)
        if transition is None:
            raise TransitionError(
                f"Transition {self.name} « {current} → {target} » inexistante.",
                extra={"from": current, "to": target},
            )
        if not (transition.roles & actor_roles):
            raise TransitionError(
                f"Ton rôle ne permet pas la transition « {current} → {target} ».",
                problem_type="transition-forbidden",
                extra={"from": current, "to": target, "allowed_roles": sorted(transition.roles)},
            )
        if transition.guard is not None:
            transition.guard(**context)
        return transition

    def targets_from(self, current: str, actor_roles: set[str]) -> list[str]:
        return sorted(
            {t.target for t in self.transitions if current in t.source and (t.roles & actor_roles)}
        )
