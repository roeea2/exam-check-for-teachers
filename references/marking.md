# Marking errors on the page

## Boxes from the locator grid

`prepare_pages.py` makes `עמודים/<id>/grid-p01.png` ...: each student page with a grid in percent of the image.
Red lines and red numbers every 10% (x along the top and bottom edges, y along the left and right edges), light
blue lines every 5%, and small blue "x,y" labels at the 20/40/60/80 crossings.

For every deduction:
1. Open the grid image of that page and find the exact place: the wrong number, the wrong graph line, the line
   with the missing explanation, or the place where the missing part should be (next to its part label).
2. Read `box = [x, y, w, h]` from the grid: x and y of the top-left corner, then width and height, all in percent.
   Make the box hug the item with a small margin (1-2%). Typical sizes: a number 6-10% wide and 3-5% high, a line
   of writing 30-60% wide and 3-4% high, a whole graph 30-50% each way.
3. The label (points and reason) is drawn under the circle, aligned to the circle's right edge (or left edge for
   a circle near the left side). If that covers writing or another label, set `label_at: [x, y]` (the label's
   top-right corner) or `label_at: [x, y, "left"]` (its top-left corner) to a free spot: a margin, or empty
   grid space below the answer. A label is about 25-35% of the page wide.

Several deductions on one page: give each its own box; keep labels from overlapping by moving one with
`label_at`. A correct final answer may get an `ok` mark (green check), but do not clutter the page.

## Check the result

After `annotate.py`, render the marked PDF pages and look at every page that has marks:

```
pdftoppm -r 70 -png "<folder>/בדיקה/<name> - בדוק.pdf" <scratch>/m
```

Fix: a circle in the wrong place (re-read the grid), a label covering the student's writing or another label
(`label_at`), a label cut at the page edge. The cover page must show the same total as the stamp on page 1.

## Rotated or sideways photos

Chrome applies the photo's orientation tag, so phone photos usually come out upright. If a page is still sideways
or upside down, rotate the file itself before preparing it (macOS: `sips -r 90 file.jpg`, or 180 / 270), rerun
`prepare_pages.py --only <id> --force`, and use the new grid.
