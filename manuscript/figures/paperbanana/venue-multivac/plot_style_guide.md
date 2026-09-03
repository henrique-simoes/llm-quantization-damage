# Plot style guide — multivac / *Divergence Ranks What Benchmarks Bound*

Applies to every statistical plot in this paper. Install with:

    mkdir -p ~/.config/paperbanana/venues/multivac
    cp manuscript/figures/paperbanana/venue-multivac/* ~/.config/paperbanana/venues/multivac/
    paperbanana plot-batch --manifest manuscript/figures/paperbanana/plots.yaml --venue multivac

## Palette

Okabe–Ito only, which is safe for deuteranopia, protanopia and tritanopia:

| role | hex |
|---|---|
| UD-Q6_K_XL (reference arm) | `#000000` |
| UD-Q6_K | `#0072B2` |
| UD-Q5_K_XL | `#009E73` |
| UD-Q4_K_XL | `#D55E00` |
| KV-dtype-only control | `#CC79A7` |
| external reference band | `#F0E442` at 25 % alpha |
| withdrawn / excluded / not tested | `#767676` with a diagonal hatch |

**Colour never carries information alone.** Two of these hues are close in luminance and merge in
greyscale, so every series is also distinguished by marker shape and line style:

| arm | marker | line |
|---|---|---|
| UD-Q6_K_XL | open circle | solid |
| UD-Q6_K | filled circle | solid |
| UD-Q5_K_XL | filled square | dashed |
| UD-Q4_K_XL | filled triangle | dash-dot |
| KV-only control | filled diamond | dotted |

Evaluation domains are encoded by marker fill, not hue: prose = open, code = filled, task prompts =
half-filled.

## Form

White background. No gradients, no drop shadows, no 3-D, no chartjunk, no background grids heavier
than a hairline. Thin rules, generous internal padding, sans-serif labels. Legends inside the panel
when they fit. Figures are sized for a single column of a two-column paper unless the intent says
otherwise.

## Rules that are not negotiable

1. **Do not invent, round, reorder or omit any value present in the data file.** If a row is in the
   CSV it is in the figure, unless the intent explicitly excludes it.
2. **Do not add a trend line** unless the intent asks for one. Two figures here explicitly forbid it.
3. **Do not rescale an axis to make small error bars visible.** In several figures the error bars are
   smaller than the markers and that is the finding.
4. **Every axis label carries its unit.** Every log axis is labelled as such.
5. **Use the caption supplied in the intent verbatim.** Do not write a new one.
6. **Reproduce annotations exactly as given**, including the ones that qualify or withdraw a result.
   Several of them exist to prevent a reader drawing a conclusion the data does not support.
7. Hatch fills mark three things and nothing else: an engine-confounded arm, a modelled (not
   measured) quantity, and a failed or not-tested cell. Give each a legend entry.
