import math

from app.forecast_engine.base.models import ForecastResult


class ForecastValidator:
    """
    Validates standardized ForecastResult outputs.
    Rejects NaNs, infinites, out-of-bounds probabilities, and invalid direction states.
    """

    VALID_DIRECTIONS = {"BULLISH", "BEARISH", "NEUTRAL"}

    @classmethod
    def validate(cls, result: ForecastResult) -> tuple[bool, list[str]]:
        """
        Validates the given ForecastResult.
        
        :return: (is_valid, list_of_errors)
        """
        errors = []

        # 1. Check Direction
        if result.direction not in cls.VALID_DIRECTIONS:
            errors.append(f"Invalid direction: '{result.direction}'. Must be one of {cls.VALID_DIRECTIONS}")

        # 2. Check Confidence Bounds
        if not (0.0 <= result.confidence <= 1.0):
            errors.append(f"Confidence out of bounds: {result.confidence}. Must be between 0.0 and 1.0")

        # 3. Check Probability Bounds (if provided)
        if result.probability is not None:
            if not (0.0 <= result.probability <= 1.0):
                errors.append(f"Probability out of bounds: {result.probability}. Must be between 0.0 and 1.0")

        # 4. Check for NaN or Infinity in numeric fields
        numeric_fields = {
            "expected_move_pct": result.expected_move_pct,
            "expected_volatility": result.expected_volatility,
        }
        
        for field_name, value in numeric_fields.items():
            if value is not None:
                if math.isnan(value):
                    errors.append(f"{field_name} is NaN")
                elif math.isinf(value):
                    errors.append(f"{field_name} is infinite")

        # 5. Check logical inconsistencies
        if result.direction == "NEUTRAL" and result.expected_move_pct is not None and abs(result.expected_move_pct) > 5.0:
             # Just a logical warning/error: a large expected move shouldn't be 'NEUTRAL'
             errors.append("Direction is NEUTRAL but expected_move_pct is unusually large.")
             
        if result.expected_hold_candles is not None and result.expected_hold_candles <= 0:
            errors.append("expected_hold_candles must be > 0.")

        is_valid = len(errors) == 0
        return is_valid, errors

forecast_validator = ForecastValidator()
