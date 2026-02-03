from dataclasses import dataclass, field
from typing import Optional

@dataclass
class ApiConfig:
    name: str
    url: str
    weight: int = 50
    description: str = ""
    enabled: bool = True
    supports_params: bool = False
    params: str = ""
    source: str = "unknown"
    line_number: int = 0
    
    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "url": self.url,
            "weight": self.weight,
            "description": self.description,
            "enabled": self.enabled,
            "supports_params": self.supports_params,
            "params": self.params,
            "source": self.source,
            "line_number": self.line_number
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "ApiConfig":
        return cls(
            name=data.get("name", ""),
            url=data.get("url", ""),
            weight=data.get("weight", 50),
            description=data.get("description", ""),
            enabled=data.get("enabled", True),
            supports_params=data.get("supports_params", False),
            params=data.get("params", ""),
            source=data.get("source", "unknown"),
            line_number=data.get("line_number", 0)
        )
