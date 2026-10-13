# transcribe-and-create-note (builder and tools)

Builds AES-style lecture notes as a Word file: slide on the left (two-thirds width, centred), notes on the right, one page per slide appearance, in lecture order. Used by the `transcribe-and-create-note` Claude skill.

Get everything in one step (the skill does this):

```
curl -sSfL https://codeload.github.com/sarojratul/transcribe-and-create-note/tar.gz/main | tar xz -C "$S" --strip-components=1
```

```
python3 build_notes.py scan  deck.pdf -o slides/          # purple-note redaction, render + crop, map.txt, contact sheets
python3 build_notes.py build notes.md --slides slides/ -o EE321-lecture-12-notes.docx --render render/
```

What `build` does: parses the notes markup, auto-splits long pages into `(continued)` pages, converts LaTeX to native Word equations (via pandoc), writes the title page, contents, "Marked as important", the 4-column cheat sheet and an auto-generated Open questions list, then checks for em dashes, recording references, timestamps, unplaced slides, marker wording and cheat-sheet rules. A `!fig path.png` line places an image at column width (cheat-sheet design figures, or a figure in a notes column).

Needs: Python 3 with pymupdf, pillow, lxml, pyyaml; pandoc; LibreOffice (`soffice`) for .pptx decks and `--render`. The tools also need matplotlib, schemdraw, scipy, numpy.

The markup format is documented in the skill's SKILL.md.

## tools/

Reusable scripts, so a run calls them instead of rewriting them. Every script prints its usage with `-h` or in its docstring.

| Script | What it does |
|---|---|
| `cheat_figures.py` | Library of ready-made cheat-sheet design figures (circuit left, parameter plot right). `--list` shows the catalogue; `python3 tools/cheat_figures.py figs/ lrc sk butter` writes PNGs. |
| `figlib.py` | Drawing helpers behind the figures: figure size and fonts, schemdraw on matplotlib axes, parts by explicit endpoints, op-amp pin positions, s-plane axes, poles and zeros, Bode axes, block-diagram boxes, collision-free frequency labels. |
| `cheat_update.py` | Changes the cheat sheet of an existing notes .docx in place (keeps hand edits): Variables lists after equation groups, design figures under `Use when:`, new entries, extra lines. Driven by a YAML spec. |
| `cheat_dump.py` | Lists each cheat-sheet entry with paragraph kinds and equation ordinals (EQ0, EQ1, ...) for writing a `cheat_update.py` spec. |
| `cheat_common.py` | Shared reader for the cheat-sheet section (used by the two scripts above). |
| `contact_sheet.py` | Stacks PNGs into one labelled image for checking figures in a single look. |

Adding to the toolbox: when a run writes something reusable (a new figure, a helper, a checker), add it here with a docstring and a line in this table, and commit it, so the next run reuses it instead of rewriting it.
