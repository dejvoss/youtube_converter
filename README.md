# Konwerter YouTube do MP3 i MP4

Prosta aplikacja konsolowa dla systemu Windows, zaprojektowana tak, aby dobrze
współpracowała z czytnikami ekranu (NVDA, JAWS). Wklejasz link do filmu z
YouTube, wybierasz format (dźwięk MP3 albo film MP4), a program zapisuje plik
w folderze Pobrane.

- Jeden plik `.exe`, bez instalacji.
- Bez przeglądarki, bez reklam, bez konta.
- Wszystkie komunikaty po polsku.
- Brak paska postępu, który spamowałby czytnikiem ekranu – program mówi tylko,
  co trzeba, w pełnych zdaniach.
- Krótki sygnał dźwiękowy po zakończeniu (inny dla sukcesu, inny dla błędu).

## Jak uruchomić

1. Pobierz `KonwerterMP3.exe` ze strony Releases.
2. Zapisz plik w dowolnym miejscu, na przykład na pulpicie.
3. Uruchom go dwukrotnym kliknięciem lub naciśnięciem Enter w menedżerze plików.

Przy pierwszym uruchomieniu program pobierze dwa pomocnicze pliki
(`yt-dlp.exe` i `ffmpeg.exe`). Powie o tym głosem i poczekasz około minuty.
Potem już uruchamia się natychmiast.

### Windows SmartScreen

Przy pierwszym uruchomieniu system Windows może wyświetlić okno zabezpieczeń
SmartScreen z napisem „System Windows chronił Twój komputer”. W tym oknie:

1. Naciśnij „Więcej informacji”.
2. Następnie naciśnij „Uruchom mimo to”.

To normalne zachowanie dla nowych, niepodpisanych plików `.exe`.

## Jak używać

Po uruchomieniu program odczyta:

> Konwerter YouTube do MP3 i MP4.
>
> Wklej link i naciśnij Enter. Aby zakończyć, naciśnij Enter bez wpisywania niczego.

Wklej link (Ctrl+V) i naciśnij Enter. Program zapyta o format:

> Wybierz format. Wpisz 1, aby pobrać dźwięk MP3, albo 2, aby pobrać film MP4.
> Sam Enter wybiera MP3.

- `1` (albo `mp3`) — sam dźwięk, plik `.mp3`.
- `2` (albo `mp4`, `film`) — film z dźwiękiem, plik `.mp4` (H.264 + AAC,
  otworzy go każdy odtwarzacz w Windows).
- Sam Enter — ostatnio wybrany format (na początku MP3).

Potem poczekaj. Usłyszysz:

- „Pobieram: *tytuł filmu*.”
- „Pobrano 25 procent.” — i podobnie dla 50 i 75.
- „Konwertuję do MP3.” (dla MP3) albo „Łączę obraz z dźwiękiem.” (dla MP4).
- Krótki sygnał dźwiękowy.
- „Gotowe. Zapisano plik *tytuł*.mp3 (lub .mp4) w folderze Pobrane.”

Po zakończeniu program zapyta o kolejny link. Aby zakończyć, naciśnij Enter
bez wpisywania niczego.

Jeśli w chwili startu w schowku masz już link do YouTube, program to wykryje i
powie: „W schowku jest link do YouTube. Naciśnij Enter, aby go pobrać, albo
wklej inny.” Wtedy wystarczy nacisnąć Enter.

## Sygnały dźwiękowe

Program celowo używa krótkich sygnałów dźwiękowych zamiast dodatkowych
komunikatów głosowych, żeby nie przeszkadzać czytnikowi ekranu i żeby
szybciej rozpoznać wynik „uchem", bez czekania aż NVDA skończy czytać.

- **Sukces** — krótki, wysoki dźwięk (systemowy dźwięk „Asterisk" / „Gwiazdka").
  Oznacza: plik MP3 lub MP4 został zapisany w folderze Pobrane.
- **Błąd** — niski, ostrzegawczy dźwięk (systemowy „Critical Stop" / „Zatrzymanie
  krytyczne"). Oznacza: coś poszło nie tak (np. zły link, prywatny film, brak
  internetu). Po dźwięku program i tak powie głosem, co się stało.

Dźwięki pochodzą z motywu dźwiękowego systemu Windows, więc brzmią znajomo
i można je zmienić w **Panel sterowania → Dźwięk → zakładka Dźwięki**
(odpowiednio zdarzenia „Gwiazdka" i „Zatrzymanie krytyczne"). Jeśli masz
Windows w trybie wyciszonym, dźwięków nie usłyszysz — ale komunikaty głosowe
czytnika ekranu i tak zawsze się pojawią.

## Gdzie są pliki

- Plik `.exe`: tam, gdzie go zapisałeś.
- Pliki pomocnicze (`yt-dlp.exe`, `ffmpeg.exe`, `log.txt`):
  `%LOCALAPPDATA%\KonwerterMP3\`.
- Pobrane piosenki i filmy: w folderze Pobrane (jeśli masz go przeniesionego do
  OneDrive, program to uwzględni).

## Obsługiwane linki

- `https://www.youtube.com/watch?v=...`
- `https://youtu.be/...`
- `https://music.youtube.com/watch?v=...`
- `https://m.youtube.com/watch?v=...`
- Shorts, Live, Embed

Linki zawierające `&list=` są pobierane jako pojedynczy film (bez całej playlisty).

## Błędy

Program tłumaczy typowe błędy na zwykły polski język:

- „Brak połączenia z internetem. Sprawdź połączenie i spróbuj ponownie.”
- „Film jest prywatny i nie można go pobrać.”
- „Film został usunięty lub jest niedostępny.”
- „Film ma ograniczenie wieku i nie można go pobrać bez logowania.”
- „Nie rozpoznaję tego linku jako filmu z YouTube.”

Pełny dziennik techniczny jest w pliku `%LOCALAPPDATA%\KonwerterMP3\log.txt`.

## Budowanie ze źródeł

Wymaga Pythona 3.12.

```powershell
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements-dev.txt
pytest
pyinstaller --noconfirm --clean KonwerterMP3.spec
```

Gotowy plik znajdziesz w `dist\KonwerterMP3.exe`.

## Dla deweloperów

Testy jednostkowe (walidacja linków, parsowanie postępu, mapowanie błędów,
wykrywanie folderu Pobrane) są niezależne od Windows i przechodzą na Linuxie.

GitHub Actions (`.github/workflows/build.yml`) uruchamia testy na Linuxie i
buduje `.exe` na `windows-latest`. Przy tagu `v*` plik jest automatycznie
dołączany do release.

## Ręczny test dostępności z NVDA

Poniższa procedura sprawdza, czy aplikacja zachowuje się poprawnie z czytnikiem
ekranu – przede wszystkim, czy NVDA **nie** czyta spamu w stylu „pobieram
jeden procent, pobieram dwa procent, pobieram trzy procent”.

### Przygotowanie

1. Zainstaluj NVDA ze strony <https://www.nvaccess.org/>.
2. Uruchom NVDA. W trybie mowy: `Insert + S` → *Mowa*.
3. Przekopiuj `KonwerterMP3.exe` na pulpit.

### Scenariusz 1 — uruchomienie i pobranie pliku

1. Zaznacz `KonwerterMP3.exe` i naciśnij Enter. NVDA powinien odczytać tytuł
   okna terminala, a następnie zdanie: *„Konwerter YouTube do MP3.”*
2. Przy pierwszym uruchomieniu usłyszysz: *„Pierwsze uruchomienie. Pobieram
   potrzebne pliki, to potrwa około minuty.”* Po chwili: *„Pliki pobrane.
   Program jest gotowy do użycia.”*
3. Następnie: *„Wklej link i naciśnij Enter. Aby zakończyć, naciśnij Enter bez
   wpisywania niczego.”*
4. Skopiuj do schowka link do krótkiego, publicznego filmu (najlepiej
   30-sekundowego), wklej `Ctrl+V`, naciśnij Enter.
4a. NVDA odczyta pytanie o format. Naciśnij Enter (MP3). Powtórz scenariusz
   z `2` i Enter — powinien powstać plik `.mp4`, a zamiast „Konwertuję do
   MP3” usłyszysz „Łączę obraz z dźwiękiem.”
5. **Krytyczne:** w trakcie pobierania NVDA powinien odczytać **tylko** cztery
   zdania, każde raz:
   - „Pobieram: *tytuł filmu*.”
   - „Pobrano 25 procent.”
   - „Pobrano 50 procent.”
   - „Pobrano 75 procent.”
   - „Konwertuję do MP3.”
   - „Gotowe. Zapisano plik *tytuł*.mp3 w folderze Pobrane.”
6. Jeśli słyszysz procenty co pół sekundy („cztery procent, pięć procent,
   sześć procent…”) — to jest błąd dostępności, zgłoś go.
7. Po sukcesie powinien zabrzmieć krótki sygnał dźwiękowy.
8. Otwórz folder Pobrane (`Win + E`, nawiguj do „Pobrane”) i upewnij się, że
   plik `.mp3` jest.

### Scenariusz 2 — schowek wykryty przy starcie

1. Skopiuj link do YouTube (`Ctrl+C`) **zanim** uruchomisz program.
2. Uruchom `KonwerterMP3.exe`. NVDA powinien odczytać: *„W schowku jest link
   do YouTube. Naciśnij Enter, aby go pobrać, albo wklej inny.”*
3. Naciśnij Enter. Program powinien rozpocząć pobieranie bez konieczności
   wklejania linku.

### Scenariusz 3 — zły link

1. Po uruchomieniu wpisz `to nie jest link` i naciśnij Enter.
2. NVDA powinien odczytać: *„To nie wygląda na link do YouTube. Wklej link
   zaczynający się od https.”*
3. Powinien zabrzmieć inny sygnał dźwiękowy (błąd) niż przy sukcesie.
4. Program powinien poprosić o kolejny link, a nie wyjść.

### Scenariusz 4 — brak internetu

1. Odłącz Wi-Fi.
2. Uruchom program, wklej dowolny poprawny link YouTube i wybierz format.
3. NVDA powinien odczytać: *„Brak połączenia z internetem. Sprawdź połączenie
   i spróbuj ponownie.”* — bez technicznego tracebacka.

### Scenariusz 5 — zamknięcie

1. Gdy program pyta o kolejny link, naciśnij Enter bez wpisywania niczego.
2. NVDA powinien odczytać: *„Do widzenia.”* i okno terminala się zamknie.

### Znane „nie-błędy”

- SmartScreen przy pierwszym uruchomieniu — to normalne zachowanie Windows
  dla niepodpisanych plików `.exe`. NVDA przeczyta nazwę przycisku *„Więcej
  informacji”* — naciśnij go, a potem *„Uruchom mimo to”*.
- Przy pierwszym uruchomieniu pobranie pomocniczych plików może zająć do
  minuty. Program milczy w tym czasie — to nie jest zawieszenie.

## Licencje

- `yt-dlp` — Unlicense: <https://github.com/yt-dlp/yt-dlp>
- `ffmpeg` (build „yt-dlp/FFmpeg-Builds”, GPL) — <https://github.com/yt-dlp/FFmpeg-Builds>

Program nie zawiera tych plików – pobiera je przy pierwszym uruchomieniu z ich
oficjalnych stron Releases.
