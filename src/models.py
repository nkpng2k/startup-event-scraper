from dataclasses import dataclass, field


@dataclass
class Event:
    name: str
    date: str
    cost: str
    description: str
    registration_link: str
    source: str
    topics: list[str] = field(default_factory=list)
