from .adapter import KronosAdapter

model_dict = {
    'kronos_adapter': KronosAdapter
}

def get_model_class(model_name):
    if model_name in model_dict:
        return model_dict[model_name]
    else:
        print(f"Model {model_name} not found in model_dict")
        raise NotImplementedError
