# Finding background photos

Each post uses the next photo in `photos/`, so 8 to 15 good photos keep the feed fresh.

## Best: the business's own photos
- Photos from their website, found by `brand_kit.py` in `brand-kit/photo-*.jpg`. Keep only real work, the place itself, or the team at work. Drop stock-looking banners, photos with text on them, and badges.
- Ask the person for drone shots, finished jobs, before-and-afters, the storefront, or the team.
- Photos attached to a review become that review's background (see SKILL.md).

## Next: free stock photos that fit
Use **Unsplash** (unsplash.com) or **Pexels** (pexels.com). Both are free for commercial use with no sign-up needed to download.
1. In the browser, search for what the business works on plus the area. Some examples:
   - roofer, landscaper or builder: "aerial neighborhood houses <city>", "suburban homes drone", "roof aerial"
   - dentist or clinic: "dental clinic interior", "bright smile"
   - restaurant: "<cuisine> food overhead"
   - cleaner: "clean bright living room"
2. Open each photo's page. Download the **largest** size (the "Download" button, or "Original").
3. Check that it really shows what the business does. For home services that means **homes and roofs, never downtown skylines or office towers**. Also check that it is sharp at full size, has no watermark, and has no close-up faces.
4. Save it as `area-01.jpg`, `area-02.jpg`, and so on, and add a line to `photos/PHOTO-CREDITS.md`: file, photographer, link.

Never use photos from Google Images, competitors' sites or Instagram accounts that aren't the business's own.

## Check the result
After making posts, look at each image. If a crop cuts off the roof or a face, set `photo_focus` for that file in settings.json. If a photo looks blurry or off-topic, delete it.
