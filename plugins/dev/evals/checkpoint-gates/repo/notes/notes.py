NOTES = []


def add_note(text, tags=()):
    NOTES.append({"text": text, "tags": list(tags)})


def list_notes():
    return list(reversed(NOTES))


def search_by_tag(tag):
    return []  # TODO T3
