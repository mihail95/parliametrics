def clean_name(raw_name: str) -> str:
    """
    Remove prefix like 'Парламентарна група (на)' from the name.
    """
    cleaned = raw_name.strip()
    if cleaned.startswith("Парламентарна група на "):
        cleaned = cleaned.replace("Парламентарна група на ", "")
    elif cleaned.startswith("Парламентарна група "):
        cleaned = cleaned.replace("Парламентарна група ", "")
    cleaned = cleaned.replace('\\"', '"')
    cleaned = cleaned.replace('"', '')
    return cleaned.strip(' "')