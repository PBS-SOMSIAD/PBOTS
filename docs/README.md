# PBOTS — Bot Politechniki Bydgoskiej

## Przegląd

PBOTS to inteligentny system RAG zaprojektowany do odpowiadania na pytania dotyczące Politechniki Bydgoskiej. Aplikacja wykorzystuje zaawansowane techniki AI do wyszukiwania informacji w bazie wiedzy uczelni oraz w internecie, aby udzielać precyzyjnych odpowiedzi na tematy związane z:

- **Kierunkami studiów** - informacje o programach kształcenia, planach studiów, wymaganiach
- **Procesami administracyjnymi** - procedury rekrutacji, zapisy na przedmioty, legitymacje
- **Życiem studenckim** - akademiki, stypendia, organizacje studenckie, wydarzenia
- **Pracą naukową** - instytuty, laboratoria, projekty badawcze, publikacje
- **Infrastrukturą** - budynki, sale, biblioteka, laboratoria
- **Kontaktami** - dziekany, pracownicy, godziny urzędowania

## Architektura

### Komponenty systemu

1. **Backend (FastAPI)** - Serwer API obsługujący zapytania i zarządzający bazą wiedzy PB
2. **Frontend (Next.js)** - Interfejs użytkownika do interakcji z botem
3. **Baza wektorowa (Qdrant)** - Przechowywanie i wyszukiwanie dokumentów uczelni
4. **Model AI (Qwen)** - Generowanie odpowiedzi na podstawie kontekstu uczelni



## Funkcjonalności

### Główne funkcje

- **Inteligentne odpowiadanie na pytania** - System analizuje pytania i dostarcza szczegółowe odpowiedzi o Politechnice Bydgoskiej
- **Wyszukiwanie w bazie wiedzy** - Wykorzystuje wektorową bazę danych z oficjalnymi dokumentami uczelni
- **Wyszukiwanie internetowe** - Uzupełnia wiedzę o najnowsze informacje ze strony PB i innych źródeł
- **Filtrowanie tematyczne** - Odpowiada tylko na pytania związane z Politechniką Bydgoską
- **Streaming odpowiedzi** - Wyświetla odpowiedzi w czasie rzeczywistym
- **Interfejs czatu** - Przyjazny interfejs do konwersacji z botem

### Zaawansowane możliwości

- **Hybrydowe wyszukiwanie** - Łączy wyszukiwanie semantyczne z BM25
- **Chunking dokumentów** - Inteligentne dzielenie dokumentów uczelni na fragmenty
- **Weryfikacja intencji** - Sprawdza czy pytanie dotyczy PB przed przetworzeniem
- **Monitoring i logowanie** - Pełne śledzenie działania systemu
- **Wsparcie wielojęzyczne** - Odpowiedzi w języku polskim i angielskim

## Struktura projektu

## Przykłady pytań

Bot jest przygotowany do odpowiadania na różnorodne pytania dotyczące Politechniki Bydgoskiej:

### Pytania o studia
- "Jakie są wymagania na kierunek Informatyka Stosowana?"
- "Ile kosztują studia na Politechnice Bydgoskiej?"
- "Kiedy są zapisy na wychowanie fizyczne?"

### Pytania administracyjne
- "Jak złożyć wniosek o stypendium?"
- "Gdzie mogę załatwić legitymację studencką?"
- "Jakie są godziny otwarcia dziekanatu?"

### Pytania o infrastrukturę
- "Gdzie znajduje się Wydział Telekomunikacji, Informatyki i Elektrotechniki?"
- "Jakie są godziny otwarcia biblioteki?"
- "Czy jest parking dla studentów?"

## Technologie

### Backend
- **FastAPI** - Framework webowy Python
- **Qdrant** - Baza wektorowa
- **Pydantic AI** - Framework AI
- **OpenAI API** - Model językowy
- **Logfire** - Monitoring i logowanie

### Frontend
- **Next.js** - Framework React
- **React** - Biblioteka UI
- **JavaScript** - Język programowania

### Infrastruktura
- **Docker** - Konteneryzacja
- **Docker Compose** - Orkiestracja kontenerów

## Bezpieczeństwo i prywatność

- Wszystkie dane są przetwarzane zgodnie z RODO
- System nie przechowuje danych osobowych użytkowników
- Komunikacja jest szyfrowana
- Dostęp do API może być ograniczony przez tokeny autoryzacji

## Wsparcie i rozwój

Bot jest aktywnie rozwijany przez koło naukowe SOMSIAD Politechniki Bydgoskiej.
