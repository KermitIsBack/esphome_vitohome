# Entwicklung für XIAO ESP32S3 und Vitodens 20C2

Dieser Fork ergänzt eine lokale Entwicklungsumgebung für einen Seeed XIAO
ESP32S3 mit einem USB-Optolinkkopf (CH340, VID 1A86 / PID 7523).
Upstream-Komponenten bleiben unverändert. Die Konfiguration ist für P300,
4800 Baud, 8 Datenbits, gerade Parität und 2 Stoppbits ausgelegt.

## Arbeitsstand

- Original: https://github.com/SoulSolistice/esphome_vitohome
- Fork: https://github.com/KermitIsBack/esphome_vitohome
- Entwicklungsbranch: `develop/xiao-esp32s3-20c2`
- Ausgangscommit: `5c0e5216d957343de84bd43c79ad6d47576a8c84`
- Python 3.12, ESPHome 2026.9.1 gemäß Upstream-Pin in requirements.txt.
- Keine Firmware wurde auf Hardware übertragen; USB-Stromversorgung,
  Enumeration und Messwerte müssen am tatsächlichen Aufbau geprüft werden.

## Einstieg

`vitodens-xiao.code-workspace` in VS Code öffnen. Die enthaltenen Aufgaben
richten die Umgebung ein, prüfen YAML, führen Tests aus und bauen die Firmware.
Eine bereits angelegte `.venv` wird automatisch als Python-Interpreter genutzt.

Alternativ im Repository-Ordner:

```sh
bash scripts/setup_xiao.sh
bash scripts/check_xiao.sh
.venv/bin/python -m pytest tests/unit -q
bash scripts/build_xiao.sh
```

Für die erstmalige Einrichtung wird Python 3.12 benötigt. Falls es nicht unter
`python3.12` erreichbar ist, den Pfad ausdrücklich angeben:

```sh
VITODENS_PYTHON=/pfad/zu/python3.12 bash scripts/setup_xiao.sh
```

## Die zwei Firmware-Profile

`devices/xiao-esp32s3/read-only.yaml` ist das Standardprofil. Es liest Außen-,
Kessel-, Speicher- und Abgastemperatur, die Betriebsart und das interne Ventil.
Die MQTT-Anbindung der vorhandenen Installation wird nicht benutzt. Das Gerät
meldet sich über die ESPHome-API als eigener Entwicklungsknoten. Damit bleiben
Produktivbetrieb und Historie während der Entwicklung getrennt.

`devices/xiao-esp32s3/with-controls.yaml` ist ein ausdrückliches Zusatzprofil.
Es bietet nur drei Betriebsarten am Register 0x2323 an:

| Byte | Betriebsart |
| --- | --- |
| 0 | Aus / Abschaltbetrieb |
| 1 | Nur Warmwasser |
| 2 | Heizung + Warmwasser |

Die Auswahl wird nach einem Schreibvorgang vom selben Bedienregister
zurückgelesen (`read_back: true`). Die separate Statusanzeige liest 0x2301;
dessen Werte sind anders codiert und dürfen nicht als Schreibwerte benutzt
werden. Die Register wurden zuvor an einer 20C2 unter vcontrold geprüft.
Ihre Umsetzung mit dieser ESP-Firmware ist noch kein Hardwaretest.

Keine Rohschreib-Konsole, automatischen Moduswechsel oder Uhrzeitsynchronisierung
sind in diesen Profilen aktiviert. Erst das Leseprofil auf echter Hardware
prüfen, danach das Steuerprofil gezielt testen.

## Zugangsdaten und Build-Dateien

Vor einem späteren Hardwaretest `secrets.example.yaml` im Geräteordner nach
`secrets.yaml` kopieren und alle Beispielwerte durch eigene ersetzen. Einen
neuen API-Schlüssel etwa mit `openssl rand -base64 32` erzeugen. Die echten
Secrets werden von Git ignoriert. Zugangsdaten der produktiven Anlage werden
nicht in diesen Fork übernommen.

Die Prüf- und Build-Skripte arbeiten ausschließlich mit öffentlichen
Beispielwerten in `.validation/xiao/`. Sie ändern keine echten Secrets und
führen **keinen Upload** aus. Eine damit erzeugte Firmware enthält ungültige
WLAN-Zugangsdaten und ist nur ein Buildnachweis, keine Installationsdatei.
Nach Eintragen echter Werte später neu aus dem Geräteprofil kompilieren;
niemals die Test-Binärdatei aufspielen.

Logs und temporäre Firmware liegen unter `.validation/`; die lokale
PlatformIO-Toolchain liegt in `.platformio/`. Beides ist ignoriert.

## Hardware und Migration

Der USB-C-Port wird im Betrieb vom CH340-Lesekopf belegt. Logs und spätere
Updates erfolgen über WLAN; für die erste Installation wird der Kopf getrennt.
Eine geeignete 5-V-VBUS-Versorgung des Kopfes ist zusätzlich zur Software nötig.
Die konkrete Versorgung nach Seeed-Schaltplan prüfen, nicht aus der
USB-C-Steckerform ableiten.

Ein Umstieg auf die produktive Installation erfolgt separat: bewährte MQTT-
Topics und Discovery-IDs übernehmen oder die vorhandenen Dashboard-Entitäten
gezielt zuordnen. Pi- und ESP-Anbindung dürfen nicht gleichzeitig dieselben
MQTT-Geräteidentitäten veröffentlichen. Dieser Fork verändert aktuell weder
Home Assistant noch die laufende Heizung.

## Aktualisieren

```sh
git fetch upstream
git switch develop/xiao-esp32s3-20c2
git merge upstream/main
bash scripts/check_xiao.sh
.venv/bin/python -m pytest tests/unit -q
bash scripts/build_xiao.sh
```

Den funktionierenden ESPHome-/Upstream-Stand erst nach diesen Prüfungen und
einem erneuten Hardwaretest wechseln. Die lokale Paketauflösung des Macs ist
in `.validation/python-packages.txt` dokumentiert; die portablen direkten
Abhängigkeiten stehen in requirements-dev.txt.

## Geprüft am 24.10.2026

- Beide Profile: ESPHome-Schemavalidierung erfolgreich.
- Python-Tests: 533 bestanden, 1 übersprungen.
- Ruff: keine Befunde.
- Firmware-Leseprofil: vollständig kompiliert, RAM 48.140 Bytes,
  Flash 796.475 Bytes.
- Firmware-Steuerprofil: vollständig kompiliert, RAM 48.276 Bytes,
  Flash 800.123 Bytes.
- Kein USB-/Optolink-Hardwaretest und kein Upload durchgeführt.
- GitHub-Forks deaktivieren Actions anfangs häufig. Die lokalen Prüfbefehle
  funktionieren unabhängig davon; der ergänzte Workflow liegt für spätere
  Pushes und manuelle Läufe bereit.
