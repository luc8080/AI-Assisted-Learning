from abc import ABC, abstractmethod
from typing import List, Dict


class ComponentPluginBase(ABC):
    """
    元件推薦 Plugin 的抽象基底類別。
    所有插件都需實作此介面，定義推薦邏輯與視覺化欄位。
    """

    @property
    @abstractmethod
    def category(self) -> str:
        """對應的產品類別名稱（如 Ferrite Bead）"""
        pass

    @property
    @abstractmethod
    def prompt_template(self) -> str:
        """給 LLM 的推薦 prompt 模板"""
        pass

    @property
    @abstractmethod
    def key_metrics(self) -> List[str]:
        """用於視覺化分析的欄位（雷達圖、條件比對）"""
        pass

    @abstractmethod
    def match_score(self, product: Dict, requirements: Dict) -> float:
        """計算條件符合程度，回傳百分比（0-100）"""
        pass
