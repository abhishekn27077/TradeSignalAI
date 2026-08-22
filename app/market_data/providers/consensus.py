import pandas as pd
import numpy as np
from enum import Enum
from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List


class ConsensusStatus(str, Enum):
    PRIMARY = "PRIMARY"
    SECONDARY = "SECONDARY"
    DISAGREEMENT = "DISAGREEMENT"
    UNAVAILABLE = "UNAVAILABLE"


@dataclass
class ConsensusComparison:
    timestamp: str
    primary_close: Optional[float]
    secondary_close: Optional[float]
    abs_diff: float
    pct_diff: float
    volume_diff_pct: float
    status: ConsensusStatus
    details: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ProviderConsensusReport:
    asset: str
    timeframe: str
    primary_provider: str
    secondary_provider: str
    status: ConsensusStatus
    mean_price_deviation_pct: float
    max_price_deviation_pct: float
    disagreement_count: int
    is_consensus_healthy: bool
    comparisons: List[ConsensusComparison] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "asset": self.asset,
            "timeframe": self.timeframe,
            "primary_provider": self.primary_provider,
            "secondary_provider": self.secondary_provider,
            "status": self.status.value,
            "mean_price_deviation_pct": round(float(self.mean_price_deviation_pct), 4),
            "max_price_deviation_pct": round(float(self.max_price_deviation_pct), 4),
            "disagreement_count": self.disagreement_count,
            "is_consensus_healthy": self.is_consensus_healthy,
        }


class ProviderConsensusEngine:
    """
    Multi-Provider Feed Comparison and Consensus Engine.
    Cross-validates price and volume integrity across independent data feeds.
    """

    def __init__(self, max_allowed_deviation_pct: float = 0.005):  # 0.5% max price deviation
        self.max_allowed_deviation_pct = max_allowed_deviation_pct

    def evaluate_consensus(
        self,
        primary_df: Optional[pd.DataFrame],
        secondary_df: Optional[pd.DataFrame],
        asset: str = "UNKNOWN",
        timeframe: str = "1H",
        primary_name: str = "PRIMARY_FEED",
        secondary_name: str = "SECONDARY_FEED"
    ) -> ProviderConsensusReport:
        if primary_df is None or primary_df.empty:
            if secondary_df is not None and not secondary_df.empty:
                return ProviderConsensusReport(
                    asset=asset,
                    timeframe=timeframe,
                    primary_provider=primary_name,
                    secondary_provider=secondary_name,
                    status=ConsensusStatus.SECONDARY,
                    mean_price_deviation_pct=0.0,
                    max_price_deviation_pct=0.0,
                    disagreement_count=0,
                    is_consensus_healthy=True
                )
            return ProviderConsensusReport(
                asset=asset,
                timeframe=timeframe,
                primary_provider=primary_name,
                secondary_provider=secondary_name,
                status=ConsensusStatus.UNAVAILABLE,
                mean_price_deviation_pct=0.0,
                max_price_deviation_pct=0.0,
                disagreement_count=0,
                is_consensus_healthy=False
            )

        if secondary_df is None or secondary_df.empty:
            return ProviderConsensusReport(
                asset=asset,
                timeframe=timeframe,
                primary_provider=primary_name,
                secondary_provider=secondary_name,
                status=ConsensusStatus.PRIMARY,
                mean_price_deviation_pct=0.0,
                max_price_deviation_pct=0.0,
                disagreement_count=0,
                is_consensus_healthy=True
            )

        # Merge on timestamp for exact comparison
        p_sub = primary_df[['timestamp', 'close', 'volume']].rename(columns={'close': 'p_close', 'volume': 'p_vol'})
        s_sub = secondary_df[['timestamp', 'close', 'volume']].rename(columns={'close': 's_close', 'volume': 's_vol'})

        merged = pd.merge(p_sub, s_sub, on='timestamp', how='inner')
        if merged.empty:
            return ProviderConsensusReport(
                asset=asset,
                timeframe=timeframe,
                primary_provider=primary_name,
                secondary_provider=secondary_name,
                status=ConsensusStatus.DISAGREEMENT,
                mean_price_deviation_pct=1.0,
                max_price_deviation_pct=1.0,
                disagreement_count=len(primary_df),
                is_consensus_healthy=False
            )

        abs_diff = np.abs(merged['p_close'] - merged['s_close'])
        pct_diff = abs_diff / merged['p_close']
        vol_diff = np.abs(merged['p_vol'] - merged['s_vol']) / (merged['p_vol'] + 1e-6)

        disagreements = pct_diff > self.max_allowed_deviation_pct
        disagreement_count = int(disagreements.sum())

        mean_dev = float(pct_diff.mean())
        max_dev = float(pct_diff.max())

        status = ConsensusStatus.DISAGREEMENT if disagreement_count > 0 else ConsensusStatus.PRIMARY
        healthy = (disagreement_count == 0) and (mean_dev <= self.max_allowed_deviation_pct)

        return ProviderConsensusReport(
            asset=asset,
            timeframe=timeframe,
            primary_provider=primary_name,
            secondary_provider=secondary_name,
            status=status,
            mean_price_deviation_pct=mean_dev,
            max_price_deviation_pct=max_dev,
            disagreement_count=disagreement_count,
            is_consensus_healthy=healthy
        )
