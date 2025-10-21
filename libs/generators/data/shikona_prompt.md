You are given a Sumo **shikona** (ring name) in Japanese script to process. You may also be given:
- A **parent shikona** to create a lineage-related name
- A **shusshin** (origin/birthplace) to incorporate cultural/geographic themes
- Both parent and shusshin for multi-layered naming

## Input formats

### Standard generation (no context)
```
豊昇龍
```

### With parent shikona (lineage)
```
GENERATED: 太郎山
PARENT: 豊昇龍
```

### With shusshin (origin)
```
GENERATED: 海斗
SHUSSHIN: Mongolia
```

### With both parent and shusshin
```
GENERATED: 力山
PARENT: 白鵬
SHUSSHIN: Aomori
```

## Your task

Return **only** a JSON object with exactly these fields:

- `"shikona"`: the processed shikona (see modification rules below)
- `"transliteration"`: the shikona in **romaji**, ASCII lowercase, no spaces, no hyphens, no macrons/diacritics
- `"interpretation"`: a very short 1-5 word English gloss that captures the name's sense/feel

Do not include any extra fields, comments, or text outside the JSON.

## Modification rules (when PARENT is provided)

When a PARENT shikona is provided, you **may** modify the GENERATED name to create a relationship to the PARENT, following authentic sumo naming traditions:

### Sumo naming traditions:
- **Heya (stable) lineage**: Wrestlers from the same stable often share 1-2 kanji (e.g., 琴欧洲, 琴奨菊, 琴光喜 from Sadogatake stable - all share 琴)
- **Oyakata (coach) references**: Wrestlers may adopt characters from their coach's name as tribute
- **Thematic connections**: Names sharing similar meanings/themes (mountains, dragons, strength, nature)
- **Phonetic echoes**: Similar sounds without identical kanji
- **Note**: Not all wrestlers in a stable share characters - variety is authentic!

### Relationship strength: **FLEXIBLE**
- You can choose to share 1-2 kanji characters with the parent
- You can choose to share only thematic elements (both dragon-themed, both mountain-themed)
- You can choose to use phonetic similarity
- You can also choose to keep the GENERATED name unchanged if it's already good
- Variety is important - don't always use the same approach
- The relationship can range from obvious to subtle to non-existent

### Modification approach (if you choose to modify):
1. Examine the GENERATED name and PARENT name
2. Decide whether to modify or keep the generated name
3. If modifying, choose ONE approach: character sharing, thematic connection, or phonetic echo
4. Swap/adjust 1-3 kanji to create the connection
5. Ensure the result is still a realistic shikona (2-5 kanji, authentic sound/structure)
6. Ensure it differs from the PARENT (don't just copy characters)

### Examples of modifications:

**Example 1: Character sharing**
```
GENERATED: 太郎山
PARENT: 豊昇龍
→ Modified: 太昇龍 (share 昇龍, but different first character)
```

**Example 2: Thematic connection**
```
GENERATED: 勝利花
PARENT: 白鵬
→ Modified: 黒鵬 (both bird-themed: white phoenix → black phoenix)
```

**Example 3: Phonetic echo**
```
GENERATED: 海斗
PARENT: 貴ノ花
→ Modified: 貴海斗 (adds 貴 for phonetic/visual connection to Takano-hana lineage)
```

When **no PARENT** is provided, proceed to check for SHUSSHIN.

## Modification rules (when SHUSSHIN is provided)

When a SHUSSHIN (origin/birthplace) is provided, you **may** modify the GENERATED name to incorporate **cultural, geographic, or thematic elements** associated with that place.

### Influence strength: **FLEXIBLE**
- You can choose to incorporate cultural/geographic themes from the region
- You can choose to keep the GENERATED name unchanged if it's already good
- If you do incorporate origin themes, avoid using the place name directly (e.g., don't just add "Mongolia")
- Instead, use cultural imagery, natural features, or traditional concepts from that area
- The connection can range from obvious to subtle to non-existent
- Not all wrestlers' names reflect their origin - variety is authentic!

### Regional theme examples:

**Mongolia**: Steppe, horses, eagles, nomadic warriors, sky, vast plains, strength, freedom
- Kanji suggestions: 蒼 (blue/vast), 翔 (soaring), 鷹 (hawk), 馬 (horse), 原 (plains)

**Bulgaria/Eastern Europe**: Mountains, roses, strength, ancient warriors, balkans
- Kanji suggestions: 峰 (peak), 剛 (strong), 花 (flower), 岳 (mountain)

**United States**: Freedom, power, eagles, stars, greatness, modern strength
- Kanji suggestions: 星 (star), 鷲 (eagle), 力 (power), 豪 (magnificent)

**Tokyo (Japan)**: Capital, prosperity, urban, cherry blossoms, imperial
- Kanji suggestions: 京 (capital), 桜 (cherry), 栄 (prosperity), 都 (metropolis)

**Aomori (Japan)**: Northern Japan, apples, snow, festivals, traditional
- Kanji suggestions: 雪 (snow), 北 (north), 林 (forest), 祭 (festival)

**Osaka (Japan)**: Commerce, energy, tigers (baseball), urban vitality
- Kanji suggestions: 虎 (tiger), 豪 (vigorous), 商 (commerce), 浪 (wave)

### Modification approach with shusshin (if you choose to modify):
1. Examine the GENERATED name and identify the SHUSSHIN
2. Decide whether to modify or keep the generated name
3. If modifying, select 1-2 culturally/geographically appropriate kanji from the theme list
4. Swap 1-2 kanji in the GENERATED name
5. Ensure the result still sounds like an authentic shikona

### Examples of shusshin modifications:

**Example 1: Mongolia origin**
```
GENERATED: 太郎山
SHUSSHIN: Mongolia
→ Modified: 蒼鷹山 (blue hawk mountain - evokes Mongolian steppe and raptors)
```

**Example 2: Aomori origin**
```
GENERATED: 海斗
SHUSSHIN: Aomori
→ Modified: 雪海 (snow sea - northern maritime theme)
```

**Example 3: Bulgaria origin**
```
GENERATED: 勝利
SHUSSHIN: Bulgaria
→ Modified: 剛山 (strong mountain - Balkan mountain strength)
```

### When BOTH parent and shusshin are provided:
You have complete flexibility to decide how to handle this:
- You can prioritize the parent connection and ignore the shusshin
- You can prioritize the shusshin and ignore the parent
- You can incorporate both influences if it feels natural
- You can keep the GENERATED name unchanged
- Choose what creates the most authentic and natural-sounding shikona

**Example: Both parent and shusshin (one possible approach)**
```
GENERATED: 力山
PARENT: 白鵬
SHUSSHIN: Tokyo
→ Modified: 白桜 (white cherry - shares 白 with parent, adds 桜 for Tokyo)
```

**Alternative: Both parent and shusshin (another approach)**
```
GENERATED: 力山
PARENT: 白鵬
SHUSSHIN: Tokyo
→ Keep: 力山 (already a good shikona, no modification needed)
```

When **no PARENT or SHUSSHIN** is provided, return the input unchanged.

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

If a shikona is known to belong to an existing rikishi, use the **official/most widely accepted** reading. When uncertain, choose the most likely conventional shikona reading.

## INTERPRETATION RULES (1-5 words)

- Produce a tiny, evocative gloss in plain ASCII lowercase.
- 1 to 5 words, single spaces only, no punctuation.
- Base meaning on kanji components and shikona conventions (place names, auspicious terms).
- If a kanji has multiple senses in shikona, choose the most conventional/evocative one.
- This is a gloss, not a strict translation.

## Example

**Input**

```
豊昇龍
```

**Output**

```json
{
  "shikona": "豊昇龍",
  "transliteration": "hoshoryu",
  "interpretation": "rising dragon"
}
```
