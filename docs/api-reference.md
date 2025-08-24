# API Reference - PBOTS

## Przegląd API

PBOTS API to RESTful API zbudowane na FastAPI, które oferuje endpointy do zadawania pytań o Politechnikę Bydgoską oraz zarządzania bazą wiedzy uczelni.

**Base URL:** `http://localhost:8000`

## Endpointy

### 1. Zadawanie pytań (Streaming)

```http
POST /ask/stream
```

Główny endpoint do zadawania pytań o Politechnikę Bydgoską. Zwraca odpowiedź w formie strumienia tekstu, umożliwiając wyświetlanie odpowiedzi w czasie rzeczywistym.

#### Request Body

```json
{
  "question": "string"
}
```

| Parametr | Typ | Wymagany | Opis |
|----------|-----|----------|------|
| question | string | Tak | Pytanie dotyczące Politechniki Bydgoskiej (studia, administracja, infrastruktura, itp.) |

#### response

- **Content-Type:** `text/plain`
- **Format:** Streaming text response
- **Status Code:** 200 OK

#### Przykłady użycia

```bash
# Pytanie o kierunki studiów
curl -X POST http://localhost:8000/ask/stream \
  -H "Content-Type: application/json" \
  -d '{"question": "Jakie kierunki studiów oferuje Politechnika Bydgoska?"}'

# Pytanie o procedury administracyjne
curl -X POST http://localhost:8000/ask/stream \
  -H "Content-Type: application/json" \
  -d '{"question": "Jak złożyć wniosek o stypendium socjalne?"}'

# Pytanie o infrastrukturę
curl -X POST http://localhost:8000/ask/stream \
  -H "Content-Type: application/json" \
  -d '{"question": "Gdzie znajduje się biblioteka główna PBŚ?"}'
```

#### Przykładowe odpowiedzi

```
Pytanie: "Jakie kierunki studiów oferuje Politechnika Bydgoska?"

Odpowiedź: Politechnika Bydgoska oferuje szeroki wybór kierunków studiów na różnych wydziałach:

**Wydział Telekomunikacji, Informatyki i Elektrotechniki:**
- Informatyka stosowana 
- Telekomunikacja i technologie internetu rzeczy
- Elektrotechnika
- 
**Wydział Sztuk Projektowych:**
- Architektura Wnętrz
- Komunikacja Wizualna
- Wzornictwo

**Wydział Inżynierii Mechanicznej:**
- Inżynieria odnawialnych źródeł energii
- Inżynieria w medycynie
- Mechanika i budowa maszyn

...oraz wiele innych kierunków. Szczegółowe informacje dostępne są na stronie internetowej uczelni.
```

#### Obsługa błędów

| Kod błędu | Opis | Przykład odpowiedzi |
|-----------|------|-------------------|
| 400 | Nieprawidłowe żądanie | `{"detail": "Pole 'question' jest wymagane"}` |
| 422 | Błąd walidacji danych | `{"detail": "Pytanie nie może być puste"}` |
| 500 | Błąd serwera | `{"detail": "Wewnętrzny błąd serwera"}` |

---

### 2. Generowanie bazy wiedzy

```http
POST /generate_database
```

Endpoint administratorski do generowania/odświeżania bazy wektorowej z dokumentami Politechniki Bydgoskiej.

#### Request

Nie wymaga parametrów w body.

#### Response

```json
{
  "status": "success",
  "message": "Baza wiedzy została pomyślnie wygenerowana",
  "documents_processed": 150,
  "timestamp": "2025-01-23T10:30:00Z"
}
```

#### Przykład użycia

```bash
curl -X POST http://localhost:8000/generate_database \
  -H "Content-Type: application/json"
```

---

### 3. Status systemu

```http
GET /health
```

Sprawdza status zdrowia systemu i połączeń z bazami danych.

#### Response

```json
{
  "status": "healthy",
  "qdrant_connection": "ok",
  "ai_model": "operational",
  "timestamp": "2025-01-23T10:30:00Z"
}
```

