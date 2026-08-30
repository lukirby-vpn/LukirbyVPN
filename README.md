VPN Key Scanner & Generator

Автоматизированная система поиска, тестирования и конвертации публичных VPN-конфигураций в Xray-core JSON.

Поддерживаемые протоколы:

- VLESS
- VMess
- Trojan
- Shadowsocks

Система автоматически:

1. Загружает публичные источники конфигураций.
2. Извлекает VPN URI из обычного текста и Base64-подписок.
3. Удаляет дубликаты.
4. Парсит поддерживаемые протоколы.
5. Генерирует временную Xray-конфигурацию.
6. Запускает Xray и проверяет работу через SOCKS5.
7. Получает внешний IP через VPN.
8. Проверяет доступность YouTube через VPN.
9. Отбрасывает серверы с latency выше 500 ms.
10. Определяет страну VPN-сервера через GeoIP.
11. Генерирует название вида "🇳🇱 Нидерланды #1".
12. Создаёт постоянный Xray JSON.
13. Сохраняет рабочие конфигурации в "servers/".
14. Запоминает уже обработанные URI через SHA-256.
15. Автоматически коммитит новые серверы через GitHub Actions.

Архитектура

sources.txt
     │
     ▼
 scanner.py
     │
     │  public VPN URIs
     ▼
  parser.py
     │
     │  normalized configuration
     ▼
  converter.py
     │
     │  temporary Xray config
     ▼
   tester.py
     │
     ├── Xray startup
     ├── SOCKS5
     ├── external IP
     ├── YouTube
     └── latency <= 500 ms
     │
     ▼
   geoip.py
     │
     ▼
  remarks.py
     │
     ▼
🇳🇱 Нидерланды #1
     │
     ▼
  converter.py
     │
     ▼
servers/NewGeneratedServerN.json

Структура проекта

.
├── .github/
│   └── workflows/
│       └── scanner.yml
├── servers/
├── data/
│   └── known_servers.json
├── src/
│   ├── main.py
│   ├── scanner.py
│   ├── parser.py
│   ├── tester.py
│   ├── converter.py
│   ├── geoip.py
│   ├── remarks.py
│   └── utils.py
├── sources.txt
├── requirements.txt
├── README.md
└── .gitignore

Поддерживаемые URI

Scanner распознаёт:

vless://
vmess://
trojan://
ss://
shadowsocks://

Другие схемы не ломают работу программы. Они пропускаются и выводятся в лог:

[!] UNSUPPORTED_PROTOCOL: 'hysteria2' detected. Skipping.

Это позволяет в будущем добавить поддержку новых протоколов.

Проверка серверов

Сервер считается рабочим только после прохождения всех основных проверок:

Xray config valid
        ↓
Xray started
        ↓
SOCKS5 available
        ↓
External IP obtained
        ↓
YouTube reachable through VPN
        ↓
Latency <= 500 ms
        ↓
WORKING

Если хотя бы одна обязательная проверка не проходит, конфигурация не сохраняется в "servers/".

YouTube

Проверка YouTube выполняется именно через SOCKS5-прокси Xray.

Это позволяет отличить сервер, который просто доступен по TCP, от сервера, через который реально проходит веб-трафик.

Latency

Максимально допустимая задержка:

500 ms

Если результат выше:

501 ms

сервер отклоняется.

GeoIP и remarks

После успешной проверки внешний VPN IP используется для определения страны.

Например:

IP → Netherlands
     ↓
🇳🇱 Нидерланды

Первый сервер страны:

🇳🇱 Нидерланды #1

Второй:

🇳🇱 Нидерланды #2

При следующем запуске нумерация не сбрасывается — программа анализирует уже существующие JSON в "servers/".

Если страна не определена:

🇫🇲 Неизвестная страна #1

Дубликаты

Каждый найденный URI получает SHA-256 fingerprint.

Fingerprint сохраняются в:

data/known_servers.json

При следующих запусках уже обработанные URI пропускаются.

Начальное содержимое файла:

[]

Источники

Публичные источники находятся в:

sources.txt

Каждая ссылка указывается с новой строки:

https://example.com/subscription.txt
https://example.com/nodes.txt

Строки, начинающиеся с "#", игнорируются.

Источник может содержать:

- обычные VPN URI;
- Base64-подписку;
- несколько URI;
- смешанный текст.

Зависимости

"requirements.txt":

requests>=2.31.0
PySocks>=1.7.1
urllib3>=2.0.7

Установка:

python -m pip install -r requirements.txt

Локальный запуск

1. Клонирование

git clone <repository-url>
cd <repository-directory>

2. Установка зависимостей

python -m pip install -r requirements.txt

3. Установка Xray-core

Скачайте актуальный официальный бинарный файл Xray-core для вашей системы и поместите его в корень проекта:

.
├── xray
├── src/
├── servers/
└── ...

Для Windows:

xray.exe

Бинарный файл Xray не должен добавляться в Git.

4. Запуск

Linux/macOS:

chmod +x xray
PYTHONPATH=src python src/main.py

Windows:

$env:PYTHONPATH="src"
python src/main.py

GitHub Actions

Сканер может работать автоматически через GitHub Actions.

Workflow находится здесь:

.github/workflows/scanner.yml

Он запускается:

- вручную через "workflow_dispatch";
- автоматически по расписанию.

После запуска GitHub Actions:

download sources
      ↓
extract URIs
      ↓
parse
      ↓
test
      ↓
GeoIP
      ↓
generate JSON
      ↓
servers/
      ↓
git commit
      ↓
git push

Для записи результатов workflow использует:

permissions:
  contents: write

Генерируемые файлы

Рабочие конфигурации сохраняются как:

servers/NewGeneratedServer1.json
servers/NewGeneratedServer2.json
servers/NewGeneratedServer3.json
...

Номер нового файла определяется по уже существующим конфигурациям.

Пример:

servers/
├── NewGeneratedServer1.json
├── NewGeneratedServer2.json
└── NewGeneratedServer3.json

Следующий сервер получит:

NewGeneratedServer4.json

Безопасность

Исходные URI могут содержать чувствительные данные:

- UUID;
- пароли;
- Shadowsocks credentials;
- другие параметры доступа.

Поэтому полные URI не должны выводиться в GitHub Actions logs.

".gitignore" также исключает:

.env
xray
xray.exe
*.log
__pycache__/

Будущая поддержка

Архитектура позволяет добавлять новые протоколы без переписывания всего проекта.

Планируемые направления:

Hysteria2
WireGuard
TUIC

Для нового протокола необходимо добавить:

scanner → parser → converter → tester

а затем проверить его совместимость с актуальной документацией соответствующего проекта.

Ограничения

Проект работает только с публичными источниками конфигураций.

Он не создаёт VPN-серверы самостоятельно — он ищет уже опубликованные конфигурации, проверяет их работоспособность и преобразует подходящие конфигурации в формат Xray.

Актуальная совместимость протоколов зависит от версии установленного Xray-core.
