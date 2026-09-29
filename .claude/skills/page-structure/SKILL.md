---
name: page-structure
description: The layout contract for the like2learn site — where a page file goes under resources/, how it must be named, where its images live, and how it gets registered in resources/post_metadata.json so the index, reader and gallery can find it. Use this whenever you add, move, rename or delete anything under resources/ — a post, a book chapter, a report, a lead image, a gallery album — or whenever you are about to run _tools/sync_post_metadata.py, assign a category, or give a post a feature image. Also use it when a page exists but is not showing up on the index, shows the wrong title or date, has no description under its link, or when an image 404s in the reader or appears in the wrong album. The post-creating skills (generate-learning-doc, tech-doc-report, gen-tech-doc-html, skill-study-doc) all hand off here for the filing and registration step rather than restating it. Not for writing a page's content or styling it — this covers where it lives and how the site learns about it.
---

# Page structure

Everything the site shows is a static file under `resources/`. There is no database and no
front matter on these pages: the index, the reader and the gallery are built by scanning that
directory and joining it against one JSON file. That is why filing a page correctly *is* the
publishing step — a page in the wrong place is invisible, and a page with the wrong name gets
the wrong label.

Two things decide whether a page works:

1. **Where the file sits**, which decides its URL, its breadcrumb and its album.
2. **Its entry in `resources/post_metadata.json`**, which decides its title, blurb, date,
   topic filter and lead image.

The first you get by putting the file in the right place. The second you get by running
`_tools/sync_post_metadata.py`.

## Where a page goes

`resources/` has four homes, and which one you pick is not cosmetic — the folder names become
the breadcrumb the reader shows above the page.

| Home | Shape | For |
|---|---|---|
| `resources/Custom-Post/` | `NN-slug.html` (`07-xay-dung-he-thong.html`) | Standalone numbered posts. The number orders them and shows up in the label. |
| `resources/topics/<topic>/` | `slug.html` (`nguoi-va-ai-agent.html`) | Topic posts. Nest further when a topic earns it — `topics/ai/claude/` exists. |
| `resources/topics/tech-reports/` | `YY-MM-DD--<area>--<from>_<to>.html` | Periodic reports, where the window is part of the identity. |
| `resources/ebooks/<Author>/<Book>/` | `NN-chuong-NN-slug.html` | Book chapters, numbered so they read in order. |

Slugs are lowercase, ASCII, hyphen-separated — no spaces, no diacritics. Vietnamese titles get
transliterated (`Kỷ luật của bình minh` → `ky-luat-cua-binh-minh`). This matters because the
filename is the fallback label: `resourceFileLabel` in `_includes/resource-tree.html` turns
`05-ky-luat-cua-binh-minh.html` into `05 — ky luat cua binh minh` when metadata is missing, and
underscores or diacritics make that fallback read badly.

The `NN-` prefix is meaningful only where the table says so. Adding one to a topic post buys
nothing and puts a stray number in the label.

## What the page's `<head>` must carry

The sync tool reads only the `<head>`, in small chunks, and never loads the body. Two tags are
mandatory, because they *are* the index entry:

```html
<title>Con đã về đất mẹ · Apollo 13 và phương pháp tư duy</title>
<meta name="description" content="Câu chuyện Apollo 13 và năm phương pháp tư duy: ...">
```

Both are re-read on every sync, so they live in the page, not in the JSON. If a title or blurb
is wrong on the index, fix the page and re-run — editing the JSON by hand is undone on the next
run. A `WARN ... no <title> or <meta name="description">` means one is missing.

Notebook pages are the one special case: a `Sổ ghi chép · No.NN — ` prefix (or a
` — Sổ ghi chép` suffix) is stripped from the title before it is stored, so the index shows the
subject rather than the series label.

## Images

There are two kinds of image in this repo and they are not interchangeable. Putting one in the
other's place is the most common mistake here.

**Gallery images** live in `resources/galleries/<album>/<image>`, and that depth is exact —
`_includes/gallery.html` only collects files exactly two levels below `galleries/`, so an image
in a sub-folder silently never appears. Every image in an album shows up in that album; the
first one becomes its cover. Supported: `.jpg`, `.jpeg`, `.png`, `.webp`, `.gif`.

**A post's lead image** (`feature_img`) belongs beside the post, named after it — same basename,
`.webp` instead of `.html`:

```
resources/topics/others/apollo13-con-da-ve-dat-me.html
resources/topics/others/apollo13-con-da-ve-dat-me.webp
```

Keeping it next to the post is what stops a lead image from being mistaken for gallery content
and turning up as a stray tile in an album. The pairing also makes it obvious at a glance which
image belongs to which page, and the sync tool warns if the file goes missing.

Convert before committing — these are read on phones, and a full-size PNG export is routinely
8x heavier than it needs to be:

```bash
cwebp -q 80 <source-image> -o resources/<post path without .html>.webp
```

Reuse an image that is already in an album rather than copying it around; point `feature_img`
at a converted copy beside the post and leave the album's original alone.

## Register it

After the file is in place, one run records it:

```bash
python3 _tools/sync_post_metadata.py
```

It walks `resources/**/*.html`, refreshes every title and description, keeps `created_at` (a new
page takes the date git first saw it, or its mtime if uncommitted), and drops entries whose file
is gone. It prints what it added, updated or removed — a rename shows up as one added and one
removed, which is your cue that the old URL is dead.

Then give the page the two things the tool cannot infer.

**A category** — exactly one, and the index's filter row is built from these, so reuse an
existing one unless nothing fits. The run prints the categories in use with their counts:

```bash
python3 _tools/sync_post_metadata.py --set-category "<path under resources/>" "<category>"
```

In use today: `Phát triển bản thân`, `AI & Claude Code`, `Kinh doanh & Đàm phán`,
`Tài chính & Giàu có`, `Tư duy giải quyết vấn đề`, `Báo cáo công nghệ`. A book's chapters all
take the book's category.

**A lead image**, when there is one — optional, and most posts have none:

```bash
python3 _tools/sync_post_metadata.py --set-feature-img "<path under resources/>" "<image path under resources/>"
python3 _tools/sync_post_metadata.py --set-feature-img "<path under resources/>" ""   # clear it
```

Both paths are relative to `resources/`, the same shape as the JSON's keys. The tool refuses a
path that does not point at a real file, and warns on later runs if the image disappears.

Categories and lead images are assigned by hand and carried across runs — the tool never guesses
them and never clears them.

## Turning lead images off

`resources/post_metadata.json` holds settings at its top level alongside the post entries. Any
key that does not end in `.html` is a setting and is preserved across runs:

```json
{
  "feature_image_enabled": true,
  "topics/others/apollo13-con-da-ve-dat-me.html": { ... }
}
```

Set `feature_image_enabled` to `false` to stop the reader showing any lead image site-wide
without clearing a single `feature_img` value — useful for judging whether they earn their
space.

## How the site reads all this

Worth knowing, because it explains why the conventions are shaped the way they are:

- **`index.html`** offers the same posts three ways — newest-first, by topic, and as the folder
  tree — plus the category filter row. All three are driven by the metadata, so a post with no
  entry appears with a bare filename and no blurb.
- **`read.html`** is a shell: a breadcrumb bar built from the folder path, the lead image if
  there is one, and the page itself in an iframe. The page keeps its own styling and scrolling,
  which is why pages here are self-contained rather than sharing a layout.
- **`gallery-preview.html`** renders one album as a slideshow.

## Before you call it done

- The file is in the right home, with the right name shape for that home.
- Its `<head>` has a real `<title>` and a real one-sentence `<meta name="description">`.
- A lead image, if any, sits beside the post as `.webp` and is pointed at by `feature_img`.
- `python3 _tools/sync_post_metadata.py` runs clean — no `WARN` lines for this page.
- It has exactly one category.
- New image and page files are staged. An untracked lead image deploys as no image at all: the
  reader removes the band when it fails to load, so nothing visibly breaks and nobody notices.
