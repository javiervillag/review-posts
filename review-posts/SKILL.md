---
name: review-posts
description: Turns any business's newest 5-star reviews (Google, Yelp, BBB, Facebook, Trustpilot, Houzz, Angi, the business's own website, or pasted text) into ready-to-post Instagram images (1080x1350) in the business's own brand, with captions and an approval sheet. The first time, it sets the brand up from the website: logo, colors, fonts, background photos, review links and a choice of layouts. Use when someone says "make review posts", "turn our reviews into Instagram posts", "post our 5-star reviews", "review graphics", "quote cards from reviews", "set up review posts for my business", or pastes a review and wants a post. It never posts anything itself.
---

# Review posts

You're helping a business owner or marketer who is probably **not technical**. Keep messages short, warm and plain. Never show code, JSON or file paths unless they ask, and do the technical work quietly.

This skill **never posts, publishes or replies** online. The person approves the images and posts them themselves.

**Tools:** everything is in `scripts/`, next to this file. The scripts are `brand_kit.py` (reads a website) and `make_posts.py` (makes the images). Both need Python 3 and Pillow; if you see "Pillow is missing", run `pip install pillow`. Default fonts are bundled.

**The business folder** holds everything about one business: `settings.json`, the logo, `photos/`, `fonts/`, and `seen.json` (reviews already turned into posts). Name it `<Business Name> Review Posts/` and keep it in the working folder, which in Cowork is the folder the person picked. If it already has a `settings.json`, skip setup and go to **Every week** below.

---

## First time: set up the brand (about 10 minutes)

Tell the person in one line: *"First I'll set up your look from your website. Takes about 10 minutes, once."*

### 1. Ask two things, in one message

1. **"What's your business name and website?"**
2. **"Where do your reviews live?"** Offer: Google, Yelp, BBB, Facebook, Trustpilot, Houzz, Angi, Nextdoor, or testimonials on their website. Say: *"Paste the links if you have them. If not, I'll find them on your website."*

### 2. Pull the brand from the website

Make the business folder, then run:

```bash
python3 scripts/brand_kit.py "<website>" --folder "<Business> Review Posts"
```

It saves logo candidates, big photos, any Google Fonts, and `brand-kit/brand-kit.json`, which lists the colors, fonts, phone number and review links it found.

- **If the script can't open the site** (blocked, or no internet in your sandbox): open the website in the browser instead. Screenshot the logo, read the colors and fonts with `javascript_tool` (below), and ask the person to send their logo file if needed.
- **Fonts not found** (common: many sites load fonts with JavaScript): in the browser, run
  `['h1','h2','p'].map(t => t + ': ' + getComputedStyle(document.querySelector(t) || document.body).fontFamily)`
  Then fetch each family with `python3 scripts/brand_kit.py --get-font "<Family>" --folder "<folder>"`. If it isn't a Google Font, use the closest bundled one: Playfair Display (elegant serif), Poppins (clean sans), or Raleway (labels). The person can also send the .ttf file.

Then **look at every file yourself** and choose:
- **Logo:** the cleanest full logo (name included), PNG, ideally transparent. Skip partner, award, certification and review-site badges. Copy it to `logo.png`.
- **Colors:** start from `colors.suggested` in brand-kit.json, and check it against the logo.
  - `dark` sits behind white text, so it must be dark (navy, forest, charcoal, deep teal).
  - `darker` is a deeper shade of it.
  - `accent` is the stars, highlights and lines: the brand's bright color.
  - `accent_light` is a lighter tint of the accent.
  - If the brand has no dark color, use a very dark shade of its main color.
- **Photos:** see step 3.

### 3. Background photos

The images look best with a real photo behind the quote, and the photo changes on every post. Pick the source in this order:

1. **Their own photos:** keep good ones from `brand-kit/` (their website) and copy them into `photos/`. Also ask: *"Got any photos of your work? Drone shots, finished jobs, your storefront or team? Drop them here."*
2. **Free stock photos that match the business and area,** if they have few of their own. Follow `reference/photos.md`. Rules: free for commercial use, credited in `photos/PHOTO-CREDITS.md`, and **showing what the business works on**. For example, homes and roofs for a roofer (never downtown skylines), smiles and a calm clinic for a dentist, plated food for a restaurant.
3. **No photos:** the "brand color" layout needs none.

Quality bar for every photo:
- At least 1500px on the long side. Never upscale a small one; it turns blurry.
- No text or watermarks, nothing dark or cluttered, and no faces of identifiable strangers.
- Aim for 8 to 15 photos, so the feed doesn't repeat.
- Name the files by kind (`job-01.jpg`, `area-01.jpg`, and so on). The rotation then alternates between the kinds.

### 4. Show the look options

Write `settings.json` (see `reference/settings.md`) and run:

```bash
python3 scripts/make_posts.py --folder "<folder>" --preview
```

It makes the same sample review in each layout, using their logo, colors, fonts and photos. Show all of them, then ask *"Which do you like?"*:

1. **Big quote on a photo:** bold, best for short reviews.
2. **Review card on a photo:** looks like a real review, best for longer ones.
3. **Brand color, no photo:** clean, and needs no photos.
4. **Carousel:** 2 slides for very long reviews. Slide 1 has the best line, slide 2 the full review.

Recommend **Automatic**: short reviews get layout 1, longer ones get layout 2, and only very long ones (70+ words) become carousels. Fix whatever they don't like (logo too small, wrong color, a bad photo crop), run `--preview` again, and repeat until they're happy.

### 5. Captions

Ask once: *"What should every caption end with? Most people use a phone number or 'Book online' plus a few hashtags."* Suggest one using the phone number from brand-kit.json and 3 or 4 local hashtags. Save it as `caption.extras` and `caption.hashtags`.

### 6. Wrap up the setup

Delete `brand-kit/` and `setup-previews/`; they were only for setup. Then tell them, in a short list, **what they can change any time just by asking:**
- "Use these photos as backgrounds" (or "remove the photo with the pool")
- "Make the logo bigger" or "use our color logo"
- "Change the gold to our orange"
- "Only use the review card look" or "no carousels"
- "Add Yelp" (or any other review site)
- "Change the caption ending"

Then go straight to **Every week** and make their first posts.

---

## Every week: make the posts

### 1. Get the newest 5-star reviews

Use `review_links` in `settings.json`. **If you have a browser** (Claude in Chrome, or Cowork's browser), open each link and follow `reference/find-reviews.md`. Read only: never click Reply, Like, Report or Write a review. **If you can't browse, or a page is blocked:** ask the person to paste the reviews in.

Rules:
- **5-star only.** Skip anything lower, unless the person asks otherwise in `settings.json` (`only_stars`).
- **Same review in two places** (a customer often posts on Google and BBB, or a site reposts Google reviews): make **one** post. Prefer the copy with no redactions.
- **Customer photos and profile pictures:** reviews with photos make the best posts, so look for them on purpose, including older 5-star reviews with photos that aren't in `seen.json` yet. When a reviewer attached a photo that works as a background (the finished roof, the house, the crew; sharp; no text, labels or watermark), save it in `photos/from-reviews/` and set `"photo"` on that review: it becomes that post's background, and only that post's. Crop a before/after collage down to the "after" panel. If no photo works, leave `photo` out and the post uses the normal rotation. Save a real profile picture to `photos/avatars/` and set `"avatar"`; skip Google's default one-letter icons. The details are in `reference/find-reviews.md` ("Customer photos and profile pictures"). In the hand-over, say which posts use the customer's own photo.
- Reviews already in `seen.json` are skipped automatically. Say how many were new.

### 2. Write `reviews.json` (you do this; the person never sees it)

The format is at the top of `scripts/make_posts.py`.

- **`quote`:** the full review, word for word. Never fix spelling or grammar.
- **`name`:** first name plus last initial ("Sarah M.").
- **`source`:** where it was posted ("Google", "Yelp", and so on). It's shown on the image.
- **`excerpt`** (long reviews only): the 1 to 3 strongest whole sentences, word for word.
- **`hl`:** one short phrase to highlight, word for word.
- **Hidden names:** some sites (BBB) show staff names as "REMOVED". Don't leave "REMOVED" in, and never guess the name.
  - First, try an `excerpt` that avoids it.
  - Otherwise, swap it for the plainest role word that reads naturally, with no brackets. For example: `"edits": [{"from": "REMOVED(owner)", "to": "The owner"}]`.
- **`caption`:** under 80 words, in the business's own voice.
  - Thank the reviewer by first name.
  - Mention one specific thing they said.
  - End with `caption.extras` and the hashtags.
  - Never invent details.

### 3. Make the images

```bash
python3 scripts/make_posts.py --folder "<folder>" reviews.json
```

**Look at every image before you show it.** Check for:
- cut-off text
- a bad photo crop (fix it with `photo_focus` in settings.json, then run again)
- a photo that doesn't fit the business (remove it from `photos/`)

### 4. Hand over

1. Show the images grouped per post, with each caption underneath.
2. Give them the `posts/<date>` folder, zipped if you can. It holds the images, `captions.md`, and `approval.csv` (opens in Excel or Google Sheets).
3. Tell them in plain words:
   - how many posts were made, and how many are carousels
   - anything that was skipped or edited
   - that **nothing was posted**
   - next time, they just say "make review posts".
