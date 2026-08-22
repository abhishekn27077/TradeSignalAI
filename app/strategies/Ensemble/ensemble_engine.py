import numpy as np
import pandas as pd
from typing import List, Dict, Any, Optional
from collections import defaultdict

from app.strategies.Ensemble.models import StrategyFamily, StrategyVote, EnsembleDecision


class StrategyEnsembleEngine:
    """
    Quantitative Strategy Ensemble & Cluster-Based Voting Engine.
    Incorporates regime suitability, strategy quality, and cluster-based collinearity attenuation.
    """

    # Group correlated strategy families into statistical clusters
    STRATEGY_CLUSTERS = {
        StrategyFamily.MARKET_STRUCTURE: "STRUCTURE_CLUSTER",
        StrategyFamily.SMART_MONEY: "STRUCTURE_CLUSTER",
        StrategyFamily.LIQUIDITY: "STRUCTURE_CLUSTER",
        StrategyFamily.TREND: "MOMENTUM_CLUSTER",
        StrategyFamily.MOMENTUM: "MOMENTUM_CLUSTER",
        StrategyFamily.BREAKOUT: "MOMENTUM_CLUSTER",
        StrategyFamily.ICT_SESSION: "TIMING_CLUSTER",
        StrategyFamily.VWAP: "TIMING_CLUSTER",
        StrategyFamily.MEAN_REVERSION: "REVERSION_CLUSTER",
        StrategyFamily.MULTI_TIMEFRAME: "HIERARCHY_CLUSTER",
    }

    # Baseline family weights (prioritized by out-of-sample edge stability)
    BASE_FAMILY_WEIGHTS = {
        StrategyFamily.MARKET_STRUCTURE: 1.30,
        StrategyFamily.SMART_MONEY: 1.25,
        StrategyFamily.LIQUIDITY: 1.20,
        StrategyFamily.MULTI_TIMEFRAME: 1.15,
        StrategyFamily.ICT_SESSION: 1.10,
        StrategyFamily.TREND: 1.00,
        StrategyFamily.MOMENTUM: 0.90,
        StrategyFamily.BREAKOUT: 0.90,
        StrategyFamily.VWAP: 0.85,
        StrategyFamily.MEAN_REVERSION: 0.75,
    }

    def __init__(self, consensus_threshold: float = 0.60):
        self.consensus_threshold = consensus_threshold

    def evaluate_ensemble(
        self,
        votes: List[StrategyVote],
        regime: str = "STRONG_TREND"
    ) -> EnsembleDecision:
        if not votes:
            return EnsembleDecision(
                direction="NEUTRAL",
                ensemble_confidence=0.0,
                ensemble_score=0.0,
                buy_weight=0.0,
                sell_weight=0.0,
                neutral_weight=1.0,
                participating_strategies=0,
                agreed_strategies=[],
                conflicted_strategies=[],
                collinearity_dampener_applied=0.0,
                votes=[]
            )

        # 1. Group votes by cluster and direction
        cluster_votes = defaultdict(lambda: {"BUY": [], "SELL": [], "NEUTRAL": []})
        for v in votes:
            cluster = self.STRATEGY_CLUSTERS.get(v.family, "DEFAULT")
            v.cluster = cluster
            cluster_votes[cluster][v.direction].append(v)

        total_buy_weight = 0.0
        total_sell_weight = 0.0
        total_neutral_weight = 0.0
        total_raw_weight = 0.0
        total_dampened_weight = 0.0

        agreed = []
        conflicted = []

        # 2. Compute cluster-dampened weights
        for cluster, dir_map in cluster_votes.items():
            for direction, v_list in dir_map.items():
                if not v_list:
                    continue

                k = len(v_list)
                # Collinearity dampener: divide sum of votes by sqrt(k) to attenuate collinearity
                cluster_dampener = 1.0 / np.sqrt(k)

                for v in v_list:
                    base_w = self.BASE_FAMILY_WEIGHTS.get(v.family, 1.0)
                    # Modulate by quality and regime suitability
                    effective_w = base_w * v.quality * v.regime_suitability * v.confidence
                    dampened_w = effective_w * cluster_dampener

                    total_raw_weight += effective_w
                    total_dampened_weight += dampened_w

                    if direction == "BUY":
                        total_buy_weight += dampened_w
                        agreed.append(v.family.value)
                    elif direction == "SELL":
                        total_sell_weight += dampened_w
                        agreed.append(v.family.value)
                    else:
                        total_neutral_weight += dampened_w

        total_active = total_buy_weight + total_sell_weight + total_neutral_weight
        if total_active <= 0.0:
            return EnsembleDecision(
                direction="NEUTRAL",
                ensemble_confidence=0.0,
                ensemble_score=0.0,
                buy_weight=0.0,
                sell_weight=0.0,
                neutral_weight=1.0,
                participating_strategies=len(votes),
                agreed_strategies=[],
                conflicted_strategies=[v.family.value for v in votes],
                collinearity_dampener_applied=0.0,
                votes=votes
            )

        norm_buy = total_buy_weight / total_active
        norm_sell = total_sell_weight / total_active
        norm_neutral = total_neutral_weight / total_active

        # Determine consensus direction
        if norm_buy > norm_sell and norm_buy >= self.consensus_threshold:
            final_dir = "BUY"
            conf = norm_buy
            agreed_list = [v.family.value for v in votes if v.direction == "BUY"]
            conflicted_list = [v.family.value for v in votes if v.direction == "SELL"]
        elif norm_sell > norm_buy and norm_sell >= self.consensus_threshold:
            final_dir = "SELL"
            conf = norm_sell
            agreed_list = [v.family.value for v in votes if v.direction == "SELL"]
            conflicted_list = [v.family.value for v in votes if v.direction == "BUY"]
        else:
            final_dir = "NEUTRAL"
            conf = max(norm_buy, norm_sell)
            agreed_list = []
            conflicted_list = [v.family.value for v in votes]

        ensemble_score = float(conf * 100.0)
        collinearity_delta = max(0.0, total_raw_weight - total_dampened_weight)

        return EnsembleDecision(
            direction=final_dir,
            ensemble_confidence=conf,
            ensemble_score=ensemble_score,
            buy_weight=norm_buy,
            sell_weight=norm_sell,
            neutral_weight=norm_neutral,
            participating_strategies=len(votes),
            agreed_strategies=agreed_list,
            conflicted_strategies=conflicted_list,
            collinearity_dampener_applied=collinearity_delta,
            votes=votes,
            details={
                "regime": regime,
                "total_raw_weight": round(total_raw_weight, 3),
                "total_dampened_weight": round(total_dampened_weight, 3)
            }
        )
