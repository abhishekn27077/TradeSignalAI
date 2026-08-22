import sys
import os
import traceback

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.analytics.models.kronos.kronos import Kronos, KronosTokenizer

def test_load():
    model_name = "NeoQuasar/Kronos-mini"
    tokenizer_name = "NeoQuasar/Kronos-Tokenizer-base"
    try:
        print("Loading tokenizer...")
        tokenizer = KronosTokenizer.from_pretrained(tokenizer_name)
        print("Loading model...")
        model = Kronos.from_pretrained(model_name)
        print("Success!")
    except Exception as e:
        print("Error:")
        traceback.print_exc()

if __name__ == "__main__":
    test_load()
