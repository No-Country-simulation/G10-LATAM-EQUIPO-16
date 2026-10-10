import csv
from pathlib import Path

from models import Interaction


def load_csv(file_path: str) -> list[Interaction]:
    """Carga interacciones de comunidad desde un archivo CSV."""

    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(
            f"No se encontró el archivo: {file_path}"
        )

    if path.suffix.lower() != ".csv":
        raise ValueError(
            "El archivo debe tener extensión .csv"
        )

    interactions = []

    with path.open(
        "r",
        encoding="utf-8-sig",
        newline="",
    ) as file:
        reader = csv.DictReader(file)

        for row in reader:
            interaction = Interaction(
                autor=row["autor"],
                canal=row["canal"],
                tipo=row["tipo"],
                texto=row["texto"],
            )

            interactions.append(interaction)

    return interactions