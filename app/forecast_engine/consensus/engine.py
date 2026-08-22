from app.forecast_engine.base.models import ForecastConsensus, ForecastResult
from app.logs.logger import get_logger

logger = get_logger(__name__)

class ForecastConsensusEngine:
    """
    Combines outputs from multiple forecasting models into a single consensus prediction.
    """
    
    def __init__(self):
        # Default weights if no dynamic performance data is available
        self.default_weights = {
            "kronos": 0.30,
            "transformer": 0.20,
            "lstm": 0.15,
            "xgboost": 0.15,
            "statistical": 0.10,
            "rule_based": 0.10,
            "prophet": 0.0, # example of a model that might be running but not weighted by default
        }

    def compute_consensus(self, results: list[ForecastResult]) -> ForecastConsensus:
        """
        Calculates the weighted consensus from a list of valid ForecastResults.
        """
        if not results:
            return ForecastConsensus(
                combined_direction="NEUTRAL",
                combined_confidence=0.0,
                weights_used={},
                models_included=0
            )

        bullish_score = 0.0
        bearish_score = 0.0
        total_weight = 0.0
        weights_used = {}
        
        prob_sum = 0.0
        prob_weight = 0.0

        for res in results:
            # We use the provider name. In a real app we might lookup the name from the registry using model_id.
            # Assuming model_id matches provider name for now in stubs
            provider_name = res.model_id.split("-")[0].lower() if "-" in res.model_id else res.model_id.lower()
            
            # fallback weight if not in default
            weight = self.default_weights.get(provider_name, 0.05)
            
            # Combine weight with model's own confidence
            effective_weight = weight * res.confidence
            
            if res.direction == "BULLISH":
                bullish_score += effective_weight
            elif res.direction == "BEARISH":
                bearish_score += effective_weight
                
            total_weight += effective_weight
            weights_used[res.model_id] = weight
            
            if res.probability is not None:
                prob_sum += (res.probability * effective_weight)
                prob_weight += effective_weight

        # Determine consensus direction
        combined_direction = "NEUTRAL"
        combined_confidence = 0.0
        
        if total_weight > 0:
            if bullish_score > bearish_score * 1.5:  # threshold for conviction
                combined_direction = "BULLISH"
                combined_confidence = bullish_score / total_weight
            elif bearish_score > bullish_score * 1.5:
                combined_direction = "BEARISH"
                combined_confidence = bearish_score / total_weight
            else:
                combined_direction = "NEUTRAL"
                combined_confidence = max(bullish_score, bearish_score) / total_weight

        combined_probability = None
        if prob_weight > 0:
            combined_probability = prob_sum / prob_weight

        # Calculate Expected Targets
        exp_move_sum = 0.0
        exp_vol_sum = 0.0
        exp_hold_sum = 0.0
        exp_weight = 0.0
        
        for res in results:
            # We use the provider name. In a real app we might lookup the name from the registry using model_id.
            provider_name = res.model_id.split("-")[0].lower() if "-" in res.model_id else res.model_id.lower()
            weight = self.default_weights.get(provider_name, 0.05)
            effective_weight = weight * res.confidence
            
            if res.expected_move_pct is not None:
                # Align the move percentage with the direction
                move_val = abs(res.expected_move_pct) if res.direction == combined_direction else -abs(res.expected_move_pct)
                exp_move_sum += move_val * effective_weight
                exp_weight += effective_weight
            
            if res.expected_volatility is not None:
                exp_vol_sum += res.expected_volatility * effective_weight
                
            if res.expected_hold_candles is not None:
                exp_hold_sum += res.expected_hold_candles * effective_weight

        combined_exp_move = exp_move_sum / exp_weight if exp_weight > 0 else None
        combined_exp_vol = exp_vol_sum / exp_weight if exp_weight > 0 else None
        combined_exp_hold = exp_hold_sum / exp_weight if exp_weight > 0 else None

        return ForecastConsensus(
            combined_direction=combined_direction,
            combined_confidence=round(combined_confidence, 4),
            combined_probability=round(combined_probability, 4) if combined_probability else None,
            expected_move_pct=round(combined_exp_move, 6) if combined_exp_move is not None else None,
            expected_volatility=round(combined_exp_vol, 6) if combined_exp_vol is not None else None,
            expected_hold_candles=round(combined_exp_hold, 2) if combined_exp_hold is not None else None,
            weights_used=weights_used,
            models_included=len(results)
        )

forecast_consensus_engine = ForecastConsensusEngine()
