# video/ — explainer video build

Everything needed to turn `script.md` into a finished 1080p video.

| path | what |
|---|---|
| `script.md` | final narration (17 scenes S01–S17) with VISUALS ids and ONSCREEN captions. Not edited by any script. |
| `visuals/` | the stills, 1920×1080 PNG (`V01_title.png` … `V25_close.png`; `V22a…d` are the four area cards). |
| `visuals.md` | one line per still: what it shows and where every number comes from. |
| `thumbnail.png` | 1280×720 thumbnail. |
| `tts/Sxx.txt` | narration per scene with the pronunciation fixes applied (written by the renderer). Paste these into ElevenLabs. |
| `audio/Sxx.mp3` | your voice-over, one file per scene (you create these). |
| `out/` | renders: `mh370_reanalysis_animatic.mp4` (silent), `mh370_reanalysis.mp4` (voiced), matching `.srt`, `*_timeline.json`, `frames/` (sample stills). |
| `data/` | small data copies used by the visuals (WSPR extract from wspr.live and the hourly tables derived from it). |
| `description.md` | YouTube description; its chapter block is rewritten on every full render. |

Run everything from the project root (`mh370-open/`) with the project venv. ffmpeg comes from the
`imageio-ffmpeg` wheel installed in `.venv`, so no system ffmpeg is needed.

## 1. Regenerate the stills

```sh
.venv/bin/python -I scripts/video_visuals.py            # all stills + thumbnail + visuals.md
.venv/bin/python -I scripts/video_visuals.py V12 V21    # just some (prefix match: V22 -> all four cards)
```

The stills read the project outputs directly (`outputs/*`, `data/derived/*`), so re-running them after the
analysis changes keeps the numbers on screen in sync. Takes about 20 s.

## 2. Make the voice-over (ElevenLabs)

1. Write the TTS copies (the renderer also does this on every run):
   `.venv/bin/python -I scripts/video_render.py --tts-only`
   This applies the pronunciation list at the top of `script.md` (WSPR → whisper, IMOS → eye-moss,
   colsto → col-sto, CSIRO → C-S-I-R-O, ATSB → A-T-S-B, DSTG → D-S-T-G, Réunion → ray-union, UTC → U-T-C)
   to `tts/Sxx.txt` only.
2. In ElevenLabs, generate **one file per scene** from `tts/S01.txt` … `tts/S17.txt`, using the same voice,
   model and settings for all 17. Listen for the numbers (e.g. "38.2", "7,500", "Mach zero point eight")
   and regenerate any scene that sounds wrong.
3. Download as MP3 and save as `video/audio/S01.mp3`, `video/audio/S02.mp3`, … `video/audio/S17.mp3`
   (`.wav`, `.m4a`, `.flac` also work). Don't add silence; the renderer adds 0.6 s after each scene.

Optional, scripted (check the current ElevenLabs API docs first; needs your API key and a voice id):

```sh
export ELEVEN_API_KEY=...; VOICE=...   # your key and chosen voice id
mkdir -p video/audio
for f in video/tts/S*.txt; do
  id=$(basename "$f" .txt)
  jq -n --rawfile t "$f" '{text: $t, model_id: "eleven_multilingual_v2"}' |
  curl -s -X POST "https://api.elevenlabs.io/v1/text-to-speech/$VOICE?output_format=mp3_44100_128" \
       -H "xi-api-key: $ELEVEN_API_KEY" -H "Content-Type: application/json" -d @- -o "video/audio/$id.mp3"
done
```

## 3. Render

```sh
.venv/bin/python -I scripts/video_render.py              # voiced: uses video/audio/ if any file exists
.venv/bin/python -I scripts/video_render.py --animatic   # silent animatic (ignores audio)
.venv/bin/python -I scripts/video_render.py --scenes S09,S14 --animatic   # quick preview of a few scenes
```

Options: `--no-captions` (drop the burned-in lower thirds), `--workers 8`, `--crf 20` (quality),
`--frames 6` (sample stills written to `out/frames/`).

What the renderer does:
- **Scene length** = voice-over length + 0.6 s when `audio/Sxx.*` exists, otherwise words ÷ 2.5 + 1.0 s.
  Scenes without audio get silence, so you can render with only some scenes voiced.
- **Stills** within a scene share its time evenly, except where `SCENE_WEIGHTS` in
  `scripts/video_render.py` ties a still to particular narration paragraphs (S03, S12, S14) or gives fixed
  weights (S01, S04). Each still gets a slow 4 % Ken Burns move; consecutive stills crossfade over 0.5 s;
  the video fades in from and out to navy.
- **Captions** (ONSCREEN) appear as lower thirds during the narration paragraph listed for them in
  `CAPTION_PARAS` (up to 8 s each), timed proportionally to text length (or to the audio, once present).
- **Output**: `out/mh370_reanalysis.mp4` (or `_animatic.mp4`): 1920×1080, 30 fps, H.264 yuv420p, AAC
  stereo 48 kHz (silent track in the animatic), plus an `.srt` built from the narration (≤ 2 lines,
  ≤ 42 characters per line, timed proportionally within each scene), a `*_timeline.json` with every
  scene and still start time, and the chapter list in `description.md`.
- The renderer checks the container duration against the sum of the scene lengths and warns on a mismatch.

Rendering the full animatic (18:32 at the 2.5 words/s placeholder pace) took about 5 minutes on this machine
(8 worker processes) and produced a 260 MB file; a full decode check takes ~15 s.

## 4. Swap or reorder visuals

- **Replace a still**: overwrite `visuals/<ID>.png` with any 1920×1080 PNG of the same name and re-render.
  Keep important content out of the bottom ~150 px while captions are on, and away from the outer ~50 px
  (the Ken Burns move crops slightly).
- **Use a different still in a scene**: change the ids on that scene's `VISUALS:` line in `script.md`
  (that line is not narration). An id resolves to `visuals/<ID>.png`, or, if that file does not exist,
  to every file starting with its `Vnn` prefix (that is how `V22_area_cards` becomes the four cards).
- **Change timing**: edit `SCENE_WEIGHTS` / `CAPTION_PARAS` near the top of `scripts/video_render.py`.

## Notes on content

- Every number in the stills comes from the project outputs, the shared geometry or the reports named in
  each still's source line; `visuals.md` lists the source for each still. Schematic stills (V02, V10) are
  badged "ILLUSTRATION".
- V05 shows measured BFO and the project's best-fit southern path only; a northern-route prediction was
  not computed (no credible northern path model in the project).
- Where `script.md` and the project outputs differ, the stills follow the outputs; the differences are
  listed in the hand-over notes (e.g. the ATSB band width, which the stills do not label as ±25 NM).
- Licence notes for monetised use: wspr.live data are for non-commercial use, and the DSTG book (used for
  the digitised curve in V12) is CC BY-NC 4.0. Check both before monetising.

## Single-document voice-over (alternative to per-scene files)

1. Build the full narration as plain text (no markdown, pronunciation fixes applied):
   `.venv/bin/python -I scripts/voiceover.py build` → `video/voiceover_full.txt`
   It's about 16,200 characters. If your ElevenLabs model or plan has a smaller per-generation limit,
   use ElevenLabs Studio (made for long documents), or generate it in a few consecutive chunks.
   Splitting chunks at blank lines (paragraph breaks) works best.
2. Export the audio: one file, or several files in order.
3. Cut it back into scenes:
   `.venv/bin/python -I scripts/voiceover.py split path/to/voiceover.mp3 [part2.mp3 ...]`
   This writes `video/audio/S01.wav … S17.wav` at 44.1 kHz, plus `video/audio/cuts.csv`.
   Each boundary is found by transcribing the audio locally with faster-whisper (base.en, downloaded
   once from Hugging Face; no account needed), matching each scene's last and first words, and cutting
   in the pause between them. Tested on a synthetic 14-minute read: all 16 boundaries landed correctly.
   If a cut is off, edit the times in `cuts.csv` and run `split --use-cuts`.
4. Render: `.venv/bin/python -I scripts/video_render.py`.

The per-scene text files in `video/tts/` are kept. Use whichever workflow you prefer, but don't leave
stale `Sxx.mp3` files from one workflow next to `Sxx.wav` files from the other in `video/audio/`.
