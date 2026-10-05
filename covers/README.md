# Covers

`compose.py` puts the cover text on Midjourney art.

- **Weekly** uses Caravaggio-style portraits (`--ar 3:4`). The sign name is in the sign's colour, with the hook below it.
- **Monthly** uses Doré-style black-and-white skies (`--ar 3:4`). Only the light is tinted in the sign's colour, and the name is in gold italic.

```
pip install pillow
python covers/compose.py covers/example.json
```

Put the art next to the spec file, at the paths it names (`art/leu.webp` for `example.json`). The script writes `out/` beside the spec: one 1080×1920 JPG per entry, plus `grid.jpg`, which shows the batch the way TikTok's profile grid does. Fonts download on the first run.

## Layout rules

- The grid crops 9:16 to 3:4, cutting 240 px off the top and 240 px off the bottom. Everything that matters sits between y 300 and y 1450, above the view count.
- The 3:4 art fills that band exactly. The script extends it to 9:16 using the art's own blurred edges.
- Hooks are at most 2 lines and 30 characters, under the line rules in the covers artifact.
