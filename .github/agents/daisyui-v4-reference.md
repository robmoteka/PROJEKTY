# DaisyUI v4 — Kompletna Referencja dla Agenta FrontMan

> Ten plik jest cheatsheetem DaisyUI v4 do użytku przez agenta FrontMan.
> Źródło: https://daisyui.com/components/ (65 komponentów)

---

## 🎨 System Kolorów (Semantic Colors)

**ZASADA:** Nigdy nie używaj hardkodowanych kolorów Tailwind (`bg-blue-500`). Używaj semantycznych nazw daisyUI.

### Nazwy kolorów

| Kolor               | CSS Variable               | Opis                                |
|----------------------|----------------------------|-------------------------------------|
| `primary`            | `--color-primary`          | Główny kolor marki                  |
| `primary-content`    | `--color-primary-content`  | Tekst na tle primary                |
| `secondary`          | `--color-secondary`        | Drugorzędny kolor marki             |
| `secondary-content`  | `--color-secondary-content`| Tekst na tle secondary              |
| `accent`             | `--color-accent`           | Kolor akcentowy                     |
| `accent-content`     | `--color-accent-content`   | Tekst na tle accent                 |
| `neutral`            | `--color-neutral`          | Kolor neutralny (ciemny)            |
| `neutral-content`    | `--color-neutral-content`  | Tekst na tle neutral                |
| `base-100`           | `--color-base-100`         | Bazowy kolor tła strony             |
| `base-200`           | `--color-base-200`         | Ciemniejszy odcień bazy (elewacja)  |
| `base-300`           | `--color-base-300`         | Jeszcze ciemniejszy odcień bazy     |
| `base-content`       | `--color-base-content`     | Tekst na tle base                   |
| `info`               | `--color-info`             | Informacyjny                        |
| `info-content`       | `--color-info-content`     | Tekst na tle info                   |
| `success`            | `--color-success`          | Sukces                              |
| `success-content`    | `--color-success-content`  | Tekst na tle success                |
| `warning`            | `--color-warning`          | Ostrzeżenie                         |
| `warning-content`    | `--color-warning-content`  | Tekst na tle warning                |
| `error`              | `--color-error`            | Błąd/niebezpieczeństwo              |
| `error-content`      | `--color-error-content`    | Tekst na tle error                  |

### Użycie kolorów w utility classes

```html
<!-- Tło -->
<div class="bg-primary">...</div>
<div class="bg-base-200">...</div>

<!-- Tekst -->
<p class="text-primary">...</p>
<p class="text-base-content/50">Przytłumiony tekst (50% opacity)</p>

<!-- Border -->
<div class="border border-base-300">...</div>

<!-- Ring -->
<div class="ring ring-primary">...</div>
```

### Opacity modyfikator
```html
<p class="text-base-content/70">70% opacity</p>
<div class="bg-primary/50">50% opacity tła</div>
```

---

## 📦 Komponenty — Pełna Referencja Klas

### Wspólne modyfikatory rozmiaru

Większość komponentów obsługuje: `{component}-xs`, `{component}-sm`, `{component}-md` (default), `{component}-lg`, `{component}-xl`

### Wspólne style

Wiele komponentów obsługuje: `{component}-outline`, `{component}-dash`, `{component}-soft`, `{component}-ghost`

### Wspólne kolory

Wiele komponentów obsługuje: `{component}-primary`, `{component}-secondary`, `{component}-accent`, `{component}-neutral`, `{component}-info`, `{component}-success`, `{component}-warning`, `{component}-error`

---

## 🔘 ACTIONS

### Button (`btn`)

```html
<button class="btn">Default</button>
<button class="btn btn-primary">Primary</button>
<button class="btn btn-secondary">Secondary</button>
<button class="btn btn-accent">Accent</button>
<button class="btn btn-neutral">Neutral</button>
<button class="btn btn-info">Info</button>
<button class="btn btn-success">Success</button>
<button class="btn btn-warning">Warning</button>
<button class="btn btn-error">Error</button>
```

| Klasa            | Typ       | Opis                          |
|------------------|-----------|-------------------------------|
| `btn`            | Component | Główna klasa przycisku        |
| `btn-neutral`    | Color     | neutral color                 |
| `btn-primary`    | Color     | primary color                 |
| `btn-secondary`  | Color     | secondary color               |
| `btn-accent`     | Color     | accent color                  |
| `btn-info`       | Color     | info color                    |
| `btn-success`    | Color     | success color                 |
| `btn-warning`    | Color     | warning color                 |
| `btn-error`      | Color     | error color                   |
| `btn-outline`    | Style     | outline style                 |
| `btn-dash`       | Style     | dash style                    |
| `btn-soft`       | Style     | soft style                    |
| `btn-ghost`      | Style     | ghost style                   |
| `btn-link`       | Style     | wygląda jak link              |
| `btn-active`     | Behavior  | wygląda na aktywny            |
| `btn-disabled`   | Behavior  | wygląda na wyłączony          |
| `btn-xs/sm/md/lg/xl` | Size | Rozmiary                     |
| `btn-wide`       | Modifier  | więcej paddingu horyzontalnego|
| `btn-block`      | Modifier  | pełna szerokość               |
| `btn-square`     | Modifier  | aspect ratio 1:1              |
| `btn-circle`     | Modifier  | 1:1 z zaokrąglonymi rogami   |

**Loading spinner w buttonie:**
```html
<button class="btn btn-primary">
  <span class="loading loading-spinner"></span>
  Loading
</button>
```

### Dropdown (`dropdown`)

| Klasa               | Typ       | Opis                                  |
|----------------------|-----------|---------------------------------------|
| `dropdown`           | Component | Kontener dropdown                     |
| `dropdown-content`   | Part      | Zawartość dropdown                    |
| `dropdown-start`     | Placement | Wyrównaj do początku (default)        |
| `dropdown-center`    | Placement | Wyrównaj do środka                    |
| `dropdown-end`       | Placement | Wyrównaj do końca                     |
| `dropdown-top`       | Placement | Otwieranie z góry                     |
| `dropdown-bottom`    | Placement | Otwieranie z dołu (default)           |
| `dropdown-left`      | Placement | Otwieranie z lewej                    |
| `dropdown-right`     | Placement | Otwieranie z prawej                   |
| `dropdown-hover`     | Modifier  | Otwieraj też na hover                 |
| `dropdown-open`      | Modifier  | Wymuś otwarcie                        |
| `dropdown-close`     | Modifier  | Wymuś zamknięcie                      |

**3 metody dropdown:**

```html
<!-- 1. details/summary (rekomendowane) -->
<details class="dropdown">
  <summary class="btn m-1">Open</summary>
  <ul class="dropdown-content menu bg-base-100 rounded-box z-1 w-52 p-2 shadow-sm">
    <li><a>Item 1</a></li>
    <li><a>Item 2</a></li>
  </ul>
</details>

<!-- 2. Popover API (nowe) -->
<button class="btn" style="anchor-name:--anchor-1" popovertarget="popover-1">Open</button>
<ul popover id="popover-1" class="dropdown-content menu bg-base-100 rounded-box z-1 w-52 p-2 shadow-sm" style="position-anchor:--anchor-1">
  <li><a>Item 1</a></li>
</ul>

<!-- 3. CSS Focus -->
<div class="dropdown">
  <div tabindex="0" role="button" class="btn m-1">Click</div>
  <ul tabindex="0" class="dropdown-content menu bg-base-100 rounded-box z-1 w-52 p-2 shadow-sm">
    <li><a>Item 1</a></li>
  </ul>
</div>
```

### Modal (`modal`)

| Klasa            | Typ       | Opis                                      |
|------------------|-----------|-------------------------------------------|
| `modal`          | Component | Główny kontener modala                     |
| `modal-box`      | Part      | Zawartość modala                           |
| `modal-action`   | Part      | Część z akcjami (przyciski)                |
| `modal-backdrop` | Part      | Label pokrywający stronę do zamknięcia     |
| `modal-toggle`   | Part      | Ukryty checkbox kontrolujący stan          |
| `modal-open`     | Modifier  | Wymuś otwarcie                             |
| `modal-top`      | Placement | Na górze                                   |
| `modal-middle`   | Placement | Na środku (default)                        |
| `modal-bottom`   | Placement | Na dole                                    |
| `modal-start`    | Placement | Wyrównaj do początku                       |
| `modal-end`      | Placement | Wyrównaj do końca                          |

**Rekomendowany sposób — dialog HTML:**
```html
<button class="btn" onclick="my_modal.showModal()">Otwórz</button>
<dialog id="my_modal" class="modal">
  <div class="modal-box">
    <h3 class="text-lg font-bold">Tytuł</h3>
    <p class="py-4">Treść modala</p>
    <div class="modal-action">
      <form method="dialog">
        <button class="btn">Zamknij</button>
      </form>
    </div>
  </div>
  <form method="dialog" class="modal-backdrop">
    <button>close</button>
  </form>
</dialog>
```

### Swap (`swap`)

| Klasa         | Typ       | Opis                     |
|---------------|-----------|--------------------------|
| `swap`        | Component | Kontener swap            |
| `swap-on`     | Part      | Widoczny gdy aktywny     |
| `swap-off`    | Part      | Widoczny gdy nieaktywny  |
| `swap-active` | Modifier  | Aktywuj stan swap        |
| `swap-rotate` | Style     | Rotacja przy przełączeniu|
| `swap-flip`   | Style     | Flip przy przełączeniu   |

---

## 📊 DATA DISPLAY

### Accordion (`accordion` = `collapse` group)

```html
<!-- Użyj collapse z name dla radio-group -->
<div class="collapse collapse-arrow bg-base-100 border border-base-300">
  <input type="radio" name="my-accordion-1" checked="checked" />
  <div class="collapse-title font-semibold">Tytuł 1</div>
  <div class="collapse-content">Treść 1</div>
</div>
<div class="collapse collapse-arrow bg-base-100 border border-base-300">
  <input type="radio" name="my-accordion-1" />
  <div class="collapse-title font-semibold">Tytuł 2</div>
  <div class="collapse-content">Treść 2</div>
</div>
```

### Avatar (`avatar`)

| Klasa            | Typ       | Opis                            |
|------------------|-----------|----------------------------------|
| `avatar`         | Component | Kontener awatara                 |
| `avatar-group`   | Component | Grupa awatarów                   |
| `online`         | Modifier  | Wskaźnik online                  |
| `offline`        | Modifier  | Wskaźnik offline                 |
| `placeholder`    | Modifier  | Placeholder gdy brak obrazu      |

```html
<div class="avatar">
  <div class="w-24 rounded-full">
    <img src="..." alt="Avatar użytkownika" />
  </div>
</div>
```

### Badge (`badge`)

| Klasa             | Typ    | Opis                 |
|-------------------|--------|----------------------|
| `badge`           | Component | Kontener badge    |
| `badge-outline`   | Style  | outline style        |
| `badge-dash`      | Style  | dash outline style   |
| `badge-soft`      | Style  | soft style           |
| `badge-ghost`     | Style  | ghost style          |
| `badge-neutral`   | Color  | neutral color        |
| `badge-primary`   | Color  | primary color        |
| `badge-secondary` | Color  | secondary color      |
| `badge-accent`    | Color  | accent color         |
| `badge-info`      | Color  | info color           |
| `badge-success`   | Color  | success color        |
| `badge-warning`   | Color  | warning color        |
| `badge-error`     | Color  | error color          |
| `badge-xs/sm/md/lg/xl` | Size | Rozmiary        |

```html
<span class="badge badge-primary">Primary</span>
<span class="badge badge-success badge-outline">Success</span>
```

### Card (`card`)

| Klasa          | Typ       | Opis                                   |
|----------------|-----------|----------------------------------------|
| `card`         | Component | Główna klasa karty                     |
| `card-title`   | Part      | Tytuł karty                            |
| `card-body`    | Part      | Ciało karty (treść)                    |
| `card-actions` | Part      | Akcje karty (przyciski)                |
| `card-border`  | Style     | Dodaje obramowanie                     |
| `card-dash`    | Style     | Styl dash                              |
| `card-side`    | Modifier  | Obraz z boku zamiast z góry            |
| `image-full`   | Modifier  | Obraz jako tło                         |
| `card-xs/sm/md/lg/xl` | Size | Rozmiary                         |

```html
<div class="card bg-base-100 shadow-xl">
  <figure>
    <img src="..." alt="Opis obrazu" />
  </figure>
  <div class="card-body">
    <h2 class="card-title">Tytuł</h2>
    <p>Opis</p>
    <div class="card-actions justify-end">
      <button class="btn btn-primary">Kup</button>
    </div>
  </div>
</div>
```

### Collapse (`collapse`)

| Klasa              | Typ       | Opis                               |
|--------------------|-----------|-------------------------------------|
| `collapse`         | Component | Kontener collapse                   |
| `collapse-title`   | Part      | Tytuł (klikalna część)              |
| `collapse-content` | Part      | Ukrywana zawartość                  |
| `collapse-arrow`   | Style     | Styl ze strzałką                    |
| `collapse-plus`    | Style     | Styl ze znakiem +/-                 |
| `collapse-open`    | Modifier  | Wymuś otwarcie                      |
| `collapse-close`   | Modifier  | Wymuś zamknięcie                    |

```html
<div class="collapse collapse-arrow bg-base-100 border border-base-300">
  <input type="checkbox" />
  <div class="collapse-title font-semibold">Kliknij, aby rozwinąć</div>
  <div class="collapse-content">
    <p>Ukryta treść</p>
  </div>
</div>
```

### Stat (`stat`)

| Klasa        | Typ       | Opis                     |
|--------------|-----------|--------------------------|
| `stats`      | Component | Kontener statystyk       |
| `stat`       | Part      | Pojedyncza statystyka    |
| `stat-title` | Part      | Tytuł statystyki         |
| `stat-value` | Part      | Wartość (duża)           |
| `stat-desc`  | Part      | Opis/dodatkowy tekst     |
| `stat-figure`| Part      | Ikona/obrazek            |
| `stats-vertical`   | Direction | Układ pionowy     |
| `stats-horizontal`  | Direction | Układ poziomy    |

```html
<div class="stats shadow">
  <div class="stat">
    <div class="stat-title">Łącznie zgłoszeń</div>
    <div class="stat-value">31K</div>
    <div class="stat-desc">Od 1 stycznia 2024</div>
  </div>
</div>
```

### Table (`table`)

| Klasa            | Typ       | Opis                                  |
|------------------|-----------|---------------------------------------|
| `table`          | Component | Dla tagu `<table>`                    |
| `table-zebra`    | Modifier  | Paski zebra na wierszach              |
| `table-pin-rows` | Modifier  | Sticky thead/tfoot                    |
| `table-pin-cols` | Modifier  | Sticky kolumny th                     |
| `table-xs/sm/md/lg/xl` | Size | Rozmiary                         |

```html
<div class="overflow-x-auto">
  <table class="table table-zebra">
    <thead>
      <tr>
        <th>#</th>
        <th>Nazwa</th>
        <th>Status</th>
      </tr>
    </thead>
    <tbody>
      <tr>
        <th>1</th>
        <td>Projekt A</td>
        <td><span class="badge badge-success">Active</span></td>
      </tr>
    </tbody>
  </table>
</div>
```

### List (`list`)

| Klasa       | Typ       | Opis                 |
|-------------|-----------|----------------------|
| `list`      | Component | Kontener listy       |
| `list-row`  | Part      | Wiersz listy         |

### Timeline (`timeline`)

| Klasa              | Typ       | Opis                                |
|--------------------|-----------|--------------------------------------|
| `timeline`         | Component | Kontener timeline                    |
| `timeline-start`   | Part      | Zawartość po lewej                   |
| `timeline-middle`  | Part      | Ikonka w środku                      |
| `timeline-end`     | Part      | Zawartość po prawej                  |
| `timeline-box`     | Part      | Box stylizowany                      |
| `timeline-compact` | Modifier  | Kompaktowy widok (jedna strona)      |
| `timeline-snap-icon` | Modifier | Icon snap                          |
| `timeline-vertical`   | Direction | Pionowy (default)               |
| `timeline-horizontal` | Direction | Poziomy                     |

### Chat Bubble (`chat`)

| Klasa           | Typ       | Opis                      |
|-----------------|-----------|---------------------------|
| `chat`          | Component | Kontener wiadomości       |
| `chat-start`    | Placement | Wiadomość od innych       |
| `chat-end`      | Placement | Własna wiadomość          |
| `chat-image`    | Part      | Awatar                    |
| `chat-header`   | Part      | Nagłówek (nazwa, czas)    |
| `chat-bubble`   | Part      | Tekst wiadomości          |
| `chat-footer`   | Part      | Stopka                    |

### Countdown (`countdown`)

```html
<span class="countdown font-mono text-6xl">
  <span style="--value:10;"></span>
</span>
```

### Kbd (`kbd`)

```html
<kbd class="kbd kbd-sm">Ctrl</kbd>+<kbd class="kbd kbd-sm">C</kbd>
```

---

## 🧭 NAVIGATION

### Breadcrumbs (`breadcrumbs`)

```html
<div class="breadcrumbs text-sm">
  <ul>
    <li><a>Home</a></li>
    <li><a>Projekty</a></li>
    <li>Szczegóły</li>
  </ul>
</div>
```

### Dock (Bottom Navigation) (`dock`)

| Klasa        | Typ       | Opis                          |
|--------------|-----------|-------------------------------|
| `dock`       | Component | Kontener (przyczepia do dołu) |
| `dock-label` | Part      | Etykieta pod ikoną            |
| `dock-active`| Modifier  | Aktywny element               |
| `dock-xs/sm/md/lg/xl` | Size | Rozmiary                |

```html
<div class="dock">
  <button class="dock-active">
    <svg>...</svg>
    <span class="dock-label">Home</span>
  </button>
  <button>
    <svg>...</svg>
    <span class="dock-label">Info</span>
  </button>
</div>
```

### Link (`link`)

| Klasa             | Typ   | Opis            |
|-------------------|-------|-----------------|
| `link`            | Component | Styl linku  |
| `link-hover`      | Modifier | Podkreślenie tylko na hover |
| `link-primary`    | Color | primary         |
| `link-secondary`  | Color | secondary       |
| `link-accent`     | Color | accent          |
| `link-neutral`    | Color | neutral         |
| `link-info`       | Color | info            |
| `link-success`    | Color | success         |
| `link-warning`    | Color | warning         |
| `link-error`      | Color | error           |

### Menu (`menu`)

| Klasa                  | Typ       | Opis                                    |
|------------------------|-----------|------------------------------------------|
| `menu`                 | Component | Dla `<ul>`                               |
| `menu-title`           | Part      | Stylizuje `<li>` jako tytuł              |
| `menu-dropdown`        | Part      | Składane `<ul>` (JS)                     |
| `menu-dropdown-toggle` | Part      | Przełącznik fold (JS)                    |
| `menu-disabled`        | Modifier  | Wyłączony wygląd                         |
| `menu-active`          | Modifier  | Aktywny wygląd                           |
| `menu-focus`           | Modifier  | Sfokusowany wygląd                       |
| `menu-dropdown-show`   | Modifier  | Pokaż składane submenu (JS)              |
| `menu-xs/sm/md/lg/xl`  | Size      | Rozmiary                                 |
| `menu-vertical`        | Direction | Pionowe (default)                        |
| `menu-horizontal`      | Direction | Poziome                                  |

```html
<ul class="menu bg-base-200 rounded-box w-56">
  <li class="menu-title">Nawigacja</li>
  <li><a>Dashboard</a></li>
  <li><a class="menu-active">Projekty</a></li>
  <li><a>Zgłoszenia</a></li>
</ul>
```

### Navbar (`navbar`)

| Klasa          | Typ       | Opis                         |
|----------------|-----------|------------------------------|
| `navbar`       | Component | Pasek nawigacji              |
| `navbar-start` | Part      | Lewa część (50% szerokości)  |
| `navbar-center`| Part      | Środek                       |
| `navbar-end`   | Part      | Prawa część (50%)            |

```html
<div class="navbar bg-base-100">
  <div class="navbar-start">
    <a class="btn btn-ghost text-xl">IT Project OS</a>
  </div>
  <div class="navbar-center hidden lg:flex">
    <ul class="menu menu-horizontal px-1">
      <li><a>Dashboard</a></li>
      <li><a>Projekty</a></li>
    </ul>
  </div>
  <div class="navbar-end">
    <a class="btn btn-primary">Zaloguj</a>
  </div>
</div>
```

### Pagination (`pagination`)

```html
<div class="join">
  <button class="join-item btn">«</button>
  <button class="join-item btn btn-active">1</button>
  <button class="join-item btn">2</button>
  <button class="join-item btn">3</button>
  <button class="join-item btn">»</button>
</div>
```

### Steps (`steps`)

| Klasa              | Typ       | Opis                         |
|--------------------|-----------|-------------------------------|
| `steps`            | Component | Kontener kroków               |
| `step`             | Part      | Pojedynczy krok               |
| `step-icon`        | Part      | Własna ikonka w kroku         |
| `step-primary`     | Color     | primary color                 |
| `step-secondary`   | Color     | secondary color               |
| `step-accent`      | Color     | accent color                  |
| `step-neutral`     | Color     | neutral color                 |
| `step-info`        | Color     | info color                    |
| `step-success`     | Color     | success color                 |
| `step-warning`     | Color     | warning color                 |
| `step-error`       | Color     | error color                   |
| `steps-vertical`   | Direction | Pionowe (default)             |
| `steps-horizontal` | Direction | Poziome                       |

```html
<ul class="steps">
  <li class="step step-primary">Rejestracja</li>
  <li class="step step-primary">Wybór planu</li>
  <li class="step">Płatność</li>
  <li class="step">Gotowe</li>
</ul>
```

### Tabs (`tabs`)

| Klasa          | Typ       | Opis                                   |
|----------------|-----------|----------------------------------------|
| `tabs`         | Component | Kontener zakładek                      |
| `tab`          | Part      | Pojedyncza zakładka                    |
| `tab-content`  | Part      | Zawartość zakładki (po radio input)    |
| `tabs-box`     | Style     | Styl box                               |
| `tabs-border`  | Style     | Styl z dolnym borderem                 |
| `tabs-lift`    | Style     | Styl lift (podniesiony)                |
| `tab-active`   | Modifier  | Aktywna zakładka                       |
| `tab-disabled` | Modifier  | Wyłączona zakładka                     |
| `tabs-top`     | Placement | Zakładki na górze (default)            |
| `tabs-bottom`  | Placement | Zakładki na dole                       |
| `tabs-xs/sm/md/lg/xl` | Size | Rozmiary                          |

```html
<!-- Proste zakładki -->
<div role="tablist" class="tabs tabs-border">
  <a role="tab" class="tab">Tab 1</a>
  <a role="tab" class="tab tab-active">Tab 2</a>
  <a role="tab" class="tab">Tab 3</a>
</div>

<!-- Zakładki z treścią (radio) -->
<div role="tablist" class="tabs tabs-lift">
  <input type="radio" name="my_tabs" role="tab" class="tab" aria-label="Tab 1" />
  <div role="tabpanel" class="tab-content bg-base-100 border-base-300 p-6">
    Treść zakładki 1
  </div>
  <input type="radio" name="my_tabs" role="tab" class="tab" aria-label="Tab 2" checked="checked" />
  <div role="tabpanel" class="tab-content bg-base-100 border-base-300 p-6">
    Treść zakładki 2
  </div>
</div>
```

---

## 💬 FEEDBACK

### Alert (`alert`)

| Klasa              | Typ       | Opis                          |
|--------------------|-----------|-------------------------------|
| `alert`            | Component | Kontener alertu               |
| `alert-outline`    | Style     | outline style                 |
| `alert-dash`       | Style     | dash outline style            |
| `alert-soft`       | Style     | soft style                    |
| `alert-info`       | Color     | info color                    |
| `alert-success`    | Color     | success color                 |
| `alert-warning`    | Color     | warning color                 |
| `alert-error`      | Color     | error color                   |
| `alert-vertical`   | Direction | Układ pionowy (mobile)        |
| `alert-horizontal` | Direction | Układ poziomy (desktop)       |

```html
<div role="alert" class="alert alert-success">
  <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6 shrink-0 stroke-current" fill="none" viewBox="0 0 24 24">
    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
  </svg>
  <span>Operacja zakończona pomyślnie!</span>
</div>
```

### Loading (`loading`)

| Klasa              | Typ   | Opis              |
|--------------------|-------|--------------------|
| `loading`          | Component | Element ładowania |
| `loading-spinner`  | Style | Animacja spinnera  |
| `loading-dots`     | Style | Animacja kropek    |
| `loading-ring`     | Style | Animacja pierścienia|
| `loading-ball`     | Style | Animacja piłki     |
| `loading-bars`     | Style | Animacja pasków    |
| `loading-infinity` | Style | Animacja infinity  |
| `loading-xs/sm/md/lg/xl` | Size | Rozmiary    |

```html
<span class="loading loading-spinner loading-lg"></span>
<span class="loading loading-dots loading-md text-primary"></span>
```

### Progress (`progress`)

| Klasa               | Typ   | Opis               |
|---------------------|-------|---------------------|
| `progress`          | Component | Pasek postępu   |
| `progress-primary`  | Color | primary color       |
| `progress-secondary`| Color | secondary color     |
| `progress-accent`   | Color | accent color        |
| `progress-info`     | Color | info color          |
| `progress-success`  | Color | success color       |
| `progress-warning`  | Color | warning color       |
| `progress-error`    | Color | error color         |

```html
<progress class="progress progress-primary w-56" value="70" max="100"></progress>
```

### Radial Progress

```html
<div class="radial-progress text-primary" style="--value:70;" role="progressbar">70%</div>
```

### Skeleton (`skeleton`)

```html
<div class="skeleton h-32 w-full"></div>
<div class="skeleton h-4 w-28"></div>
<div class="skeleton h-4 w-full"></div>
```

### Toast (`toast`)

| Klasa          | Typ       | Opis                                  |
|----------------|-----------|---------------------------------------|
| `toast`        | Component | Kontener przyklejon do rogu strony    |
| `toast-start`  | Placement | Wyrównaj do lewej                     |
| `toast-center` | Placement | Wyrównaj do środka                    |
| `toast-end`    | Placement | Wyrównaj do prawej (default)          |
| `toast-top`    | Placement | Na górze                              |
| `toast-middle` | Placement | Na środku                             |
| `toast-bottom` | Placement | Na dole (default)                     |

```html
<div class="toast toast-end">
  <div class="alert alert-success">
    <span>Zapisano pomyślnie.</span>
  </div>
</div>
```

### Tooltip (`tooltip`)

| Klasa              | Typ       | Opis                   |
|--------------------|-----------|------------------------|
| `tooltip`          | Component | Kontener tooltipa      |
| `tooltip-content`  | Part      | Opcjonalny div z treścią|
| `tooltip-top`      | Placement | Na górze (default)     |
| `tooltip-bottom`   | Placement | Na dole                |
| `tooltip-left`     | Placement | Po lewej               |
| `tooltip-right`    | Placement | Po prawej              |
| `tooltip-open`     | Modifier  | Wymuś otwarcie         |
| `tooltip-primary/secondary/accent/neutral/info/success/warning/error` | Color | Kolory |

```html
<div class="tooltip tooltip-primary" data-tip="Informacja">
  <button class="btn">Najedź</button>
</div>
```

---

## 📝 DATA INPUT

### Checkbox (`checkbox`)

| Klasa             | Typ   | Opis              |
|-------------------|-------|--------------------|
| `checkbox`        | Component | Checkbox       |
| `checkbox-primary/secondary/accent/neutral` | Color | Kolory |
| `checkbox-success/warning/info/error` | Color | Kolory statusu |
| `checkbox-xs/sm/md/lg/xl` | Size | Rozmiary    |

```html
<input type="checkbox" class="checkbox checkbox-primary" />
```

### Fieldset (`fieldset`)

| Klasa             | Typ       | Opis                         |
|-------------------|-----------|-------------------------------|
| `fieldset`        | Component | Kontener formularza           |
| `label`           | Component | Etykieta inputa               |
| `fieldset-legend` | Part      | Tytuł fieldsetu               |

```html
<fieldset class="fieldset">
  <legend class="fieldset-legend">Szczegóły projektu</legend>
  <label class="label">Tytuł</label>
  <input type="text" class="input" placeholder="Nazwa projektu" />
  <label class="label">Opis</label>
  <textarea class="textarea" placeholder="Opis projektu"></textarea>
</fieldset>
```

### File Input (`file-input`)

| Klasa               | Typ   | Opis              |
|---------------------|-------|--------------------|
| `file-input`        | Component | Input plikowy  |
| `file-input-ghost`  | Style | ghost style        |
| `file-input-primary/secondary/accent/neutral` | Color | Kolory |
| `file-input-xs/sm/md/lg/xl` | Size | Rozmiary    |

### Radio (`radio`)

| Klasa            | Typ   | Opis            |
|------------------|-------|-----------------|
| `radio`          | Component | Radio button |
| `radio-primary/secondary/accent/neutral` | Color | Kolory |
| `radio-success/warning/info/error` | Color | Kolory statusu |
| `radio-xs/sm/md/lg/xl` | Size | Rozmiary    |

### Range Slider (`range`)

| Klasa            | Typ   | Opis            |
|------------------|-------|-----------------|
| `range`          | Component | Range slider |
| `range-primary/secondary/accent/neutral` | Color | Kolory |
| `range-xs/sm/md/lg/xl` | Size | Rozmiary    |

### Rating (`rating`)

| Klasa           | Typ       | Opis               |
|-----------------|-----------|---------------------|
| `rating`        | Component | Kontener gwiazdek   |
| `rating-half`   | Modifier  | Pozwól na pół gwiazdki|
| `rating-hidden` | Modifier  | Ukryty input (reset) |
| `rating-xs/sm/md/lg/xl` | Size | Rozmiary       |

### Select (`select`)

| Klasa               | Typ   | Opis              |
|---------------------|-------|--------------------|
| `select`            | Component | Select element |
| `select-ghost`      | Style | ghost style        |
| `select-primary/secondary/accent/neutral` | Color | Kolory |
| `select-info/success/warning/error` | Color | Kolory statusu |
| `select-xs/sm/md/lg/xl` | Size | Rozmiary       |

```html
<select class="select select-primary w-full max-w-xs">
  <option disabled selected>Wybierz opcję</option>
  <option>Opcja 1</option>
  <option>Opcja 2</option>
</select>
```

### Text Input (`input`)

| Klasa               | Typ   | Opis              |
|---------------------|-------|--------------------|
| `input`             | Component | Pole tekstowe  |
| `input-ghost`       | Style | ghost style        |
| `input-primary/secondary/accent/neutral` | Color | Kolory |
| `input-info/success/warning/error` | Color | Kolory statusu |
| `input-xs/sm/md/lg/xl` | Size | Rozmiary       |

```html
<input type="text" class="input input-primary w-full max-w-xs" placeholder="Wpisz..." />

<!-- Input z label-em wewnątrz -->
<label class="input">
  <svg>...</svg>
  <input type="text" placeholder="Szukaj..." />
</label>
```

### Textarea (`textarea`)

| Klasa                | Typ   | Opis              |
|----------------------|-------|--------------------|
| `textarea`           | Component | Textarea       |
| `textarea-ghost`     | Style | ghost style        |
| `textarea-primary/secondary/accent/neutral` | Color | Kolory |
| `textarea-info/success/warning/error` | Color | Kolory statusu |
| `textarea-xs/sm/md/lg/xl` | Size | Rozmiary       |

```html
<textarea class="textarea textarea-primary" placeholder="Opis..."></textarea>
```

### Toggle (`toggle`)

| Klasa              | Typ   | Opis                   |
|--------------------|-------|------------------------|
| `toggle`           | Component | Przełącznik (switch)|
| `toggle-primary/secondary/accent/neutral` | Color | Kolory |
| `toggle-success/warning/info/error` | Color | Kolory statusu |
| `toggle-xs/sm/md/lg/xl` | Size | Rozmiary           |

```html
<input type="checkbox" class="toggle toggle-primary" />
```

### Validator (`validator`)

```html
<!-- Automatyczna walidacja kolorami -->
<input type="email" class="input validator" required placeholder="Email" />
```

### Filter (`filter`)

```html
<div class="filter">
  <input class="filter-reset" type="radio" name="my-filter" />
  <input class="btn filter-btn" type="radio" name="my-filter" aria-label="Wszystkie" />
  <input class="btn filter-btn" type="radio" name="my-filter" aria-label="Aktywne" checked />
  <input class="btn filter-btn" type="radio" name="my-filter" aria-label="Zamknięte" />
</div>
```

---

## 🧱 LAYOUT

### Divider (`divider`)

| Klasa                | Typ       | Opis              |
|----------------------|-----------|-------------------|
| `divider`            | Component | Separator         |
| `divider-vertical`   | Direction | Pionowy           |
| `divider-horizontal` | Direction | Poziomy (default) |
| `divider-neutral`    | Color     | neutral           |
| `divider-primary`    | Color     | primary           |
| `divider-secondary`  | Color     | secondary         |
| `divider-accent`     | Color     | accent            |
| `divider-success`    | Color     | success           |
| `divider-warning`    | Color     | warning           |
| `divider-info`       | Color     | info              |
| `divider-error`      | Color     | error             |
| `divider-start`      | Placement | Tekst na początku |
| `divider-end`        | Placement | Tekst na końcu    |

```html
<div class="divider">LUB</div>
<div class="divider divider-primary">Sekcja</div>
```

### Drawer sidebar (`drawer`)

| Klasa            | Typ       | Opis                                     |
|------------------|-----------|-------------------------------------------|
| `drawer`         | Component | Główny kontener                           |
| `drawer-toggle`  | Part      | Ukryty checkbox kontrolujący stan         |
| `drawer-content` | Part      | Zawartość strony                          |
| `drawer-side`    | Part      | Sidebar                                   |
| `drawer-overlay` | Part      | Nakładka zaciemniająca                    |
| `drawer-end`     | Placement | Sidebar po prawej stronie                 |
| `drawer-open`    | Modifier  | Wymuś otwarcie                            |
| `is-drawer-open:`| Variant   | Style gdy drawer otwarty                  |
| `is-drawer-close:` | Variant | Style gdy drawer zamknięty                |

```html
<div class="drawer lg:drawer-open">
  <input id="my-drawer" type="checkbox" class="drawer-toggle" />
  <div class="drawer-content">
    <!-- Treść strony -->
    <label for="my-drawer" class="btn btn-primary drawer-button lg:hidden">
      ☰ Menu
    </label>
  </div>
  <div class="drawer-side">
    <label for="my-drawer" aria-label="close sidebar" class="drawer-overlay"></label>
    <ul class="menu bg-base-200 min-h-full w-80 p-4">
      <li><a>Dashboard</a></li>
      <li><a>Projekty</a></li>
    </ul>
  </div>
</div>
```

### Footer (`footer`)

| Klasa          | Typ       | Opis              |
|----------------|-----------|-------------------|
| `footer`       | Component | Stopka            |
| `footer-title` | Part      | Tytuł sekcji      |
| `footer-center`| Modifier  | Wyśrodkuj treść   |

### Hero (`hero`)

| Klasa          | Typ       | Opis                         |
|----------------|-----------|-------------------------------|
| `hero`         | Component | Kontener hero                 |
| `hero-content` | Part      | Zawartość hero                |
| `hero-overlay` | Part      | Nakładka na obraz tła         |

```html
<div class="hero min-h-screen bg-base-200">
  <div class="hero-content text-center">
    <div class="max-w-md">
      <h1 class="text-5xl font-bold">IT Project OS</h1>
      <p class="py-6">System zarządzania projektami</p>
      <button class="btn btn-primary">Rozpocznij</button>
    </div>
  </div>
</div>
```

### Indicator (`indicator`)

| Klasa            | Typ       | Opis                              |
|------------------|-----------|-----------------------------------|
| `indicator`      | Component | Kontener z elementem w rogu       |
| `indicator-item` | Part      | Element wskaźnika                 |
| `indicator-top/bottom` | Placement | Góra/dół                    |
| `indicator-start/center/end` | Placement | Pozycja horyzontalna  |
| `indicator-middle` | Placement | Środek pionowy                  |

```html
<div class="indicator">
  <span class="indicator-item badge badge-primary">99+</span>
  <button class="btn">Inbox</button>
</div>
```

### Join (Group Items) (`join`)

| Klasa      | Typ       | Opis                              |
|------------|-----------|-----------------------------------|
| `join`     | Component | Grupuje elementy razem            |
| `join-item`| Part      | Pojedynczy element w grupie       |
| `join-vertical`   | Direction | Grupowanie pionowe          |
| `join-horizontal` | Direction | Grupowanie poziome (default)|

```html
<div class="join">
  <input class="input join-item" placeholder="Email" />
  <button class="btn join-item btn-primary">Subskrybuj</button>
</div>

<div class="join">
  <button class="btn join-item">1</button>
  <button class="btn join-item btn-active">2</button>
  <button class="btn join-item">3</button>
</div>
```

### Mask (`mask`)

| Klasa             | Typ   | Opis                    |
|-------------------|-------|-------------------------|
| `mask`            | Component | Maska na element     |
| `mask-squircle`   | Style | Zaokrąglony kwadrat     |
| `mask-heart`      | Style | Serce                   |
| `mask-hexagon`    | Style | Heksagon                |
| `mask-hexagon-2`  | Style | Heksagon obrócony       |
| `mask-decagon`    | Style | Dekagon                 |
| `mask-pentagon`   | Style | Pentagon                |
| `mask-diamond`    | Style | Diament                 |
| `mask-square`     | Style | Kwadrat                 |
| `mask-circle`     | Style | Koło                    |
| `mask-star`       | Style | Gwiazda 5-ramienna      |
| `mask-star-2`     | Style | Gwiazda 4-ramienna      |
| `mask-triangle`   | Style | Trójkąt                 |
| `mask-half-1`     | Modifier | Lewa połowa           |
| `mask-half-2`     | Modifier | Prawa połowa          |

### Stack (`stack`)

```html
<div class="stack">
  <div class="card bg-primary text-primary-content">...</div>
  <div class="card bg-secondary text-secondary-content">...</div>
  <div class="card bg-accent text-accent-content">...</div>
</div>
```

---

## 🖥️ MOCKUP

### Browser Mockup (`mockup-browser`)

```html
<div class="mockup-browser bg-base-300 border border-base-300">
  <div class="mockup-browser-toolbar">
    <div class="input">https://daisyui.com</div>
  </div>
  <div class="bg-base-200 px-4 py-16">Hello!</div>
</div>
```

### Code Mockup (`mockup-code`)

```html
<div class="mockup-code">
  <pre data-prefix="$"><code>npm i daisyui</code></pre>
  <pre data-prefix=">" class="text-warning"><code>installing...</code></pre>
  <pre data-prefix=">" class="text-success"><code>Done!</code></pre>
</div>
```

### Phone Mockup (`mockup-phone`)

```html
<div class="mockup-phone">
  <div class="camera"></div>
  <div class="display">
    <div class="artboard artboard-demo phone-1">Hi.</div>
  </div>
</div>
```

### Window Mockup (`mockup-window`)

```html
<div class="mockup-window bg-base-300 border border-base-300">
  <div class="bg-base-200 px-4 py-16">Hello!</div>
</div>
```

---

## 🔧 SPECIAL

### FAB / Speed Dial (`fab`)

```html
<div class="fab">
  <button class="btn btn-circle btn-primary" popovertarget="fab-menu">
    <svg>+</svg>
  </button>
  <ul popover id="fab-menu" class="fab-content menu">
    <li><button class="btn btn-circle">A</button></li>
    <li><button class="btn btn-circle">B</button></li>
  </ul>
</div>
```

### Status (`status`)

| Klasa            | Typ   | Opis                |
|------------------|-------|---------------------|
| `status`         | Component | Mały wskaźnik statusu |
| `status-primary/secondary/accent/neutral` | Color | Kolory |
| `status-info/success/warning/error` | Color | Kolory statusu |
| `status-xs/sm/md/lg/xl` | Size | Rozmiary       |

### Theme Controller (`theme-controller`)

```html
<!-- Przełącznik motywu -->
<input type="checkbox" value="dark" class="toggle theme-controller" />
```

---

## 🎨 Najczęstsze Wzorce w IT Project OS

### Formularz CRUD (moduł)

```html
<!-- partial: form.html -->
<form hx-post="/modules/issues/" hx-target="#main-content" hx-swap="innerHTML">
  <fieldset class="fieldset">
    <legend class="fieldset-legend">Nowe zgłoszenie</legend>

    <label class="label">Tytuł</label>
    <input type="text" name="title" class="input input-primary w-full" required placeholder="Tytuł zgłoszenia" />

    <label class="label">Priorytet</label>
    <select name="priority" class="select select-primary w-full">
      <option disabled selected>Wybierz priorytet</option>
      <option value="low">Niski</option>
      <option value="medium">Średni</option>
      <option value="high">Wysoki</option>
    </select>

    <label class="label">Opis</label>
    <textarea name="description" class="textarea textarea-primary w-full" placeholder="Opisz zgłoszenie..."></textarea>

    <div class="flex justify-end gap-2 mt-4">
      <button type="button" class="btn btn-ghost" hx-get="/modules/issues/" hx-target="#main-content">Anuluj</button>
      <button type="submit" class="btn btn-primary">Zapisz</button>
    </div>
  </fieldset>
</form>
```

### Lista z tabelą (moduł)

```html
<!-- partial: list.html -->
<div class="flex items-center justify-between mb-4">
  <h2 class="text-2xl font-bold">Zgłoszenia</h2>
  <button class="btn btn-primary" hx-get="/modules/issues/new" hx-target="#main-content" hx-push-url="true">
    + Nowe
  </button>
</div>

<div class="overflow-x-auto">
  <table class="table table-zebra">
    <thead>
      <tr>
        <th>#</th>
        <th>Tytuł</th>
        <th>Status</th>
        <th>Priorytet</th>
        <th>Akcje</th>
      </tr>
    </thead>
    <tbody>
      {% for issue in issues %}
      <tr class="hover">
        <th>{{ issue.id }}</th>
        <td>{{ issue.title }}</td>
        <td><span class="badge badge-info">{{ issue.status }}</span></td>
        <td><span class="badge badge-warning badge-outline">{{ issue.priority }}</span></td>
        <td>
          <button class="btn btn-sm btn-ghost" hx-get="/modules/issues/{{ issue.id }}" hx-target="#main-content" hx-push-url="true">
            Szczegóły
          </button>
        </td>
      </tr>
      {% endfor %}
    </tbody>
  </table>
</div>
```

### Karta szczegółów (moduł)

```html
<!-- partial: detail.html -->
<div class="card bg-base-100 shadow-xl">
  <div class="card-body">
    <div class="flex items-center justify-between">
      <h2 class="card-title">{{ item.title }}</h2>
      <span class="badge badge-primary">{{ item.status }}</span>
    </div>
    <p>{{ item.description }}</p>
    <div class="divider"></div>
    <div class="stats stats-vertical lg:stats-horizontal shadow">
      <div class="stat">
        <div class="stat-title">Utworzono</div>
        <div class="stat-value text-sm">{{ item.created_at }}</div>
      </div>
      <div class="stat">
        <div class="stat-title">Priorytet</div>
        <div class="stat-value text-sm">{{ item.priority }}</div>
      </div>
    </div>
    <div class="card-actions justify-end mt-4">
      <button class="btn btn-ghost" hx-get="/modules/issues/" hx-target="#main-content" hx-push-url="true">
        Powrót
      </button>
      <button class="btn btn-primary" hx-get="/modules/issues/{{ item.id }}/edit" hx-target="#main-content">
        Edytuj
      </button>
      <button class="btn btn-error btn-outline" hx-delete="/modules/issues/{{ item.id }}" hx-target="#main-content" hx-confirm="Czy na pewno chcesz usunąć?">
        Usuń
      </button>
    </div>
  </div>
</div>
```

### Modal potwierdzenia (HTMX)

```html
<button class="btn btn-error btn-outline" onclick="delete_modal.showModal()">Usuń</button>
<dialog id="delete_modal" class="modal">
  <div class="modal-box">
    <h3 class="text-lg font-bold">Potwierdź usunięcie</h3>
    <p class="py-4">Czy na pewno chcesz usunąć ten element? Tej operacji nie można cofnąć.</p>
    <div class="modal-action">
      <form method="dialog">
        <button class="btn btn-ghost">Anuluj</button>
      </form>
      <button class="btn btn-error" hx-delete="/modules/issues/{{ item.id }}" hx-target="#main-content">
        Tak, usuń
      </button>
    </div>
  </div>
  <form method="dialog" class="modal-backdrop">
    <button>close</button>
  </form>
</dialog>
```

### Empty state

```html
<div class="hero min-h-64">
  <div class="hero-content text-center">
    <div class="max-w-md">
      <h2 class="text-2xl font-bold">Brak wyników</h2>
      <p class="py-4 text-base-content/60">Nie znaleziono żadnych elementów spełniających kryteria.</p>
      <button class="btn btn-primary" hx-get="/modules/issues/new" hx-target="#main-content">
        Dodaj pierwszy element
      </button>
    </div>
  </div>
</div>
```

### Loading state (HTMX indicator)

```html
<div id="main-content">
  <span class="loading loading-spinner loading-lg htmx-indicator"></span>
</div>

<!-- Przycisk z loading -->
<button class="btn btn-primary" hx-get="/modules/issues/" hx-target="#main-content" hx-indicator=".htmx-indicator">
  Załaduj
</button>
```

---

## 🔷 System Ikon — Heroicons Outline (Inline SVG)

> Jedyna dozwolona biblioteka ikon: **Heroicons Outline**. Zawsze inline SVG — bez zewnętrznych arkuszy.
> Źródło ścieżek SVG: https://heroicons.com (wybieraj wariant **Outline**)

### Obowiązkowy szablon

```html
<!-- Ikona: [opis po polsku] -->
<svg xmlns="http://www.w3.org/2000/svg" class="w-4 h-4 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
  <path stroke-linecap="round" stroke-linejoin="round" d="..." />
</svg>
```

### Skala rozmiarów

| Klasa         | Kontekst                                          |
|---------------|---------------------------------------------------|
| `w-3 h-3`     | Mikro — wewnątrz `badge`, `tag`                  |
| `w-4 h-4`     | **Domyślny** — btn, nav, inline                  |
| `w-5 h-5`     | Alerty, nagłówki sekcji                          |
| `w-6 h-6`     | Navbar, duże CTA                                 |
| `w-8 h-8`     | `stat-figure`                                    |
| `w-10 h-10`   | Empty-state (z `opacity-30`)                     |

### Gotowe ikony projektu

```html
<!-- Ikona: użytkownik -->
<svg xmlns="http://www.w3.org/2000/svg" class="w-4 h-4 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
  <path stroke-linecap="round" stroke-linejoin="round" d="M15.75 6a3.75 3.75 0 1 1-7.5 0 3.75 3.75 0 0 1 7.5 0ZM4.501 20.118a7.5 7.5 0 0 1 14.998 0A17.933 17.933 0 0 1 12 21.75c-2.676 0-5.216-.584-7.499-1.632Z" />
</svg>

<!-- Ikona: kalendarz -->
<svg xmlns="http://www.w3.org/2000/svg" class="w-4 h-4 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
  <path stroke-linecap="round" stroke-linejoin="round" d="M6.75 3v2.25M17.25 3v2.25M3 18.75V7.5a2.25 2.25 0 0 1 2.25-2.25h13.5A2.25 2.25 0 0 1 21 7.5v11.25m-18 0A2.25 2.25 0 0 0 5.25 21h13.5A2.25 2.25 0 0 0 21 18.75m-18 0v-7.5A2.25 2.25 0 0 1 5.25 9h13.5A2.25 2.25 0 0 1 21 11.25v7.5" />
</svg>

<!-- Ikona: ołówek (edytuj) -->
<svg xmlns="http://www.w3.org/2000/svg" class="w-4 h-4 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
  <path stroke-linecap="round" stroke-linejoin="round" d="m16.862 4.487 1.687-1.688a1.875 1.875 0 1 1 2.652 2.652L10.582 16.07a4.5 4.5 0 0 1-1.897 1.13L6 18l.8-2.685a4.5 4.5 0 0 1 1.13-1.897l8.932-8.931Zm0 0L19.5 7.125" />
</svg>

<!-- Ikona: kosz (usuń) -->
<svg xmlns="http://www.w3.org/2000/svg" class="w-4 h-4 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
  <path stroke-linecap="round" stroke-linejoin="round" d="m14.74 9-.346 9m-4.788 0L9.26 9m9.968-3.21c.342.052.682.107 1.022.166m-1.022-.165L18.16 19.673a2.25 2.25 0 0 1-2.244 2.077H8.084a2.25 2.25 0 0 1-2.244-2.077L4.772 5.79m14.456 0a48.108 48.108 0 0 0-3.478-.397m-12 .562c.34-.059.68-.114 1.022-.165m0 0a48.11 48.11 0 0 1 3.478-.397m7.5 0v-.916c0-1.18-.91-2.164-2.09-2.201a51.964 51.964 0 0 0-3.32 0c-1.18.037-2.09 1.022-2.09 2.201v.916m7.5 0a48.667 48.667 0 0 0-7.5 0" />
</svg>

<!-- Ikona: plus (dodaj) -->
<svg xmlns="http://www.w3.org/2000/svg" class="w-4 h-4 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
  <path stroke-linecap="round" stroke-linejoin="round" d="M12 4.5v15m7.5-7.5h-15" />
</svg>

<!-- Ikona: strzałka wstecz -->
<svg xmlns="http://www.w3.org/2000/svg" class="w-4 h-4 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
  <path stroke-linecap="round" stroke-linejoin="round" d="M10.5 19.5 3 12m0 0 7.5-7.5M3 12h18" />
</svg>

<!-- Ikona: serwer -->
<svg xmlns="http://www.w3.org/2000/svg" class="w-4 h-4 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
  <path stroke-linecap="round" stroke-linejoin="round" d="M5.25 14.25h13.5m-13.5 0a3 3 0 0 1-3-3m3 3a3 3 0 1 0 0 6h13.5a3 3 0 1 0 0-6m-16.5-3a3 3 0 0 1 3-3h13.5a3 3 0 0 1 3 3M12 6.75a.75.75 0 1 1 0-1.5.75.75 0 0 1 0 1.5Zm0 9a.75.75 0 1 1 0-1.5.75.75 0 0 1 0 1.5Z" />
</svg>

<!-- Ikona: folder (projekty) -->
<svg xmlns="http://www.w3.org/2000/svg" class="w-4 h-4 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
  <path stroke-linecap="round" stroke-linejoin="round" d="M2.25 12.75V12A2.25 2.25 0 0 1 4.5 9.75h15A2.25 2.25 0 0 1 21.75 12v.75m-8.69-6.44-2.12-2.12a1.5 1.5 0 0 0-1.061-.44H4.5A2.25 2.25 0 0 0 2.25 6v8.25m19.5 0v.75A2.25 2.25 0 0 1 19.5 17.25h-15A2.25 2.25 0 0 1 2.25 15v-.75m19.5 0h-19.5" />
</svg>

<!-- Ikona: kod (technologie) -->
<svg xmlns="http://www.w3.org/2000/svg" class="w-4 h-4 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
  <path stroke-linecap="round" stroke-linejoin="round" d="M17.25 6.75 22.5 12l-5.25 5.25m-10.5 0L1.5 12l5.25-5.25m7.5-3-4.5 16.5" />
</svg>

<!-- Ikona: wykres (KPI) -->
<svg xmlns="http://www.w3.org/2000/svg" class="w-4 h-4 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
  <path stroke-linecap="round" stroke-linejoin="round" d="M7.5 14.25v2.25m3-4.5v4.5m3-6.75v6.75m3-9v9M6 20.25h12A2.25 2.25 0 0 0 20.25 18V6A2.25 2.25 0 0 0 18 3.75H6A2.25 2.25 0 0 0 3.75 6v12A2.25 2.25 0 0 0 6 20.25Z" />
</svg>

<!-- Ikona: ostrzeżenie (alert warning) -->
<svg xmlns="http://www.w3.org/2000/svg" class="w-5 h-5 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
  <path stroke-linecap="round" stroke-linejoin="round" d="M12 9v3.75m-9.303 3.376c-.866 1.5.217 3.374 1.948 3.374h14.71c1.73 0 2.813-1.874 1.948-3.374L13.949 3.378c-.866-1.5-3.032-1.5-3.898 0L2.697 16.126ZM12 15.75h.007v.008H12v-.008Z" />
</svg>

<!-- Ikona: info (alert info) -->
<svg xmlns="http://www.w3.org/2000/svg" class="w-5 h-5 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
  <path stroke-linecap="round" stroke-linejoin="round" d="m11.25 11.25.041-.02a.75.75 0 0 1 1.063.852l-.708 2.836a.75.75 0 0 0 1.063.853l.041-.021M21 12a9 9 0 1 1-18 0 9 9 0 0 1 18 0Zm-9-3.75h.008v.008H12V8.25Z" />
</svg>
```

### Zakazane praktyki ikon

| ❌ Zakaz | ✅ Poprawnie |
|---|---|
| `<i class="fa-trash">` | Inline SVG Heroicons |
| `fill="currentColor"` (solid) | `fill="none"` + `stroke="currentColor"` |
| `stroke-width="2"` | `stroke-width="1.5"` |
| `style="color: red"` na SVG | klasa `text-error` na rodzicu |
| brak komentarza `<!-- Ikona: ... -->` | komentarz po polsku obowiązkowy |
| brak `shrink-0` w flex | zawsze `shrink-0` w kontenerach flex |

---

## ⚡ Szybki Cheatsheet — Mapowanie Potrzeb na Komponenty

| Potrzebujesz...                    | Użyj daisyUI             |
|------------------------------------|---------------------------|
| Przycisk                           | `btn`                     |
| Formularz                          | `fieldset` + `input`/`select`/`textarea` |
| Tabela danych                      | `table`                   |
| Karta z treścią                    | `card`                    |
| Menu nawigacyjne                   | `menu` lub `navbar`       |
| Zakładki                           | `tabs`                    |
| Dialog/popup                       | `modal` (dialog HTML)     |
| Rozwijana lista                    | `dropdown`/`collapse`     |
| Status element                     | `badge` lub `status`      |
| Powiadomienie                      | `alert` lub `toast`       |
| Wskaźnik postępu                   | `progress` lub `loading`  |
| Podpowiedź                         | `tooltip`                 |
| Sidebar                            | `drawer`                  |
| Paginacja                          | `join` + `btn`            |
| Grupowanie elementów               | `join`                    |
| Separator                          | `divider`                 |
| Dane liczbowe                      | `stat`                    |
| Kroki procesu                      | `steps`                   |
| Przełącznik on/off                 | `toggle`                  |
| Gwiazdki/ocena                     | `rating`                  |
| Placeholder ładowania              | `skeleton`                |
| Ścieżka nawigacji                  | `breadcrumbs`             |
| Belka dolna (mobile)               | `dock`                    |
