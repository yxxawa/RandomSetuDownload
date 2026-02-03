from dataclasses import dataclass
from enum import Enum
from typing import Optional

class DownloadStatus(Enum):
    IDLE = "idle"
    DOWNLOADING = "downloading"
    SUCCESS = "success"
    FAILED = "failed"

@dataclass
class DownloadTask:
    url: str
    save_path: Optional[str] = None
    status: DownloadStatus = DownloadStatus.IDLE
    error_message: str = ""
    api_name: str = ""
    progress: int = 0
    total_size: int = 0
    
    def to_dict(self) -> dict:
        return {
            "url": self.url,
            "save_path": self.save_path,
            "status": self.status.value,
            "error_message": self.error_message,
            "api_name": self.api_name,
            "progress": self.progress,
            "total_size": self.total_size
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "DownloadTask":
        return cls(
            url=data.get("url", ""),
            save_path=data.get("save_path"),
            status=DownloadStatus(data.get("status", "idle")),
            error_message=data.get("error_message", ""),
            api_name=data.get("api_name", ""),
            progress=data.get("progress", 0),
            total_size=data.get("total_size", 0)
        )
