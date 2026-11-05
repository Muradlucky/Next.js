# Video tools stack — analysis

**Remotion · HyperFrames · FFmpeg · whisper.cpp · yt-dlp**

- Дата анализа: **2026-11-05**
- Источник: reel @potapovfx «Вот как смонтировать видео с помощью Claude Code», «Шаг второй».
- Status: **downloaded, not used.** Репозитории скачаны (shallow clone) только для чтения кода и документации. Ничего не собиралось, не устанавливалось и не запускалось. Скрипт загрузки с закреплёнными версиями — [`fetch.sh`](./fetch.sh).

---

## TL;DR

| Repo | Что это | Stars | License | Версия | Verdict |
|---|---|---|---|---|---|
| [yt-dlp](https://github.com/yt-dlp/yt-dlp) | загрузчик видео/аудио | 205k | Unlicense | 2026.10.26 | ✅ Industry standard, альтернатив нет. Юридический риск — в контенте, не в инструменте |
| [FFmpeg](https://github.com/FFmpeg/FFmpeg) | обработка любого видео/аудио | 66.5k (зеркало) | LGPL 2.1+ (GPL опционально) | 9.0.2 stable, 9.1 готовится | ✅ De facto standard, замены нет. Всё остальное работает поверх него |
| [whisper.cpp](https://github.com/ggml-org/whisper.cpp) | локальная транскрипция речи | 55k | MIT | v1.9.5 | 🟡 Надёжный baseline, но уже **не лидер**: Parakeet v3 точнее и быстрее, WhisperX точнее по таймкодам слов |
| [Remotion](https://github.com/remotion-dev/remotion) | видео как React-код | 71k | Remotion License (source-available) | 4.0.541 | ✅ Самый зрелый в категории, но **платный для компаний от 4 человек** |
| [HyperFrames](https://github.com/heygen-com/hyperframes) | видео как HTML (от HeyGen) | 79k | Apache 2.0 | 0.9.15 (pre-1.0) | 🟡 Promising, but young (с марта 2026) + встроенный upsell в платный HeyGen |

**Bottom line.** Набор правильный — это действительно стандартный open-source стек для монтажа через AI-агента. Но «самое годное» — с тремя оговорками:

1. **whisper.cpp** сейчас не лучший по качеству/скорости — для русского нужно сравнить с Parakeet v3 и WhisperX.
2. **Remotion vs HyperFrames** — это конкуренты, нужен один. Выбор зависит от лицензии и пилота.
3. В стеке **нет слоя rough cut** (автоматическое вырезание пауз/сцен) — без него монтаж «говорящей головы» неполный.

---

## How it fits together

```
 yt-dlp ──► FFmpeg ──► Whisper ──► Remotion / HyperFrames ──► FFmpeg
(скачать)  (аудио,    (текст +     (субтитры, плашки,          (финальный
            нарезка)   таймкоды     графика по сценарию)         encode под
                       слов)                                    Reels/YT)
```

Claude Code here is the orchestrator: пишет команды FFmpeg, код композиций, читает транскрипт и решает, что вырезать.

Key point: это не 5 независимых вещей, а **3 слоя**. Remotion и HyperFrames сами используют FFmpeg внутри (headless Chrome → кадры → FFmpeg), и оба уже имеют встроенную интеграцию с whisper.cpp (`@remotion/install-whisper-cpp`, `npx hyperframes transcribe`).

---

## 1. yt-dlp — download layer

**What it is.** CLI и Python-библиотека для скачивания видео/аудио с 1 700+ сайтов/экстракторов (YouTube, Instagram, TikTok, VK и т.д.). Форк youtube-dl, давно его заменил.

- Activity: релизы раз в 1–2 недели (последний — 2026.10.26), коммиты ежедневно.
- 2 766 открытых issues — норма для такого масштаба (в основном «сайт X сломался»).
- **Is it the best? Yes.** Самый популярный проект из пяти, реальных open-source конкурентов нет.

**Нюансы:**

- Для полноценной работы с YouTube с конца 2025 нужен **JS runtime (рекомендован `deno`) + `yt-dlp-ejs`**, иначе часть форматов недоступна. YouTube регулярно ломает загрузку (PO tokens, bot checks) → yt-dlp нужно часто обновлять. «Поставил и забыл» не работает.
- Для склейки видео+аудио и конвертации нужен FFmpeg.
- **Юридически:** скачивание с YouTube/Instagram нарушает их Terms of Service, а использование чужого контента в своих роликах — это вопрос авторского права. Сам инструмент легален; риск в том, *что* скачивать. Безопасно: свои видео, контент под свободной лицензией (Creative Commons), материалы с письменного разрешения автора. Для коммерческих роликов чужой контент без разрешения не использовать.

**Fit:** ✅ как вспомогательный инструмент — референсы, свои старые ролики, исходники с разрешения.

---

## 2. FFmpeg — the foundation

**What it is.** Библиотеки (libavcodec, libavformat, libavfilter…) + CLI `ffmpeg`/`ffprobe` для декодирования, кодирования, нарезки и фильтрации практически любого медиаформата.

- Версия: stable **9.0.2** (ветка 9.0 «Lei» вышла в августе 2026), **9.1** в процессе релиза.
- На GitHub — только зеркало `git.ffmpeg.org`, поэтому 3 issues и 66k stars не отражают реальный масштаб проекта.
- **Is it the best? Yes, de facto standard.** MoviePy, auto-editor, Remotion, HyperFrames — всё это обёртки над FFmpeg.

**Нюансы:**

- Interesting: начиная с FFmpeg 8.0 есть встроенный фильтр `whisper` (`af_whisper`, на базе whisper.cpp) — транскрипция прямо в FFmpeg. Но только в сборке с `--enable-whisper`; в обычных пакетах его нет.
- Лицензия: по умолчанию LGPL 2.1+. Сборки с `--enable-gpl` (почти все готовые сборки — из-за x264/x265) — GPL. Для **использования** (монтаж своих видео) это не важно. Важно только если будем **распространять** продукт со встроенным FFmpeg.
- Синтаксис фильтров сложный — как раз то место, где Claude Code экономит больше всего времени.
- Собирать из исходников не нужно: системный пакет (`brew install ffmpeg` / `apt install ffmpeg`).

**Fit:** ✅ обязательный компонент.

---

## 3. whisper.cpp — speech-to-text

**What it is.** Порт модели OpenAI Whisper на C/C++ от ggml-org (Georgi Gerganov — автор llama.cpp). Работает локально, без интернета: CPU, Apple Silicon (Metal / Core ML), NVIDIA, Vulkan, AMD.

- v1.9.5, активная разработка, MIT.
- Умеет: многоязычные модели (включая русский), вывод SRT/VTT/JSON, VAD (Silero), квантизация моделей, word-level timestamps (`-ml 1`, **experimental**), разделение спикеров (tinydiarize, **experimental**).

**Is it the best? Not anymore — по качеству и скорости.** Альтернативы (Nov 2026):

| Инструмент | Stars | Когда лучше |
|---|---|---|
| whisper.cpp | 55k | Mac/ноутбук, без Python, CPU, максимальная кроссплатформенность |
| [faster-whisper](https://github.com/SYSTRAN/faster-whisper) | 26.5k | GPU-сервер, batch, Python; по данным обзоров до ~4× быстрее оригинального Whisper |
| [WhisperX](https://github.com/m-bain/whisperX) | 25k | **Точные таймкоды слов** (forced alignment на wav2vec2) + разделение спикеров — важно для субтитров «слово в слово» |
| NVIDIA Parakeet TDT 0.6B v3 | — | Быстрее в 5–10× и точнее (avg WER ~6.05% vs 7.44% у whisper.cpp — данные из документации HyperFrames). Поддерживает `ru` и `uk`. Именно его HyperFrames ставит по умолчанию, whisper.cpp — fallback |

**Нюансы:**

- Whisper «галлюцинирует» на тишине и музыке (выдумывает текст) → всегда включать `--vad`.
- Word timestamps в whisper.cpp помечены как experimental — для караоке-субтитров (как в Reels) точнее WhisperX или Parakeet.
- **Русский язык:** нужны multilingual-модели (`large-v3-turbo`, `medium`), не `*.en`. Внимание: `npx hyperframes transcribe` без установленного Parakeet по умолчанию берёт `small.en` (только английский) — язык/модель нужно указывать явно.

**Fit:** ✅ годится как baseline. Перед выбором — тест на 2–3 наших русских записях: whisper.cpp `large-v3-turbo` vs Parakeet v3 vs WhisperX.

---

## 4. Remotion — video as React code

**What it is.** Фреймворк, где видео описывается React-компонентами и рендерится через headless Chrome + FFmpeg. С 2020 года, монорепо из 130+ пакетов, документация ~1 200 страниц.

- v4.0.541, patch-релизы почти ежедневно. Очень зрелый.
- **Agent-ready:** официальные Agent Skills (13 штук: `remotion-captions`, `remotion-render`, `remotion-best-practices`…) и плагин для Claude Code.
- Экосистема: шаблоны (TikTok-субтитры, audiogram, prompt-to-video, music visualization), `<Player>` для встраивания в веб, Lambda / Cloud Run для облачного рендера, `@remotion/captions`, интеграция whisper.cpp и OpenAI Whisper.
- **Совместим с этим репозиторием:** у Remotion есть шаблон `template-next-app-tailwind`, то есть он встраивается в Next.js напрямую.

**Нюансы:**

- **License — главный нюанс.** Это не open source, а source-available:
  - Бесплатно: физлица; коммерческие компании **до 3 сотрудников включительно**; некоммерческие организации; оценка/тестирование до коммерческого использования.
  - Компании **от 4 сотрудников** обязаны купить Company License (цены — на remotion.pro).
  - Запрещено: продавать, сдавать в аренду или перелицензировать собственную модификацию Remotion.
  - В коде уже подготовлено требование передавать `licenseKey` при рендере (для бесплатной лицензии — `"free-license"`); при рендере с ключом отправляется usage event на серверы Remotion. В v5 это станет обязательным.
- Нужен React — для агента это не проблема: у моделей много обучающих данных по Remotion. В независимом тесте ([woshipm](https://www.woshipm.com/?p=6408883)) на одном и том же промпте Remotion дал готовый ролик быстрее и предсказуемее, чем HyperFrames.
- Рендер ресурсоёмкий (Chrome на каждый кадр) — длинные видео локально рендерятся медленно.

**Is it the best? Yes** — самый зрелый в категории «видео как код». Альтернатива с MIT-лицензией — [Motion Canvas](https://github.com/motion-canvas/motion-canvas) (19.7k), но он развивается медленнее и ориентирован на анимации-объяснения, а не на монтаж.

**Fit:** ✅ если команда ≤3 человек или готовы платить. Лучший выбор для сложных шаблонных роликов и для встраивания в наш Next.js.

---

## 5. HyperFrames — video as HTML (by HeyGen)

**What it is.** Open-source фреймворк от HeyGen (AI-видео компания). Видео описывается обычным HTML + CSS + data-атрибутами (`data-start`, `data-duration`, `data-track-index`), анимации — GSAP / CSS / Lottie / Three.js. Рендер так же: headless Chrome + FFmpeg. Прямо позиционируется как «Remotion, но на HTML и для агентов».

- Создан в **марте 2026** (8 месяцев), версия **0.9.15 (pre-1.0)**, Apache 2.0.
- 79k stars за 8 месяцев — больше, чем у Remotion за 6 лет. Во многом это маркетинг HeyGen (UTM-ссылки по всему README, desktop app, Pro plan). **Stars ≠ maturity.**
- Очень высокая скорость изменений: последние 50 коммитов сделаны за ~15 часов, минимум 15 из них — с AI-агентом в co-author. Плюс: быстро развивается. Минус: API может меняться, возможны регрессии.
- **Agent UX — лучший из двух:** плагин для Claude Code, 9 skills, каталог ~450 готовых блоков (переходы, субтитры, графики, карты, 3D), `npx hyperframes check` (lint), Studio, рендер в AWS Lambda.
- Транскрипция «из коробки»: Parakeet v3 → fallback на whisper.cpp, с word timestamps.

**Нюансы (важно):**

- **Upsell в HeyGen встроен в skills.** Skill `media-use` прямо инструктирует агента: использовать модели HeyGen; локальные бесплатные инструменты — *только если человек попросит*; *не предлагать более дешёвые/бесплатные замены*; *не озвучивать цены без запроса*. То есть агент по умолчанию будет тратить платные кредиты HeyGen, если вы залогинены. Защита: не логиниться в HeyGen без решения по бюджету; задать лимит в `.hyperframes/credit-limit.json` (`{"credits": N}`); явно требовать локальные инструменты (`--local-only`).
- **Telemetry включена по умолчанию** (команды, производительность рендера, system info; после логина — привязка к аккаунту). Отключение: `npx hyperframes telemetry disable` или переменные `HYPERFRAMES_NO_TELEMETRY=1` / `DO_NOT_TRACK=1`.
- Требует Node.js 22+.
- Независимые отзывы смешанные: хорошо для простой графики (текст, подписи, overlays, data-графика), хуже для сложной режиссуры движения. В одном тесте: текст наложился на спикера, длинные участки без анимации, сломались шрифты после рендера (шрифт был в браузере, но не установлен локально). **Для кириллицы это особенно актуально** — шрифты с кириллицей нужно класть прямо в проект.
- Часть skills платные (HyperFrames Pro): `/reverse-any-video`, `/style-sampling`.

**Is it the best? Promising, but not proven.** Лучшая лицензия (Apache 2.0 — бесплатно для компании любого размера) и лучший agent tooling, но заметно меньше зрелости, чем у Remotion.

**Fit:** 🟡 хороший кандидат, если лицензия Remotion не подходит. Использовать только с отключённой телеметрией и под контролем трат.

---

## Remotion vs HyperFrames — what to choose

| Criterion | Remotion | HyperFrames |
|---|---|---|
| Возраст / зрелость | 6 лет, v4.0.x | 8 месяцев, v0.9.x |
| Лицензия | Платно для компаний от 4 человек | Apache 2.0, бесплатно всем |
| Формат | React (TSX), нужен bundler | HTML + GSAP, без build step |
| Результат агента «из коробки» | Стабильнее (больше обучающих данных) | Нестабильно по отзывам |
| Agent tooling | Skills + плагин | Skills + плагин + каталог ~450 блоков + lint |
| Встраивание в Next.js | Нативно (`<Player>`, шаблон Next.js) | Через web component `<hyperframes-player>` |
| Скрытые расходы | Company License | Кредиты HeyGen, если не контролировать агента |

**Recommendation:** не тянуть оба в production. Сделать **pilot**: один и тот же ролик (30–60 сек, русская речь + субтитры + 2–3 графических блока) в обоих; сравнить время, расход токенов и качество. Если команда ≤3 человек — default choice: Remotion.

---

## What's missing in the stack

Пост показывает «шаг второй» — инструменты рендера. Для реального монтажа talking-head нужен ещё слой **rough cut** (черновая нарезка):

| Tool | Stars | License | Зачем |
|---|---|---|---|
| [auto-editor](https://github.com/WyattBlue/auto-editor) | 5.8k | Unlicense | Автоматически вырезает паузы/тишину — основная рутина монтажа «говорящей головы» |
| [PySceneDetect](https://github.com/Breakthrough/PySceneDetect) | 5.4k | BSD-3 | Находит склейки/смены сцен — для нарезки референсов и длинных видео |
| [WhisperX](https://github.com/m-bain/whisperX) | 25k | BSD-2 | Точные субтитры слово-в-слово + спикеры |

---

## Scenarios — what to use for what

| Сценарий | Инструменты |
|---|---|
| Reels/Shorts из «говорящей головы» с субтитрами | FFmpeg + auto-editor (паузы) + Whisper/Parakeet (текст) + Remotion/HyperFrames (субтитры, плашки) |
| Нарезка клипов из длинного видео/подкаста | yt-dlp (только свой контент) + Whisper (транскрипт) + Claude (выбор моментов) + FFmpeg (вырезать, кроп 9:16) |
| Explainer / motion graphics без съёмки | Remotion или HyperFrames (+ TTS) |
| Шаблонные ролики массово (десятки–сотни вариантов) | Remotion (зрелый batch и Lambda) |
| Только субтитры к готовому видео | Whisper + FFmpeg (вжечь SRT) — Remotion/HyperFrames не нужны |

---

## Before we start using it

Сейчас ничего не установлено и не запускалось. При переходе к использованию:

1. Ставить из официальных источников (brew / apt / npm / pip), не из форков; закрепить версии.
2. HyperFrames: сразу отключить telemetry; не логиниться в HeyGen без решения по бюджету; задать credit limit.
3. Remotion: до коммерческого использования определить, подпадаем ли под Free License (≤3 сотрудника).
4. yt-dlp: скачивать только контент, на который есть права.
5. Работать в отдельной папке/контейнере, не внутри этого Next.js-проекта.
6. Для русских субтитров — положить в проект шрифты с кириллицей.

## Next steps

1. Решить вопрос лицензии Remotion: сколько человек в команде, коммерческое ли использование.
2. Pilot: один ролик в Remotion и в HyperFrames.
3. Тест транскрипции на русском: whisper.cpp `large-v3-turbo` vs Parakeet v3 vs WhisperX на 2–3 наших записях.
4. Добавить auto-editor в стек для черновой нарезки.

---

## Appendix — versions analysed

| Repo | Commit (HEAD on 2026-11-05) | Latest release tag | Pinned in `fetch.sh` |
|---|---|---|---|
| yt-dlp/yt-dlp | `412e7f0` | `2026.10.26` | `2026.10.26` |
| FFmpeg/FFmpeg | `cc62602` (master) | `n9.0.2` | `n9.0.2` |
| ggml-org/whisper.cpp | `1e0d76b` | `v1.9.5` | `v1.9.5` |
| remotion-dev/remotion | `ac57c702` | `v4.0.541` | `v4.0.541` |
| heygen-com/hyperframes | `5f7b85c` | `v0.9.15` | `v0.9.15` |

Stars/licenses — по данным GitHub на 2026-11-05.

## Sources

- Код и документация репозиториев (README, LICENSE, `skills/`, `docs/`, `packages/`).
- [FFmpeg 9.0 Released — Phoronix](https://www.phoronix.com/news/FFmpeg-9.0-Released)
- [FFmpeg 9.1 Preps For Release — Phoronix](https://phoronix.com/news/FFmpeg-9.1-Releasing)
- [yt-dlp now requires Deno JS runtime — Gigazine](https://gigazine.net/gsc_news/en/20250925-yt-dlp-deno-javascript-runtime)
- [Best Open Source Speech-to-Text Models to Self-Host in 2026 — Pinggy](https://pinggy.io/blog/best_open_source_self_hosted_speech_to_text_models/)
- [Parakeet.cpp vs Whisper — ModelsLab](https://modelslab.com/blog/audio-generation/parakeet-cpp-vs-whisper-self-hosted-asr-comparison-2026)
- [HyperFrames vs Remotion — официальное сравнение HeyGen](https://hyperframes.heygen.com/guides/hyperframes-vs-remotion) (сторона заинтересованная)
- [Remotion vs HyperFrames: практический тест — woshipm](https://www.woshipm.com/?p=6408883)
- [Hyperframes vs Remotion vs Selects — Cutback](https://cutback.video/blog/hyperframes-vs-remotion-vs-selects) (автор продаёт конкурирующий продукт)
