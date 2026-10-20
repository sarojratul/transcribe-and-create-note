# transcribe-and-create-note (builder and tools)

Builds AES-style lecture notes as a Word file, for any course: slide on the left (two-thirds width, centred), notes on the right, one page per slide appearance, in lecture order. Used by the `transcribe-and-create-note` Claude skill.

Get everything in one step (the skill does this):

```
curl -sSfL https://codeload.github.com/sarojratul/transcribe-and-create-note/tar.gz/main | tar xz -C "$S" --strip-components=1
```

```
python3 build_notes.py scan  deck.pdf -o slides/          # purple-note redaction, render + crop, map.txt, contact sheets
python3 build_notes.py build notes.md --slides slides/ -o EE321-lecture-12-notes.docx --render render/
```

What `build` does: parses the notes markup, auto-splits long pages into `(continued)` pages, converts LaTeX to native Word equations (via pandoc), writes the title page, contents, "Marked as important", the 4-column cheat sheet and an auto-generated Open questions list, then checks for em dashes, recording references, timestamps, unplaced slides, marker wording and cheat-sheet rules. A `!fig path.png` line places an image at column width (cheat-sheet design figures, or a figure in a notes column). Cheat-sheet entries named `Common traps ...` or `Definitions` need no `Use when:` line.

Needs: Python 3 with pymupdf, pillow, lxml, pyyaml; pandoc; LibreOffice (`soffice`) for .pptx decks and `--render`. The tools also need matplotlib, schemdraw, scipy, numpy.

The markup format is documented in the skill's SKILL.md.

## tools/

Reusable scripts, so a run calls them instead of rewriting them. Every script prints its usage with `-h` or in its docstring.

| Script | What it does |
|---|---|
| `slide_crop.py` | Cut a figure out of a scanned slide (`slides/cN.png`): `grid` overlays coordinates, `crop --box` cuts it, `--blank`/`--label` replace example values with symbols, `--strip-ink` whitens coloured handwritten ink and highlighter while keeping black line art, `pair` joins a crop and a plot side by side. First choice for any figure from a new lecture, in any course. |
| `cheat_figures.py` | Library of ready-made figures, split by subject in `figsets/` (`analog_circuits`, `dc_machines`, `magnetic_circuits`, `ac_power`, `electromagnetics`, `microprocessors`). `--list` shows the catalogue; `python3 tools/cheat_figures.py figs/ lrc sk` writes PNGs; `--plot-only` keeps just the plot panel to pair with a slide crop. |
| `figsets/<subject>.py` | One module per subject area. A new course with no fitting figures gets a new module. `analog_circuits` now also has filter design-from-spec masks (`designspec`, `designspec_cheb`, `designspec_ex`), three-output biquad plot (`biquad3_plot`) a simulated-inductor impedance plot (`zind_plot`), Schmitt trigger with hysteresis loop (`schmitt`), inverting summer and difference amp (`opsum`), log and antilog amps (`logamp`). |
| `figlib.py` | Drawing helpers and the figure registry: figure size and fonts, schemdraw on matplotlib axes, parts by explicit endpoints, s-plane and Bode axes, block-diagram boxes, collision-free labels. |
| `cheat_update.py` | Changes the cheat sheet of an existing notes .docx in place (keeps hand edits): Variables lists after equation groups, figures under `Use when:`, new entries, extra lines. Driven by a YAML spec (`example_spec.yaml`). |
| `cheat_dump.py` | Lists each cheat-sheet entry with paragraph kinds and equation ordinals (EQ0, EQ1, ...) for writing a `cheat_update.py` spec. |
| `cheat_common.py` | Shared reader for the cheat-sheet section (used by the two scripts above). |
| `cs4_post.py` | Post-processor for the standalone 4-column exam cheat sheet (`cheatsheet-generator` skill, any course): pandoc docx -> house style (landscape, 4 columns, coloured native equations, `NEWX` = added in green, section font sizes). |
| `cs4_edit.py` | Edits an existing 4-column cheat sheet in place: `dump` blocks, `append` formulas/variables to a block, `addblock` a new topic block, `figs` (YAML plan, true-size pictures under a Figures label), `cut` blocks (exam-scope copies), `legend` line, `notes` (YAML plan: per-topic Steps numbered list and Traps bullets after Variables), `render` (LibreOffice preview + PNGs). |
| `figsets/dc_machines.py` | DC machine figures: 5 field connections as generator and motor (parts, nodes, current arrows, KCL/KVL line), plugging, Ward-Leonard, OCC/critical R, external characteristics, power flow, efficiency, motor characteristics, commutation, cross-section with GNA/MNA, universal-motor phasor. |
| `figsets/magnetic_circuits.py`, `figsets/ac_power.py` | Core with gap + reluctance equivalent + toroid geometry, Fleming's rules; power triangle + star/delta. |
| `figsets/electromagnetics.py` | Electromagnetics (Hayt and Buck, EE 301): RCS-CCS and RCS-SCS point figures with unit vectors at P, and RCS/CCS/SCS differential volume elements with edge lengths, face normals, dS on each face and dv; drawn with a true orthographic projection helper (`View`) so labels stay put. |
| `figsets/microprocessors.py` | Microprocessor and ARM assembly (CME 331): `number_wheel4` (4-bit number wheel with bit patterns, unsigned and signed values, C wrap at 1111/0000 and V wrap at 0111/1000, add = clockwise) and `stack_push3` (stack before and after `PUSH {Ra,Rb,Rc}`: SP drops 4k, lowest register at the lowest address, POP refills in the same order). |
| `contact_sheet.py` | Stacks PNGs into one labelled image for checking figures in a single look. |
| `abbr_tips.py` | Adds abbreviation hover tips (Word ScreenTips) to a finished notes .docx without changing how text looks: `python3 tools/abbr_tips.py IN.docx DICT.json OUT.docx [--dry]`. DICT maps whole-word keys to "Full name: purpose." tips; skips headings, contents, Open questions, red markers, equations and existing links; verifies paragraph text is unchanged. |

Adding to the toolbox: when a run writes something reusable (a new figure, a helper, a checker), add it here with a docstring and a line in this table, and commit it straight to `main` at the end of the run, so the next run downloads it instead of rewriting it.
