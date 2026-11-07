# Video lab — step-by-step plan

- Обновлено: **2026-11-07**
- Контекст: работаю один, **personal, non-commercial use**.
- Основано на: [video-tools/README.md](./video-tools/README.md) (видео-стек) и [claude-repos/README.md](./claude-repos/README.md) (10 skills для Claude).

## Decisions so far

| Вопрос | Решение |
|---|---|
| Лицензия Remotion | Free License подходит: физлицо, некоммерческое использование. Company License не нужна |
| Remotion vs HyperFrames | Делаем pilot обоих на одном ролике, потом выбираем один |
| Транскрипция | Сравниваем 3 движка на русской речи |
| Instagram | Отдельный этап позже (этап 8) |
| Skills для Claude | Сначала только Humanizer; Last30Days и Diagram Design — позже |

## Overview

| # | Этап | Результат | Время (оценка) |
|---|---|---|---|
| 0 | Setup | Установлены инструменты, есть папка проекта | 1 вечер |
| 1 | Исходник | 1 свой ролик 30–60 сек | 30 мин |
| 2 | Transcription test | Выбран движок для русского | 1–2 вечера |
| 3 | Rough cut | Ролик без пауз | 1 вечер |
| 4 | Pilot: Remotion | Готовый ролик + заметки | 1–2 вечера |
| 5 | Pilot: HyperFrames | Готовый ролик + заметки | 1–2 вечера |
| 6 | Compare & choose | Выбран один фреймворк | 30 мин |
| 7 | Final encode | Файл под Reels | 15 мин |
| 8 | Instagram (later) | Механика скачивания reels | отдельно |
| 9 | Scripts workflow | Процесс «тема → сценарий → ролик» | после пилота |

---

## Token economy — важно с первого шага

Лимит токенов уже закончился один раз, поэтому:

1. **Один этап = одна сессия Claude.** В начале сессии: «Работаем по research/PLAN.md, этап N». Так Claude не тратит токены на повторный анализ.
2. В папке проекта держать короткий `CLAUDE.md` (5–10 строк: цель, выбранные инструменты, где лежат файлы).
3. Не ставить плагины «про запас»: каждый добавляет текст в контекст.
4. Длинные выводы команд (логи рендера, ffmpeg) не вставлять в чат целиком — только последние строки или ошибку.

---

## Stage 0 — Setup

**Где работать.** Рекомендую свой компьютер: рендер видео грузит процессор, а исходники большие.
Облачная сессия Claude Code тоже подходит для тестов, но видео туда надо загружать через репозиторий: GitHub не принимает файлы больше 100 МБ.

**Шаги (macOS):**

1. Установить Homebrew, если его нет (brew.sh).
2. Установить инструменты:
   ```bash
   brew install ffmpeg node deno uv yt-dlp whisper-cpp
   ```
   Node.js должен быть версии 22 или новее: проверить `node -v`.
3. Создать отдельную папку проекта — **не внутри этого Next.js-репозитория**:
   ```bash
   mkdir -p ~/video-lab/{sources,audio,transcripts,cut,pilot-remotion,pilot-hyperframes,renders,fonts}
   ```
4. Скачать 1–2 шрифта с кириллицей в `~/video-lab/fonts/` (например, Inter, Manrope или Montserrat с Google Fonts). Без этого русские субтитры могут сломаться после рендера.
5. Создать `~/video-lab/CLAUDE.md` с кратким описанием проекта.

На Windows вместо brew: `winget install Gyan.FFmpeg OpenJS.NodeJS.LTS astral-sh.uv DenoLand.Deno`, whisper.cpp — готовая сборка со страницы Releases.

✅ Done when: `ffmpeg -version`, `node -v`, `whisper-cli --help` работают.

---

## Stage 1 — Source video

1. Снять на телефон **свой** ролик 30–60 секунд: «говорящая голова», вертикально (9:16), на русском. Специально оставить 2–3 паузы и одну оговорку — проверим нарезку.
2. Положить в `~/video-lab/sources/talk.mp4`.
3. Проверить параметры и извлечь звук для транскрипции:
   ```bash
   cd ~/video-lab
   ffprobe -hide_banner sources/talk.mp4
   ffmpeg -i sources/talk.mp4 -vn -ac 1 -ar 16000 -c:a pcm_s16le audio/talk.wav
   ```

✅ Done when: есть `audio/talk.wav`.

---

## Stage 2 — Transcription test (3 engines)

**Цель:** выбрать движок для русской речи.

**Шаг 2.1. Эталон.** Вручную набрать точный текст ролика (или поправить любой черновой транскрипт) → `transcripts/reference.txt`. С ним сравниваем.

**Шаг 2.2. whisper.cpp:**
```bash
# модели скачиваются один раз: распознавание (~1.6 ГБ) и VAD (маленькая)
mkdir -p models
curl -L -o models/ggml-large-v3-turbo.bin https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-large-v3-turbo.bin
curl -L -o models/ggml-silero-v6.2.0.bin https://huggingface.co/ggml-org/whisper-vad/resolve/main/ggml-silero-v6.2.0.bin

whisper-cli -m models/ggml-large-v3-turbo.bin -l ru \
  --vad -vm models/ggml-silero-v6.2.0.bin \
  -f audio/talk.wav -ojf -osrt -of transcripts/whispercpp
```
`--vad` обязателен: без него Whisper выдумывает текст на паузах.

**Шаг 2.3. Parakeet v3** (через CLI HyperFrames, сначала отключить телеметрию):
```bash
npx hyperframes telemetry disable
npx hyperframes models install parakeet      # ~640 МБ, один раз
npx hyperframes transcribe audio/talk.wav --engine parakeet
```
В HeyGen **не логиниться** (`auth login` не запускать).

**Шаг 2.4. WhisperX:**
```bash
uv tool install whisperx
whisperx audio/talk.wav --model large-v3 --language ru \
  --compute_type int8 --output_format json --output_dir transcripts/whisperx
```
Без видеокарты NVIDIA работает медленно — для минутного ролика это нормально.

**Шаг 2.5. Сравнить** — заполнить таблицу:

| Критерий | whisper.cpp | Parakeet v3 | WhisperX |
|---|---|---|---|
| Ошибок на 100 слов (сверка с эталоном) | | | |
| Пунктуация и заглавные буквы | | | |
| Точность таймкодов 5 слов (на слух, ±0.1 с) | | | |
| Время обработки | | | |
| Сложность установки (1–5) | | | |

✅ Done when: выбран один движок; его результат — `transcripts/talk.json`.

---

## Stage 3 — Rough cut

1. Автоматически вырезать паузы:
   ```bash
   uv tool install auto-editor
   auto-editor sources/talk.mp4 --margin 0.2sec -o cut/talk_cut.mp4
   ```
2. Просмотреть результат. Если режет слишком жёстко — увеличить `--margin`.
3. Оговорку вырезать по транскрипту: попросить Claude найти её в `talk.json` и дать команду ffmpeg с точными таймкодами.
4. **Повторить транскрипцию выбранным движком на `cut/talk_cut.mp4`** — после нарезки таймкоды сдвигаются, а субтитрам нужны новые.

✅ Done when: `cut/talk_cut.mp4` + `transcripts/talk_cut.json`.

---

## Stage 4 — Pilot: Remotion

**Одинаковое ТЗ для обоих пилотов** (сохранить в `~/video-lab/brief.md`):
- формат 1080×1920, 30 fps, длина = длине `talk_cut.mp4`;
- субтитры по словам (подсветка текущего слова), русский, шрифт из `fonts/`;
- плашка с темой в первые 2 секунды;
- 2 графические вставки (например, карточка с цифрой и список из 3 пунктов);
- финальная плашка-CTA.

**Шаги:**
1. `cd ~/video-lab/pilot-remotion && npx create-video@latest` → выбрать шаблон **TikTok** (в нём уже есть субтитры через whisper.cpp).
2. Установить Remotion Agent Skills для Claude Code (инструкция: remotion.dev/docs/ai/skills).
3. В новой сессии Claude: «Сделай ролик по brief.md, видео — cut/talk_cut.mp4, транскрипт — transcripts/talk_cut.json».
4. Превью в Remotion Studio (`npm run dev`), правки, рендер через `npx remotion render`.
5. Лицензия: при рендере через API передавать `licenseKey: "free-license"`.
6. Записать: время, число итераций, расход токенов (команда `/cost` в Claude Code), что пришлось чинить руками.

✅ Done when: `renders/remotion.mp4` + заметки.

---

## Stage 5 — Pilot: HyperFrames

**Перед началом (обязательно):**
```bash
npx hyperframes telemetry disable
```
В HeyGen не логиниться. Если агент предлагает платные модели HeyGen (музыка, голос, генерация) — отказываться, просить только локальные инструменты.

**Шаги:**
1. `cd ~/video-lab/pilot-hyperframes && npx hyperframes init pilot && cd pilot`
2. `npx hyperframes skills update` — ставит только базовый набор skills.
3. В новой сессии Claude — то же ТЗ из `brief.md`.
4. `npx hyperframes preview` → правки → `npx hyperframes check` → `npx hyperframes render`.
5. Проверить шрифты после рендера (кириллица!).
6. Записать те же метрики, что в этапе 4.

✅ Done when: `renders/hyperframes.mp4` + заметки.

---

## Stage 6 — Compare & choose

| Критерий | Remotion | HyperFrames |
|---|---|---|
| Время до готового ролика | | |
| Токены / стоимость (`/cost`) | | |
| Число итераций | | |
| Качество субтитров (1–5) | | |
| Качество графики (1–5) | | |
| Что пришлось чинить руками | | |
| Насколько легко менять потом | | |

Выбрать один; второй удалить, чтобы не путаться. Записать решение в `CLAUDE.md`.

---

## Stage 7 — Final encode for Reels

```bash
ffmpeg -i renders/CHOSEN.mp4 \
  -c:v libx264 -preset slow -crf 18 -pix_fmt yuv420p -r 30 -vf "scale=1080:1920" \
  -af loudnorm=I=-14:TP=-1.5:LRA=11 -c:a aac -b:a 192k -ar 48000 \
  -movflags +faststart renders/final_reels.mp4
```
- `-14 LUFS` — привычная громкость для соцсетей;
- `+faststart` — видео начинает играть до полной загрузки.

✅ Done when: `final_reels.mp4` нормально загружается в Instagram (можно в черновики).

---

## Stage 8 — Instagram download (later, separate mechanics)

**Цель:** забирать reels как референсы — для разбора структуры, хуков, темпа. **Только для личного анализа, не для перепубликации.**

**Инструменты:**

| Tool | Stars | Для чего |
|---|---|---|
| yt-dlp | 205k | Отдельные reels по ссылке. Скачивание профиля целиком сейчас помечено как «currently broken» |
| [instaloader](https://github.com/instaloader/instaloader) | 13.8k | Профили, сохранённые (saved) посты, stories |
| [gallery-dl](https://github.com/mikf/gallery-dl) | 20k | Универсальный загрузчик, тоже умеет Instagram |

Scrapling (из подборки) для Instagram **не использовать** — см. claude-repos/README.md.

**Черновик команд** (проверим, когда дойдём до этапа):
```bash
# один reel, с cookies своего браузера (Instagram часто требует вход)
yt-dlp --cookies-from-browser chrome -o "sources/insta/%(uploader)s_%(id)s.%(ext)s" "https://www.instagram.com/reel/XXXX/"

# свои сохранённые посты
instaloader --login ВАШ_ЛОГИН :saved
```

**Риски — читать до начала:**
- Правила Instagram запрещают автоматический сбор контента. Аккаунт, через который скачиваете, могут временно ограничить (checkpoint, просьба подтвердить вход).
- Поэтому: скачивать понемногу, с паузами, без массовых выгрузок.
- Авторские права: скачанное — только для личного анализа, в свои ролики без разрешения автора не вставлять.

**Дальше по цепочке:** reel → транскрипция (выбранный движок) → Claude разбирает структуру (хук в первые 3 секунды, темп, CTA) → идеи для своих сценариев (этап 9).

---

## Stage 9 — Scripts workflow (после пилота)

1. **Тема:** `/last30days <тема>` — что обсуждают сейчас (только бесплатные источники, cookies браузера не давать).
2. **Референсы:** 3–5 reels по теме (этап 8) → разбор структуры.
3. **Черновик сценария:** Claude пишет по шаблону: хук (0–3 с) → суть → 2–3 тезиса → CTA.
4. **Humanizer:** `/humanizer` по черновику — убрать «AI-звучание». Проверить на русском.
5. **Съёмка → этапы 1–7.**
6. Для explainer-роликов: схемы через Diagram Design → вставка в выбранный фреймворк.

---

## Checklist

- [ ] Stage 0 — setup
- [ ] Stage 1 — source video
- [ ] Stage 2 — transcription test
- [ ] Stage 3 — rough cut
- [ ] Stage 4 — pilot Remotion
- [ ] Stage 5 — pilot HyperFrames
- [ ] Stage 6 — choose
- [ ] Stage 7 — final encode
- [ ] Stage 8 — Instagram mechanics
- [ ] Stage 9 — scripts workflow
