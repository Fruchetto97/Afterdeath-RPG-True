# Afterdeath RPG

RPG a turni in pixel art, scritto in Python con [pygame-ce](https://pyga.me/).
Si sceglie una specie di non-morti (Maedo, Minnago, Sapifer, Selkio), si esplora
l'overworld (mappe [Tiled](https://www.mapeditor.org/)) e si combatte con un sistema
a turni basato su parti del corpo, effetti di stato e abilità.

## Giocare

1. Apri la pagina **Releases** del repository e scarica `Afterdeath-<versione>-windows.zip`
   (le build intermedie sono negli *artifact* dei workflow **Build game**, tab **Actions**).
2. Estrai lo zip e avvia `Afterdeath/Afterdeath.exe`.

Salvataggi, impostazioni e log (`afterdeath.log`) vengono scritti in `Afterdeath/userdata/`.

## Avviare dai sorgenti

Serve Python 3.11 o superiore.

```bash
python -m venv .venv
.venv\Scripts\activate          # Windows  (Linux/macOS: source .venv/bin/activate)
pip install -r requirements-dev.txt
python -m afterdeath           # dalla cartella del repository
```

Comandi utili:

| Comando                      | A cosa serve                                 |
| ---------------------------- | -------------------------------------------- |
| `python -m afterdeath`       | avvia il gioco                               |
| `pytest`                     | esegue i test (moduli, asset, equipaggiamento) |
| `ruff check .`               | lint                                         |
| `ruff format .`              | formatta il codice                           |
| `pyinstaller afterdeath.spec`| crea l'eseguibile in `dist/Afterdeath/`      |

## Struttura del progetto

```
afterdeath/                 codice del gioco (package Python)
├── __main__.py             entry point (python -m afterdeath / exe)
├── main_menu.py            menu principale, creazione personaggio, caricamento
├── paths.py                tutti i percorsi di asset e dati utente
├── sfx.py                  volume globale ed effetti sonori
├── save_system.py          salvataggi JSON
├── data/                   dati statici: species, skills, status_effects
├── combat/                 battle.py (sistema di combattimento), enemy_ai.py
├── player/                 equipment, items, moves del giocatore
└── overworld/
    ├── game.py             loop principale dell'overworld (run())
    ├── enemies.py          NPC nemici e loro definizioni
    ├── maps/               configurazione di ogni mappa + transizioni
    └── menus/              menu di pausa e sottomenu
assets/
├── audio/                  music/, sfx/
├── fonts/
├── images/                 portraits, ui, items, status_effects, battle_backgrounds
├── sprites/                players, enemies, overworld
└── maps/                   mappe .tmx e tilesets/ (.tsx + immagini)
tests/                      test pytest
afterdeath.spec             ricetta PyInstaller
```

### Convenzioni

- **Mai percorsi assoluti o relativi alla cartella corrente.** Ogni asset si raggiunge
  con le funzioni di `afterdeath/paths.py` (`paths.sfx("...")`, `paths.ui_image("...")`,
  `paths.FONT_PATH`, ...). Funziona sia dai sorgenti sia dall'exe.
- **Import statici del package** (`from afterdeath.player.equipment import ...`).
  Niente `sys.path`, `importlib` o `subprocess` per collegare i moduli. Gli import
  dentro le funzioni restano solo dove evitano un import circolare (per esempio
  `battle` ↔ `equipment`) o dove leggono uno stato che cambia durante la partita.
- Nuova mappa: crea `afterdeath/overworld/maps/<nome>.py` sul modello delle altre e
  aggiungi le transizioni in `afterdeath/overworld/maps/__init__.py`.
- Formattazione e lint con Ruff (configurazione in `pyproject.toml`): la CI li controlla.

## Asset mancanti

Le mappe Tiled usano tileset le cui immagini non sono mai state caricate nel repository
(stavano nella cartella *Download* di chi le ha create). Finché non vengono aggiunte,
**l'overworld non si avvia** (menu principale e "Battle Test" funzionano). Vanno messe con
questi nomi:

```
assets/maps/tilesets/Tileset_Foresta_Dorsale.png
assets/maps/tilesets/Tileset_Foresta_Dorsale_NoObj.png
assets/maps/tilesets/Tileset_Citta_01.png
assets/maps/tilesets/Tileset_Citta_Dorsale.png
assets/maps/tilesets/Tileset_Citta_Dorsale_V3.png
assets/maps/tilesets/Ponte_Base_Dorsale.png
assets/maps/tilesets/Oggetti_Citta_01/Objects.png
assets/maps/tilesets/Oggetti_Citta_01/Casa_11.png
assets/maps/tilesets/Oggetti_Citta_01/Casa_12.png
assets/maps/tilesets/Oggetti_Citta_01/Casa_13.png
assets/maps/tilesets/Oggetti_Citta_01/Staccionata_Ossea.png
assets/maps/tilesets/Oggetti_Citta_01/Torri_connesse_1.png
```

## Build e release automatiche (GitHub Actions)

- **CI** (`.github/workflows/ci.yml`): a ogni push e pull request esegue lint, controllo
  formattazione e test.
- **Build game** (`.github/workflows/build.yml`): a ogni push su `main` crea l'exe Windows
  e lo carica come artifact. Si può anche avviare a mano dal tab Actions (*Run workflow*).
- **Release**: per pubblicare una versione giocabile basta creare e pushare un tag:

  ```bash
  git tag v0.1.0
  git push origin v0.1.0
  ```

  Il workflow crea la GitHub Release con lo zip allegato e le note generate in automatico.
