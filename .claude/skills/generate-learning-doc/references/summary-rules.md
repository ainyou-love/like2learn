# Step 1 — Summary rules (Fable subagent)

Pass this whole file to the step-1 subagent. Its only job is to turn the raw script into sectioned notes; it never writes HTML.

## Input

A raw Vietnamese YouTube transcript. Lines are broken mid-sentence (auto-caption output), so rejoin fragments into sentences before reading for meaning. Ignore timestamps, `[Âm nhạc]`, `[Vỗ tay]` and similar caption tags.

## Task

Ghi lại ý tóm tắt rút gọn theo TỪNG PHẦN, đúng thứ tự tài liệu (không phải summary tổng thể).

Split the script into the parts the speaker actually uses — "thứ nhất / thứ hai…", "bí quyết số 1…", named habits, chapters, or clear topic shifts. Typically 5–10 parts; a long book chapter can have up to ~14. Keep document order. Name each part by its idea, not its position, the way earlier entries do ("Tư duy linh hoạt", "Quy tắc 1 · Chọn triết lý làm việc sâu", "Kết · Cuộc sống sâu"). A diary or timeline keeps its order, with the idea in the title, e.g. "Thứ Hai · Luôn giữ nhiều lựa chọn". A book can open with "Giới thiệu sách" (title, author, translator, publisher, if the script says them). Front matter like acknowledgements and closing ads for the app/channel count as skippable filler. Do not merge two distinct parts to hit a count, and do not split one idea to pad.

### QUY TẮC GIỮ NGỮ CẢNH (bắt buộc)

- Giữ NGUYÊN VĂN, đặt trong ngoặc kép, các loại câu sau nếu script có: câu tự nhủ / câu tuyên bố mẫu, câu hỏi tự vấn, lời nhắc dán/viết ra, trích dẫn đắt giá của tác giả (Jim Rohn...).
- Mỗi nguyên tắc / bước / nghi thức khi liệt kê phải kèm ví dụ hành động cụ thể lấy từ script (đặt báo thức xa giường, gấp sẵn áo...) — không chỉ ghi tên nguyên tắc.
- Giữ con số cụ thể: khung giờ, số phút, số trang, số ngày, %, số tiền.
- Giữ tên nhân vật + ít nhất 1 câu nói hoặc chi tiết đặc trưng của từng người; không gộp thành "các nhân vật đều...".
- CHỈ được lược bỏ: từ đệm, câu lặp lại ý, đoạn chuyển cảnh, lời kêu gọi like/share/subscribe.

### QUY TẮC VIẾT GỌN

- Rút gọn diễn đạt của từng đoạn, không thêm ý ngoài script.
- Câu mẫu nguyên văn được rút ngắn nhưng không diễn giải lại bằng lời của người tóm tắt.

Why these rules matter: the notes are the only thing the HTML step sees. A quote paraphrased here, a number dropped, or a character flattened into "mọi người" is lost for good — step 2 is forbidden from going back to the script to recover it.

Shortening a verbatim quote means cutting words out of it (optionally with `…`), never rewording it. If transcript noise garbles a quote, fix only obvious caption errors (split words, missing diacritics on a clear word) and keep the rest.

Auto-captions often mangle foreign names and units (a person's name heard as random English words, "đồng là" for "đô la"). When the source context you're given (book/video title, author) makes the real name or unit certain, write the corrected form. When it isn't certain, keep what was heard rather than guessing: a wrong "correction" looks trustworthy and can't be caught later. At the end of the notes, list every correction under `## Sửa lỗi phiên âm` as `nghe: "…" → sửa: "…"` so the orchestrator can check it.

Use straight double quotes `"…"` for every verbatim phrase so step 2 can detect and wrap them.

## Output format

Write a Markdown file to the path you are given, exactly in this shape:

```markdown
# <Tiêu đề ngắn của bài, 3–8 từ, lấy từ chủ đề script>

- Nguồn: <kênh / tác giả / sách được nhắc trong script, hoặc "YouTube" nếu không rõ>
- Tóm lược: <1–2 câu nêu chủ đề chung của cả bài, không thêm ý ngoài script>

## Phần 1 — <tên phần>

- <ý rút gọn, kèm ví dụ/con số/câu nguyên văn trong "…">
- <…>
- Bài học: <kết luận của chính phần này nếu script có nói; bỏ dòng nếu không>

## Phần 2 — <tên phần>
...
```

Each part: 3–7 bullets. Prefix the conclusion bullet with `Bài học:` or `Nguyên tắc:` only when the speaker states one for that part.

When done, reply with just: the output path, the number of parts, and each part's title on its own line.
