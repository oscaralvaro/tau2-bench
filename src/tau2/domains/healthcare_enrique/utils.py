import os


def get_data_path(filename: str) -> str:
    """
    Retorna la ruta correcta a los archivos del dominio
    """

    # subir hasta la raíz del proyecto
    base_dir = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "../../../../")
    )

    data_dir = os.path.join(
        base_dir,
        "data",
        "tau2",
        "domains",
        "healthcare_enrique"
    )

    return os.path.join(data_dir, filename)