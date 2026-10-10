# transcribe-and-create-note (builder)

Builds AES-style lecture notes as a Word file: slide on the left (two-thirds width, centred), notes on the right, one page per slide appearance, in lecture order. Used by the `transcribe-and-create-note` Claude skill.

```
python3 build_notes.py scan  deck.pdf -o slides/          # purple-note redaction, render + crop, map.txt, contact sheets
python3 build_notes.py build notes.md --slides slides/ -o EE321-lecture-12-notes.docx --render render/
```

What `build` does: parses the notes markup, auto-splits long pages into `(continued)` pages, converts LaTeX to native Word equations (via pandoc), writes the title page, contents, "Marked as important", the 4-column cheat sheet and an auto-generated Open questions list, then checks for em dashes, recording references, timestamps, unplaced slides, marker wording and cheat-sheet rules.

Needs: Python 3 with pymupdf, pillow, lxml, pyyaml; pandoc; LibreOffice (`soffice`) for .pptx decks and `--render`.

The markup format is documented in the skill's SKILL.md.

## Example (fictional)

`example/` holds a made-up lecture (DEMO 200, Lecture 5: first-order RC circuits) that shows every format feature. Nothing in it comes from a real course.

- `example-deck.pdf`: the 6 invented slides (slide 4 carries a purple notetaker note, which the scan removes)
- `example-notes.md`: the markup that produced the notes
- `DEMO200-lecture-5-notes.docx`: the finished Word notes
- `reference-sheet1.png`, `reference-sheet2.png`: rendered pages, 12 per image, used as the layout reference

Rebuild it:

```
python3 build_notes.py scan example/example-deck.pdf -o slides/
python3 build_notes.py build example/example-notes.md --slides slides/ -o out.docx --render render/
```
