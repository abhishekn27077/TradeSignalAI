from typing import Any


class ConsensusEngine:
    """
    Combines predictions from multiple AI models, technical indicators,
    and market structure to generate a final high-confidence forecast.
    """
    
    def generate_consensus(self, predictions: list[dict[str, Any]], features: dict[str, Any]) -> dict[str, Any]:
        """
        Takes raw predictions and computes a weighted consensus.
        """
        if not predictions:
            return {"direction": "NEUTRAL", "final_confidence": 0, "risk_score": 100}
            
        buy_score = 0.0
        sell_score = 0.0
        total_weight = 0.0
        
        # Simplified weighted voting based on model confidence
        for p in predictions:
            weight = p.get("confidence", 50) / 100.0
            if p["direction"] == "BUY":
                buy_score += weight
            elif p["direction"] == "SELL":
                sell_score += weight
            total_weight += weight
            
        if total_weight == 0:
             return {"direction": "NEUTRAL", "final_confidence": 0, "risk_score": 100}
             
        buy_prob = buy_score / total_weight
        sell_prob = sell_score / total_weight
        
        direction = "BUY" if buy_prob > sell_prob else "SELL"
        final_confidence = max(buy_prob, sell_prob) * 100
        
        # Adjust confidence based on technical confluence (example)
        if direction == "BUY" and features.get("close", 0) > features.get("SMA_200", float('inf')) or direction == "SELL" and features.get("close", float('inf')) < features.get("SMA_200", 0):
            final_confidence = min(100, final_confidence + 5)
            
        return {
            "direction": direction,
            "final_confidence": round(final_confidence, 2),
            "risk_score": round(100 - final_confidence, 2), # Simplified risk
            "expected_move_pct": sum(p["expected_move_pct"] for p in predictions) / len(predictions),
            "expected_hold_time_hours": sum(p["expected_hold_time_hours"] for p in predictions) / len(predictions),
            "target_price": sum(p["target_price"] for p in predictions) / len(predictions),
            "stop_price": sum(p["stop_price"] for p in predictions) / len(predictions),
            "models_used": [p["model_id"] for p in predictions],
            "ai_reasoning": f"Consensus reached {direction} with {final_confidence:.1f}% confidence across {len(predictions)} models."
        }
