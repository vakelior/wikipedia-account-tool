# Wikipedia Account Creator — GitHub Actions

نفس الطريقة ديال المتصفح السحابي، ولكن مشغّلة فـ GitHub Actions عبر Playwright (متصفح Chromium حقيقي headless).

## كيفاش تخدم؟

1. الـ repo منشور بالفعل لـ `vakelior/wikipedia-account-tool`.
2. دخل للـ repo → تبويبة **Actions** → شغّل **create-wikipedia-accounts** يدويًا (Run workflow) أو خلّي الجدولة cron ديالية.

## الملفات

- `wiki_create.py` — السكربت الرئيسي (Playwright + Chromium).
- `.github/workflows/create.yml` — الـ workflow.
- `requirements.txt` — `playwright`.
- `batches/sample.json` — مثال batch (عدّل فيه الأسماء).

## الاستعمال اليدوي (Run workflow)

- **username** (اختياري): اسم واحد باش ينخلق.
- **password** (اختياري): كلمة السر ديالو.
- إذا خليتي الحقول خاوية، غادي يقرا `batches/sample.json`.

## ⚠️ القيود الحقيقية (باش ما تتفاجأش)

1. **GitHub Actions IP محظور غالبًا من Wikimedia**: الرانر كيستخدم IPs ديال Microsoft/Azure datacenter، وهادو محظورين بصفة "Open proxy/Webhost". يعني ممكن تدخل فبلوك IP مباشرة.
2. **hCaptcha المرئي**: الـ headless ما كيقدرش يحل الـ hCaptcha البصري. إلا ظهر، السكربت كيوقف ويعطيك `captcha_required`.
3. **حد 6 حسابات لكل IP / 24 ساعة**: الـ IP ديال الرانر ثابت تقريبًا.

## تشخيص النتيجة

السكربت كيرجع `results.json` بكل حساب وحالته:
- `created` ✅
- `captcha_required` — ظهر كابتشا بصري
- `ip_limit` — وصلتي حد 6/24h
- `blocked` — الـ IP محظور
