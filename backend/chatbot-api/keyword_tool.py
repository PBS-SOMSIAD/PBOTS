import json
import unicodedata

titles = ['prof', 'dr', 'dr hab', 
          'wykladowca', 'profesor', 'pan', 'pani']

def normalize_text(text: str) -> str:
    """Usuwa polskie znaki, zamienia litery na małe, usuwa spacje."""
    if not isinstance(text, str):
        return ""
    normalized = unicodedata.normalize("NFD", text)
    normalized = normalized.encode("ascii", "ignore").decode("utf-8")
    return normalized.lower().strip()

def normalize_title(title: str) -> str:
    """Normalizuje tytuł — usuwa kropki, spacje i diakrytyki."""
    return normalize_text(title.replace(".", ""))

def rule_function(message: str, data: list): #normalizacja danych
    normalized_message = normalize_text(message)
    words = normalized_message.split()

    found_title = None
    for word in words:
        if normalize_title(word) in titles:
            found_title = word
            break
    if not found_title:
        return False

    # --- 2️⃣ Przygotowujemy dane znormalizowane ---
    all_first_names = [normalize_text(p["firstName"]) for p in data if "firstName" in p]
    all_last_names = [normalize_text(p["lastName"]) for p in data if "lastName" in p]

    # --- 3️⃣ Szukamy nazwiska ---
    found_last = None
    for word in words:
        if word in all_last_names:
            found_last = word
            break
    if not found_last:
        return False

    # --- 4️⃣ Szukamy osób o tym nazwisku ---
    matching_people = [p for p in data if normalize_text(p["lastName"]) == found_last]
    if not matching_people:
        return False

    # --- 5️⃣ Szukamy imienia w wiadomości ---
    found_first = None
    for word in words:
        if word in all_first_names:
            found_first = word
            break

    # --- 6️⃣ Jeśli znaleziono tylko nazwisko, ale wiele osób ---
    if not found_first and len(matching_people) > 1:
        imiona = [p["firstName"] for p in matching_people]
        print(f"Znalazłem kilka osób o nazwisku {matching_people[0]['lastName']}: {', '.join(imiona)}")
        wybor = input("O którego chodzi? Podaj imię: ").strip()

        # 🔹 normalizacja odpowiedzi użytkownika
        wybor_norm = normalize_text(wybor)

        for p in matching_people:
            if normalize_text(p["firstName"]) == wybor_norm:
                return f"Znalazłem {found_title} {p['firstName']} {p['lastName']}", True

        return "Nie znalazłem takiej osoby.", False

    # --- 7️⃣ Jeśli znaleziono pełne dane (imię + nazwisko) ---
    if found_first:
        for p in matching_people:
            if normalize_text(p["firstName"]) == found_first:
                return f"Znalazłem {found_title} {p['firstName']} {p['lastName']}", True

    # --- 8️⃣ Jeśli tylko jedna osoba o tym nazwisku ---
    if len(matching_people) == 1:
        p = matching_people[0]
        return f"Znalazłem {found_title} {p['firstName']} {p['lastName']}", True

    return False


# --- 🔹 Przykład działania ---
if __name__ == "__main__":
    with open("Wydział Telekomunikacji, Informatyki i Elektrotechniki.json", "r", encoding="utf-8") as f:
        data = json.load(f)

    test_input = "Czy pan dr choras jest gitem?"
    result = rule_function(test_input, data)
    print(result)
