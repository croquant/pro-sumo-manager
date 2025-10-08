You are given a JSON array of Sumo **shikona** (ring names) in Japanese script, e.g.:

```json
["豊昇龍", "都留樹富士", "一山本"]
```

## Your task

Return **only** a JSON array of objects where each object has:

- `"shikona"`: the original input string, unchanged
- `"transliteration"`: the shikona in **romaji**, ASCII lowercase, no spaces, no hyphens, no macrons/diacritics
- "interpretation": a very short 1–5 word English gloss that captures the name’s sense/feel

Preserve input order. Do not add, drop, or reorder items. Do not include any extra fields, comments, or text outside the JSON.

## Romanization rules (for shikona)

Use name readings actually used in sumo whenever known; otherwise infer the most likely shikona reading using standard conventions.

1. Base: Hepburn-style syllables (`shi`, `chi`, `tsu`, `fu`, `ryu`, etc.), but **ASCII only** (no macrons).
2. Long vowels (e.g., ō/ū) → **collapse to single vowel**: `ō → o`, `ū → u` (e.g., `Hōshōryū` → `hoshoryu`).
3. Sokuon (small っ) → **double the following consonant** (e.g., 〜っぽ → `ppo`).
4. `ん` → always `n` (do **not** change to `m` before b/p/m).
5. Particles/formatting used in shikona:

   - `ノ` or `乃` → `no` (e.g., `貴ノ花` → `takanohana`).

6. Common shikona morphemes (guidance, not exhaustive):

   - 富士 → `fuji`
   - 山 → `yama`
   - 海 → `umi`
   - 竜/龍 → `ryu`
   - 旭 → `asahi`
   - 朝 → `asa`
   - 若 → `waka`
   - 琴 → `koto`
   - 豪 → `go`
   - 千代 → `chiyo`
   - 玉 → `tama`
   - 鶴 → `tsuru`
   - 都留 (place-name reading) → `tsuru`

7. Apply **rendaku** where natural for shikona compounds (e.g., `k` → `g`, `t` → `d`, `h` → `b/p`) when that yields established/most natural shikona readings (e.g., `都留樹富士` → `tsurugifuji`).

If a shikona is known to belong to an existing rikishi, use the **official/most widely accepted** reading. When uncertain, choose the most likely conventional shikona reading; do not leave blanks.

## INTERPRETATION RULES (1–5 words)

- Produce a tiny, evocative gloss in plain ASCII lowercase.
- 1 to 5 words, single spaces only, no punctuation.
- Base meaning on kanji components and shikona conventions (place names, auspicious terms).
- If a kanji has multiple senses in shikona, choose the most conventional/evocative one.
- This is a gloss, not a strict translation.

Validate mentally before responding. If any input item is not a string, skip it (do not insert placeholders), but keep the order of the rest.

## Example

**Input**

```json
["豊昇龍", "都留樹富士", "一山本"]
```

**Output**

```json
[
  {
    "shikona": "豊昇龍",
    "transliteration": "hoshoryu",
    "interpretation": "rising dragon"
  },
  {
    "shikona": "都留樹富士",
    "transliteration": "tsurugifuji",
    "interpretation": "rooted fuji strength"
  },
  {
    "shikona": "一山本",
    "transliteration": "ichiyamamoto",
    "interpretation": "one mountain base"
  }
]
```
