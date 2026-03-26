from dataclasses import dataclass


@dataclass
class Event:
    name: str
    date: str
    cost: str
    description: str
    registration_link: str
    source: str
