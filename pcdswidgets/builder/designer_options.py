from dataclasses import dataclass


@dataclass
class DesignerOptions:
    group: str
    is_container: bool
    icon: str | None
