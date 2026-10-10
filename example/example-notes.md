---
course: DEMO 200
title: Introduction to Circuit Analysis (fictional example)
lecture: 5
date: January 15, 2026
footer: DEMO 200 · Lecture 5 (Jan 15)
topics: series RC circuit, first-order differential equation, time constant, step response, discharging, RC vs RL comparison.
sources:
  - example-deck.pdf | Slides 1 to 6 | Slide images, slide text, notation
howto:
  - "Ink: red marks the professor's emphasis (the boxed equation on slide 2); green on slide 3 is part of the slide."
---

## Slide 1: First-order RC circuits
**What it is:** Start of the unit on circuits with one energy-storage element. Today: the series RC circuit.

### Announcements
- **Assignment 3** is due next Friday. It covers today's material.
- Office hours move to Thursday this week.

- Objectives read from the slide: write the circuit's differential equation, find the time constant and step response, sketch charging and discharging.
- The professor said the whole unit builds on **one equation**, so it is worth getting comfortable with it today.
- Reading on the slide is reference only; it was not discussed.

## Slide 2: Series RC circuit
**What it is:** A source, a resistor and a capacitor in one loop. Applying KVL gives a first-order differential equation.
- Walk around the loop with **KVL**: the source voltage equals the resistor drop plus the capacitor voltage.
$$V_s=Ri+v_C$$
- The capacitor current depends on how fast its voltage changes:
$$i=C\frac{dv_C}{dt}$$
defs: $V_s$ = source voltage (V); $R$ = resistance (Ω); $C$ = capacitance (F); $v_C$ = capacitor voltage (V); $i$ = loop current (A)
- Substitute $i$ into the KVL equation:
$$RC\frac{dv_C}{dt}+v_C=V_s$$
- The professor boxed this in red and called it "the equation for the whole unit". It is **first order** because only the first derivative appears.
!! WILL BE ON EXAM: Deriving the RC differential equation from KVL. Professor: "You will write this on the midterm, guaranteed." Boxed in red on the slide.
- Class question: why not just use Ohm's law on the capacitor? Answer given: a capacitor has no resistance value; its current depends on the **rate of change** of voltage, not the voltage itself.
!watch Keep the passive sign convention: current entering the + terminal of the capacitor. A flipped sign gives a growing exponential, which is not physical.

## Slide 3: Time constant and step response
**What it is:** Solving the equation for a step input from an uncharged capacitor.
- Define the **time constant** $\tau=RC$ (units: Ω·F = seconds).
$$v_C(t)=V_s\left(1-e^{-t/\tau}\right),\ t\geq0$$
- Valid only when the capacitor **starts uncharged** and the source switches on at $t=0$.
- The slide asks what fraction of $V_s$ is reached at $t=\tau$. **Answer given in class:** $1-e^{-1}\approx0.632$, so about **63%**.
- The professor stressed reading the graph in units of $\tau$, not seconds: the curve always has the same shape.
!slide The green dashed line marks $t=\tau$; the curve is plotted against $t/\tau$, so it fits any RC circuit.
!! REPEATED 3 TIMES: 63% at one time constant. Said here, again when slide 3 came back, and in the end-of-class recap.
!red UNCLEAR IN LECTURE: ONE EXAMPLE VALUE FOR $R$ COULD NOT BE MADE OUT. AI NOTETAKER'S BEST GUESS: 10 kΩ, SINCE THE RESULT GIVEN WAS $\tau=1$ ms WITH $C=100$ nF.

## Slide 4: Discharging
- With the source removed at $t=0$ and the capacitor starting at $V_0$, the voltage decays:
$$v_C(t)=V_0e^{-t/\tau}$$
- **Why $5\tau$:** the professor showed that $e^{-5}\approx0.0067$, so less than 1% of the starting voltage is left. Engineers treat that as fully discharged. After $3\tau$ about 5% is still left, which is not small enough.
- **Energy stored** in the capacitor: $W=\frac{1}{2}CV^2$ (joules). The professor called it "the same form as kinetic energy".
!red SLIDE AND LECTURE DISAGREE: "AFTER $4\tau$" WAS SAID ONCE; THE SLIDE AND THE REST OF CLASS USE $5\tau$. THESE NOTES FOLLOW THE SLIDE.

## Slide 3: Time constant and step response (back to it)
- The professor went back to slide 3 to compare charging and discharging side by side: charging rises to 63% in one $\tau$; discharging falls to 37% in one $\tau$.
- Both curves are "mirror images" with the same time constant.

### Topic wrap-up: RC step response
**Recognize it:** "find $v_C(t)$", "how long until the capacitor is charged?", a switch closing on an RC circuit at $t=0$.
1. Check the initial capacitor voltage (zero, or $V_0$).
2. Find $\tau=RC$ using the resistance seen by the capacitor.
3. Write $v_C(t)=V_{final}+(V_{initial}-V_{final})e^{-t/\tau}$.
4. Substitute the time asked for, or solve for $t$.
**Check:** $\tau$ comes out in seconds; $v_C$ starts at the initial value and settles at the final value.
**Example (constructed):** $R=10$ kΩ, $C=100$ nF, $V_s=5$ V, uncharged: $\tau=1$ ms, and at $t=2$ ms, $v_C=5(1-e^{-2})\approx4.32$ V.

```
  Capacitor charged at t=0?
            |
      +-----+------+
     no           yes
      |            |
 Charging:     Source still
 Vs(1-e^-t/T)  connected?
               no: V0 e^-t/T
```

## Slide 5: RC vs RL summary
**What it is:** Side-by-side comparison of the two first-order circuits.
- Same equation shape for both; only the time constant and the state variable change.
- The quantity that **cannot jump** is the one that stores energy: capacitor voltage, inductor current.
- RL details come next class; the professor said only the time constant $L/R$ is needed today.

## Wide: Slide 5 (continued)
| Property | RC circuit | RL circuit | Why it matters |
|---|---|---|---|
| Time constant | $\tau=RC$ | $\tau=L/R$ | Sets the speed of the response |
| State variable | $v_C$ | $i_L$ | Continuous at the switching instant |
| Energy stored | $\frac{1}{2}CV^2$ | $\frac{1}{2}LI^2$ | Explains why it cannot jump |
| Long-time behaviour | Open circuit | Short circuit | Use for final values |

## Slide 6: Think-pair-share
### Think-pair-share
**Focus:** *Why a camera flash needs a few seconds between shots*
- **Small-group discussion:** pairs pointed out that the flash capacitor charges through a resistance from a small battery, so the charging current is limited.
- **Whole-class discussion:** the class linked the wait to $\tau$: the flash is ready after a few time constants. A large capacitor gives a bright flash but a long $\tau$.
**Kept coming back to:** the trade-off between flash brightness (large $C$) and waiting time (large $RC$).

## Box "Video: Capacitor charging demo": Video shown in class
### Video
**Focus:** *Video: "Capacitor charging demo", an oscilloscope trace of an RC circuit*
- The trace showed the charging curve rising quickly, then levelling off, matching slide 3.
- Changing $R$ on the bench stretched the curve in time without changing its shape.

# Marked as important
| Item | Why flagged | Slide |
|---|---|---|
| Derive $RC\,dv_C/dt+v_C=V_s$ from KVL | Professor: "on the midterm, guaranteed" + boxed in red on the slide (both sources) | Slide 2 |
| 63% of the final value at $t=\tau$ | Repeated three times in class and marked on the slide's graph (both sources) | Slide 3 |

# Cheat sheet, copy-ready

## First-order RC circuit
Use when: "find $v_C(t)$", "time constant", a switch opens or closes on an RC circuit
$$RC\frac{dv_C}{dt}+v_C=V_s$$
$$\tau=RC$$
$$v_C(t)=V_f+(V_i-V_f)e^{-t/\tau}$$
Valid for $t\geq0$ after one switching event; $V_i$ = value just before, $V_f$ = long-time value.
- At $t=\tau$: 63% of the change done; at $5\tau$: over 99%.
Solve: initial value, final value (capacitor = open circuit), $\tau$ from the resistance seen by $C$, then substitute.
Trap: use the resistance seen by the capacitor, not the total circuit resistance.

## RL comparison
Use when: an inductor instead of a capacitor, "current cannot change instantly"
$$\tau=L/R$$
- State variable $i_L$; long-time inductor = short circuit.
Trap: $\tau=L/R$, not $LR$.

## Common traps (all topics)
- Capacitor voltage and inductor current cannot jump; the other quantities can.
- Read graphs in units of $\tau$.
