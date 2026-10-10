import re

from models import Interaction


def anonymize_text(text: str, author: str) -> str:
    """Oculta el nombre conocido del autor dentro del texto."""

    if not author or not author.strip():
        return text

    name = author.strip()

    # Reemplaza el nombre completo, sin distinguir mayúsculas.
    pattern = re.compile(
        rf"(?<!\w){re.escape(name)}(?!\w)",
        flags=re.IGNORECASE,
    )

    return pattern.sub("[AUTOR]", text)


def anonymize_interaction(interaction: Interaction) -> Interaction:
    """Crea una copia anonimizada sin modificar el objeto original."""

    return interaction.model_copy(
        update={
            "autor": "Usuario anónimo",
            "texto": anonymize_text(
                interaction.texto,
                interaction.autor,
            ),
        }
    )