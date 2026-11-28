# Design craft: make the work look considered

"Ugly" and "cheap" usually come from broken relationships, not from missing effects. Fix the relationships first; express personality last, with one decisive design move.

Read this file when the feedback says the work looks ugly, cheap, unfinished, plain, or generic.

## 1. Diagnose in repair order

A later fix cannot rescue an earlier failure. Check in this order:

1. alignment and edges;
2. spacing and grouping;
3. type scale, weight, and line length;
4. color roles and contrast;
5. depth — borders and shadows — and shape;
6. imagery and icons;
7. one expressive design move.

If the work is not yet good at items 1–3, adding effects from 5–7 only makes it worse.

## 2. Type

- Use a small type scale: three or four sizes, two or three weights. Avoid arbitrary values.
- Set body line length at roughly 45–75 characters. Body line height around 1.5, headings around 1.2.
- Left-align long text; center only short display text.
- Establish hierarchy with weight and color before increasing size.
- Do not use faux bold or faux italic.
- For CJK text, do not set all caps and do not use negative letter spacing; use line height around 1.7–1.9, with genuine bold and italic glyphs.

## 3. Color

- Start from a neutral base, one accent color, and the success, warning, and error semantic colors.
- Reserve the accent for the primary action or the one thing that must stand out. Used everywhere, it loses its meaning.
- Body contrast should reach roughly 4.5:1; large text and interface boundaries roughly 3:1.
- Avoid pure black on pure white or pure white on pure black. Use a warmer or cooler gray that matches the tone of the work.
- State must not be carried by color alone; pair it with a text label, an icon, or a shape.
- Dark mode needs its own surface and text roles, not a mechanical inversion.

## 4. Space

- Proximity expresses grouping: spacing within a group should be smaller than spacing between groups.
- Use one spacing scale and one set of padding values, and align shared edges.
- Leave space around the focal element. Do not push content to the edges just because the viewport is wide.
- Generous space reads as composed; cramped space reads as cheap. Whitespace with no hierarchy reads as unfinished.

## 5. Depth and shape

- Choose one depth cue: a border, a background change, or a shadow. Do not use all three on every element at once.
- Shadows express elevation; keep the light direction consistent. If everything floats, nothing actually stands out.
- Keep corner radii and border widths consistent. One sharp corner can be deliberate emphasis, but there should only be one.

## 6. Imagery and icons

- Crop around the subject; do not stretch. Keep one consistent ratio or matte.
- Put captions near the image. Use a stable, subdued style for credits.
- Match icon stroke weight and size to the type. Do not use an icon to repeat what the label already says.
- An image must match what the text claims. Open the actual file and check it against the claim, the caption, and the alt text. A file loading does not make it evidence.

## 7. When the work looks plain or unfinished

Decide which case it is:

- **Hierarchy, contrast, or scale is weak.** Fix those first; the work may not need more decoration.
- **A decisive point of view is missing.** Add one clear design move drawn from the content: type treatment, a color block, image proportion, a diagram, or spatial rhythm.
- **The craft signals are missing.** Tighten alignment, spacing, and type before considering decoration.

One decisive design move beats ten small decorations. Do not mistake "more" for "more designed", and do not mistake "quiet" for "unfinished".

## 8. Completion check

- Squinting at it, the intended hierarchy is still clear.
- At actual size, there are no alignment errors, clipped text, stretched images, or inconsistent spacing.
- Contrast passes, and state is not expressed by color alone.
- Every expressive design choice relates to the current content.
- The work looks deliberately designed at real viewing size, not merely tidy in code.

## Avoid

- Adding gradients, shadows, and large corner radii to every element.
- Using too many sizes, font families, or accent colors.
- Centering long text and leaving alignment loose.
- Pure black text, stretched images, purely decorative icons.
- "Premium" effects that do no actual work.
- Adding decoration while spacing and type are still unresolved.
