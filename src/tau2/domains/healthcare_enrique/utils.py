import os


def get_data_path(filename: str) -> str:
    """Devuelve la ruta absoluta a los archivos de data del dominio"""
    
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    
    return os.path.join(
        base_dir,
        "data",
        "tau2",
        "domains",
        "healthcare_enrique",
        filename
    )