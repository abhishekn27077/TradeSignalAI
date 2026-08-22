class EventClassifier:
    """
    Detects specific macro-economic events from text.
    """
    EVENTS = {
        "NFP": ["nonfarm payroll", "nfp", "jobs report"],
        "FOMC": ["fomc", "federal reserve", "fed rate"],
        "CPI": ["cpi", "consumer price index", "inflation rate"],
        "GDP": ["gdp", "gross domestic product"]
    }

    @staticmethod
    def classify(text: str) -> str:
        text_lower = text.lower()
        for event, triggers in EventClassifier.EVENTS.items():
            for trigger in triggers:
                if trigger in text_lower:
                    return event
        return None

class TopicDetection:
    """
    Detects general overarching topics of the article.
    """
    TOPICS = {
        "Macroeconomics": ["economy", "inflation", "recession", "gdp"],
        "Monetary Policy": ["interest rate", "central bank", "fed", "ecb"],
        "Geopolitics": ["war", "sanctions", "election", "treaty"]
    }
    
    @staticmethod
    def detect(text: str) -> list:
        detected = []
        text_lower = text.lower()
        for topic, keywords in TopicDetection.TOPICS.items():
            if any(kw in text_lower for kw in keywords):
                detected.append(topic)
        return detected
