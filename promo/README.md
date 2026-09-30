# Fahkle motion piece

A 15-second, 1080p60 motion graphics spot for Fahkle: `fahkle-motion.mp4`.

Everything is procedural. `scene.html` draws each frame on a canvas as a pure function of time, with real 3D dice, 4× sub-frame motion blur, film grain and glitch post effects. `synth.py` generates the 120 BPM score, and `render.js` drives headless Chromium and pipes raw frames into ffmpeg.

```
python3 synth.py                                    # -> audio.wav
node render.js stills 2.0,9.0,12.6                   # preview PNGs into ./stills
node render.js video out.mp4 4 audio.wav             # full render (FFMPEG=/path/to/ffmpeg)
```
