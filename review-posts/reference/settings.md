# settings.json

Lives in the business folder. Only `business_name` is required; everything else has a sensible default.

```json
{
  "business_name": "Brightway Dental",
  "website": "https://example.com",
  "review_links": [
    { "name": "Google", "url": "https://www.google.com/maps/place/..." },
    { "name": "Yelp", "url": "https://www.yelp.com/biz/..." }
  ],
  "only_stars": 5,
  "template": "auto",
  "carousel": "long-only",
  "short_quote_words": 32,
  "carousel_min_words": 70,
  "colors": { "dark": "#0f4c5c", "darker": "#08303a", "accent": "#e86a4f", "accent_light": "#f39a84" },
  "fonts": { "head": "Montserrat[wght].ttf", "body": "Montserrat[wght].ttf", "label": "Montserrat[wght].ttf" },
  "logo": "logo.png",
  "logo_style": "white",
  "photos_folder": "photos",
  "photo_focus": { "job-03.jpg": "50% 20%" },
  "bubble_title": "Client Review",
  "caption": { "extras": "Book online: example.com", "hashtags": ["#YourTown", "#SmallBusiness"] }
}
```

| Key | What it does |
|---|---|
| `template` | `auto` (short reviews get `hero`, longer ones get `bubble`), `hero` (big quote on a photo), `bubble` (review card on a photo), or `solid` (brand color, no photo) |
| `carousel` | `long-only` (reviews over `carousel_min_words` become 2 slides), `always`, or `off` |
| `colors.dark` / `darker` | The background shade behind white text. Must be dark. |
| `colors.accent` / `accent_light` | Stars, highlighted phrase, lines and labels |
| `fonts` | Roles: `head` (quote), `head_italic` (highlight), `body`, `body_bold`, `body_light`, `label` (small capitals). Put the files in `fonts/`. A missing role falls back to a related one; with no `fonts` at all, the bundled Playfair Display, Poppins and Raleway are used. Variable fonts (`Name[wght].ttf`) work. |
| `logo_style` | `white` (an all-white version, which is safest on photos) or `original` (full color; only if the logo reads well on dark) |
| `photo_focus` | Per photo: which part to keep when cropping to 4:5, as `"x% y%"`. `"50% 20%"` keeps the top. |
| `bubble_title` | Big words under the review card: "Client Review", "Patient Review", "Guest Review" |
| `only_stars` | 5 by default. Set it to 4 to also use 4-star reviews (only if the person asks). |
