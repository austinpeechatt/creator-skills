# Headshots

Drop your own headshot photos in this folder. The skill picks one and passes it
to the image model as a likeness reference.

The original author's photos are deliberately **not** included in this repo.

## What works

- Well lit, face clearly visible, shot straight on or at a slight angle
- Higher resolution is better — 1500x1500 or above noticeably improves likeness
- A few variants (casual, blazer, different expressions) so you can match the
  tone of a given video

## The honest limitation

Image models still do not nail a specific person's face. Treat the generated
face as a **layout placeholder** and composite your real photo in afterwards
(Canva, Figma, Photoshop). Judge these renders on composition, type and colour
— not on whether the face is a perfect match.

One thing that measurably helps: keep the person description in your prompt
SHORT. One or two sentences. Long descriptions of facial features push the
model toward a stylised, generic face.
