# JOSEPH PONNAR – 4K intro

`make_intro.py` renders a 3840x2160, 30 fps, 16:9 intro (48.7 s) set to *Theeya Vantha*.

- The song's beat grid was measured at 114 BPM. Every cut, flash and zoom-punch lands on a beat or a bar downbeat.
- 0–14 s: lion shots cut on each bar · 14–33 s: 2-bar shots with soft crossfades · 33–35 s: a cut on every beat
- 35 s: fire-explosion reveal, timed so its peak lands on the 39.2 s downbeat
- 41.3 s **JOSEPH** and 42.4 s **PONNAR** slam in (Anton, bold block capitals, gold), then a light sweep and a fade-out
- The vertical clips are cropped to 16:9 so no captions, watermarks or the template's "Your Logo" text appear.

Run: `python3 make_intro.py out.mp4 [scale]` (scale 0.25 = quick preview). Requires ffmpeg, numpy, Pillow and the Anton font in `fonts/`.
