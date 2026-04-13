"""Job dependency resolution for cronwatch.

Allows jobs to declare dependencies on other jobs, ensuring they only
run after their dependencies have succeeded in the current cycle.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set


@dataclass
class DependencyPolicy:
    """Policy describing a job's dependencies."""

    requires: List[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        if not isinstance(self.requires, list):
            raise TypeError("requires must be a list of job names")
        for item in self.requires:
            if not isinstance(item, str) or not item.strip():
                raise ValueError(
                    f"Each dependency must be a non-empty string, got: {item!r}"
                )
        self.requires = [r.strip() for r in self.requires]

    @classmethod
    def from_config(cls, cfg: Optional[dict]) -> "DependencyPolicy":
        if not cfg:
            return cls()
        return cls(requires=cfg.get("requires", []))

    def enabled(self) -> bool:
        return len(self.requires) > 0


def build_dependency_graph(
    jobs: List,
) -> Dict[str, List[str]]:
    """Return a mapping of job name -> list of dependency names."""
    graph: Dict[str, List[str]] = {}
    for job in jobs:
        policy = getattr(job, "dependency", DependencyPolicy())
        graph[job.name] = list(policy.requires)
    return graph


def resolve_order(graph: Dict[str, List[str]]) -> List[str]:
    """Topological sort; raises ValueError on circular dependency."""
    visited: Set[str] = set()
    in_stack: Set[str] = set()
    order: List[str] = []

    def visit(name: str) -> None:
        if name in in_stack:
            raise ValueError(f"Circular dependency detected involving job: {name!r}")
        if name in visited:
            return
        in_stack.add(name)
        for dep in graph.get(name, []):
            if dep not in graph:
                raise ValueError(
                    f"Job {name!r} depends on unknown job {dep!r}"
                )
            visit(dep)
        in_stack.discard(name)
        visited.add(name)
        order.append(name)

    for node in graph:
        visit(node)

    return order


def jobs_ready_to_run(
    graph: Dict[str, List[str]], succeeded: Set[str]
) -> List[str]:
    """Return job names whose dependencies have all succeeded."""
    return [
        name
        for name, deps in graph.items()
        if all(dep in succeeded for dep in deps)
    ]
