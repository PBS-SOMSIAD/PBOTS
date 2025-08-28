import requests
import json
import os

headers = {
    "Accept": "application/json",
    "User-Agent": "Mozilla/5.0"
}

# Utwórz folder na dane jeśli nie istnieje
output_dir = "unispace_data"
os.makedirs(output_dir, exist_ok=True)

# Mapowanie kodów na nazwy jednostek
unit_names = {
    "01": "Wydział Budownictwa, Architektury i Inżynierii Środowiska",
    "02": "Wydział Technologii i Inżynierii Chemicznej",
    "03": "Wydział Inżynierii Mechanicznej",
    "04": "Wydział Rolnictwa i Biotechnologii",
    "05": "Wydział Telekomunikacji, Informatyki i Elektrotechniki",
    "06": "Wydział Hodowli i Biologii Zwierząt",
    "08": "Wydział Zarządzania",
    "09": "Studium Języków Obcych",
    "14": "Szkoła Doktorska",
    "15": "Wydział Sztuk Projektowych",
    "16": "Akademickie Centrum Sportu",
    "17": "Wydział Medyczny",
    "99": "Administracja Centralna"
}

# Lista kodów jednostek (można łatwo dodać nowe)
unit_codes = list(unit_names.keys())

# Lista kodów jednostek - iteruj np. po 0-100
# unit_codes += [f"{i:02d}" for i in range(0, 101)]
# --- add automatic scraping for new unit codes (check if possible) ---

for code in unit_codes:
    url = f"https://unispace.pbs.edu.pl/api/search-provider/employee/find-all-by-sub-unit-code?subUnitCode={code}"
    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        try:
            employees = response.json()
            print(f"Pobrano {len(employees)} wyników dla kodu jednostki '{code}'")

            # Nazwa jednostki lub kod jeśli brak w słowniku
            unit_name = unit_names.get(code, code)
            safe_unit_name = unit_name.replace("/", "_").replace(",", "").replace(" ", "_")

            # Ścieżki plików dynamicznie z nazwą jednostki
            json_raw_file = os.path.join(output_dir, f"{unit_name}.json")

            # Zapis oryginalnego JSON
            with open(json_raw_file, "w", encoding="utf-8") as f:
                json.dump(employees, f, indent=4, ensure_ascii=False)
            print(f"Plik JSON zapisany dla jednostki {unit_name}:\n- {json_raw_file}")

        except Exception as e:
            print(f"Błąd przy przetwarzaniu kodu {code}:", e)
    else:
        print(f"Błąd HTTP dla kodu {code}: {response.status_code}")