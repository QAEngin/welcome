let openedGuide = null;

const customerLookupConfig = {
    enabled: false,
    crmProvider: "future-crm",
    requiredFields: [
        "businessId",
        "businessPhone"
    ]
};

function updateSearchStickyOffset(){

    const root = document.documentElement;

    const topBanner =
        document.querySelector(".top-banner");

    const bannerHeight =
        topBanner ? topBanner.offsetHeight : 0;

    root.style.setProperty(
        "--search-sticky-top",
        `${bannerHeight}px`
    );
}

window.addEventListener(
    "load",
    updateSearchStickyOffset
);

window.addEventListener(
    "resize",
    updateSearchStickyOffset
);

function clearActiveCards(){

    const cards =
        document.querySelectorAll(".card");

    cards.forEach(card => {

        card.classList.remove("active");
        card.removeAttribute("aria-pressed");

    });
}

function clearSearchResults(){

    const resultsContainer =
        document.getElementById("guideSearchResults");

    if(!resultsContainer){

        return;
    }

    resultsContainer.innerHTML = "";
    resultsContainer.classList.remove("active");
}

function resetSearchState(){

    const searchInput =
        document.getElementById("guideSearch");

    if(searchInput){

        searchInput.value = "";
    }

    document.querySelectorAll(".card").forEach(card => {

        card.style.display = "";

    });

    clearSearchResults();
}

function goHome(){

    const guideContent =
        document.getElementById("guideContent");

    if(guideContent){

        guideContent.innerHTML = "";
    }

    openedGuide = null;
    clearActiveCards();
    resetSearchState();

    window.scrollTo({

        top:0,

        behavior:"smooth"
    });
}

function bindTopBannerHome(){

    const topBanner =
        document.querySelector(".top-banner");

    if(!topBanner){

        return;
    }

    topBanner.addEventListener("click", event => {

        if(event.target.closest(".nav-support-btn, .nav-link")){

            return;
        }

        if(event.target.closest(".nav-logo")){

            event.preventDefault();
        }

        goHome();
    });
}

window.addEventListener(
    "load",
    bindTopBannerHome
);

const guides = {

fax: `

<div class="guide-box" id="pdf-content">

<h2>
מדריך שליחת פקס מהמייל
</h2>

<p class="guide-intro">
שירות מייל 2 פקס מאפשר לשלוח פקס ישירות מתיבת המייל של העסק, ללא צורך במכשיר פקס פיזי.
</p>

<ol class="guide-steps">

<li>
פתחו את תיבת המייל שלכם.
</li>

<li>
בשדה הנמען (TO) יש להזין את כתובת הפקס במבנה הבא:

<br><br>

<b>
fax_number@fax.tc
</b>

</li>

<li>
במקום:
<b>
fax_number
</b>
יש להזין את מספר הפקס שאליו תרצו לשלוח.
</li>

<li>
לדוגמה:

<br><br>

<b>
031234567@fax.tc
</b>

<br><br>

שימו לב: המספר חייב להופיע בצד שמאל של הסימן @.
</li>

<li>
בשדה הנושא (SUBJECT) ניתן לרשום מידע לתיעוד עצמי בלבד. הטקסט לא יישלח בפקס.
</li>

<li>
בגוף המייל ניתן לכתוב טקסט חופשי או לצרף קובץ.

<ul>
<li>אם שולחים טקסט בלבד, הטקסט יישלח בפקס.</li>
<li>אם מצרפים קובץ, הקובץ יישלח בפקס.</li>
</ul>

</li>

<li>
מומלץ לצרף קובץ PDF, אך ניתן לשלוח גם פורמטים נוספים.
</li>

<li>
לאחר מספר דקות יתקבל מייל חוזר עם סטטוס השליחה.
</li>

</ol>

<p class="guide-note">
מומלץ לוודא שמספר הפקס תקין לפני השליחה, כולל קידומת אזורית מלאה.
</p>

<button class="download-btn"
onclick="openGuidePreview('מדריך מייל 2 פקס')">

הצגת מדריך PDF

</button>

</div>

`,

sms: `

<div class="guide-box" id="pdf-content">

<h2>
שירות SMS
</h2>

<p class="guide-intro">
שירות SMS עסקי מאפשר לשלוח הודעות שירות ללקוחות העסק עם נוסח מוגדר ושם שולח.
</p>

<ol class="guide-steps">

<li>
ניתן לעדכן את תוכן ההודעה בהתאם לצורך העסקי.
</li>

<li>
הודעת שירות סטנדרטית מוגבלת עד 160 תווים.
</li>

<li>
שם השולח יכול להיות באנגלית בלבד ועד 11 תווים.
</li>

<li>
כדאי לנסח הודעה קצרה, ברורה וללא מידע רגיש שאינו נדרש.
</li>

</ol>

<p class="guide-note">
אם נדרש שינוי בנוסח ההודעה או בשם השולח, יש לפנות לתמיכה.
</p>

<button class="download-btn"
onclick="openGuidePreview('מדריך שירות SMS')">

הצגת מדריך PDF

</button>

</div>

`,

recordings: `

<div class="guide-box" id="pdf-content">

<h2>
הקלטות שיחות ודוחות
</h2>

<p class="guide-intro">
ממשק ההקלטות מאפשר לצפות בשיחות מוקלטות, לאתר שיחות לפי פרטים רלוונטיים ולהפיק מידע תפעולי עבור העסק.
</p>

<img src="assets/Rec.png"
class="recording-image"
alt="מסך מערכת הקלטות שיחות">

<p>
לקבלת גישה לממשק או עזרה בהתחברות יש ליצור קשר ב-WhatsApp:
</p>

<a class="whatsapp-access"
href="https://wa.me/972778066666"
target="_blank"
rel="noopener">

<i class="fa-brands fa-whatsapp"></i>

מעבר לתמיכה WhatsApp

</a>

<h3>
כניסה למערכת
</h3>

<p>
<a href="https://hot.nimbusip.com/"
target="_blank"
rel="noopener">
https://hot.nimbusip.com/
</a>
</p>

<p class="guide-note">
פרטי הכניסה למערכת ניתנים בהתאם להרשאות השירות שהוגדרו לעסק.
</p>

<button class="download-btn"
onclick="openGuidePreview('מדריך הקלטות שיחות')">

הצגת מדריך PDF

</button>

</div>

`,

yealink: `

<div class="guide-box">

<h2>
מדריך כללי למשתמשי Yealink
</h2>

<p class="guide-intro">
כאן ניתן למצוא מדריך מלא לטלפוני Yealink, פעולות נפוצות וסרטוני הדרכה לשימוש במרכזייה.
</p>

<div class="sub-guide">

<h3>
מדריך מלא למשתמש
</h3>

<iframe
class="pdf-viewer"
src="guides/manual-centrix.pdf"
title="מדריך מלא למשתמש Yealink">
</iframe>

</div>

<div class="sub-guide">

<h3>
A) טיפול ברעשים בשמע
</h3>

<p>
אם קיימים רעשים בשמע בדגם W70B, יש לבצע הפעלה מחדש דרך השפופרת:
</p>

<ol class="guide-steps">

<li>
מקש OK
</li>

<li>
הגדרות
</li>

<li>
הגדרות מערכת
</li>

<li>
אתחול בסיס
<br>
קוד:
<b>0000</b>
</li>

</ol>

<p>
יש להמתין 2-4 דקות עד שהבסיס יעלה מחדש ויירשם למרכזייה.
</p>

<p>
לאחר מכן יש לבצע בדיקה חוזרת.
</p>

</div>

<div class="sub-guide">

<h3>
B) הוספת BLF
</h3>

<video class="guide-video"
controls>

<source
src="guides/video/BLF.mp4"
type="video/mp4">

</video>

</div>

<div class="sub-guide">

<h3>
C) שיחת וועידה
</h3>

<video class="guide-video"
controls>

<source
src="guides/video/Conference call.mp4"
type="video/mp4">

</video>

</div>

</div>

`

};

function getGuideTypeFromCard(card){

    const action =
        card.getAttribute("onclick") || "";

    const match =
        action.match(/toggleGuide\('([^']+)'\)/);

    return match ? match[1] : "";
}

function getPlainTextFromHtml(html){

    const template =
        document.createElement("template");

    template.innerHTML =
        html;

    return template.content.textContent || "";
}

function normalizeSearchText(text){

    return (text || "")
        .toString()
        .toLowerCase()
        .replace(/\s+/g, " ")
        .trim();
}

function getSearchSnippet(text, query){

    const cleanText =
        (text || "").replace(/\s+/g, " ").trim();

    if(!cleanText){

        return "";
    }

    const normalizedText =
        cleanText.toLowerCase();

    const index =
        normalizedText.indexOf(query);

    if(index === -1){

        return cleanText.slice(0, 110);
    }

    const start =
        Math.max(0, index - 45);

    const end =
        Math.min(cleanText.length, index + query.length + 65);

    const prefix =
        start > 0 ? "... " : "";

    const suffix =
        end < cleanText.length ? " ..." : "";

    return `${prefix}${cleanText.slice(start, end)}${suffix}`;
}

function getGuideSearchItems(){

    return Array.from(document.querySelectorAll(".card"))
        .map(card => {

            const type =
                getGuideTypeFromCard(card);

            const title =
                card.querySelector(".card-title")?.textContent.trim() || card.textContent.trim();

            const cardText =
                card.textContent || "";

            const guideText =
                getPlainTextFromHtml(guides[type] || "");

            return {
                type,
                title,
                card,
                guideText,
                searchText:normalizeSearchText(`${title} ${cardText} ${guideText}`)
            };

        })
        .filter(item => item.type);
}

function renderSearchResults(results, query){

    const resultsContainer =
        document.getElementById("guideSearchResults");

    if(!resultsContainer){

        return;
    }

    resultsContainer.innerHTML = "";
    resultsContainer.classList.toggle("active", results.length > 0);

    results.forEach(item => {

        const resultButton =
            document.createElement("button");

        resultButton.type = "button";
        resultButton.className = "search-result-link";
        resultButton.addEventListener("click", () => {

            clearSearchResults();

            if(openedGuide === item.type){

                document.getElementById("guideContent")?.scrollIntoView({

                    behavior:"smooth",

                    block:"start"
                });

                return;
            }

            toggleGuide(item.type);

        });

        const title =
            document.createElement("span");

        title.className = "search-result-title";
        title.textContent = item.title;

        const snippet =
            document.createElement("span");

        snippet.className = "search-result-snippet";
        snippet.textContent =
            getSearchSnippet(item.guideText || item.card.textContent, query);

        resultButton.appendChild(title);
        resultButton.appendChild(snippet);

        resultsContainer.appendChild(resultButton);

    });
}

function getFeatureLookupMarkup(){

    return `

<div class="feature-auth-layout">

<section class="feature-auth-info" aria-labelledby="featureAuthTitle">

<span>איזור אישי ללקוח</span>

<h2 id="featureAuthTitle">
בדיקת שירותים לפי ח.פ וטלפון ראשי
</h2>

<p>
הזינו את פרטי העסק כפי שהם מופיעים במערכת. לאחר אימות מול ה-CRM יוצגו השירותים הפעילים והפרטים שהוגדרו עבור העסק.
</p>

</section>

<section class="feature-lookup-card" aria-label="אימות לקוח">

<div class="feature-lookup-form">

<label for="businessFeatureId">
ח.פ / עוסק מורשה
</label>

<input
id="businessFeatureId"
class="feature-lookup-input"
type="text"
inputmode="numeric"
autocomplete="off"
placeholder="לדוגמה: 514123456"
oninput="updateFeatureCheckButton()">

<label for="businessMainPhone">
מספר טלפון ראשי
</label>

<input
id="businessMainPhone"
class="feature-lookup-input"
type="tel"
inputmode="tel"
autocomplete="tel"
placeholder="לדוגמה: 03-1234567"
oninput="updateFeatureCheckButton()">

<button
id="featureCheckBtn"
class="download-btn feature-check-btn"
type="button"
onclick="handleFeatureLookupCheck()"
disabled>
<i class="fa-solid fa-right-to-bracket" aria-hidden="true"></i>
כניסה לאזור האישי
</button>

</div>

</section>

</div>

`;
}

function showFeatureLookup(){

    const guideContent =
        document.getElementById("guideContent");

    if(!guideContent){

        return;
    }

    if(openedGuide === "featureLookup"){

        guideContent.scrollIntoView({

            behavior:"smooth",

            block:"start"
        });

        return;
    }

    openedGuide = "featureLookup";
    clearActiveCards();
    clearSearchResults();

    guideContent.innerHTML =
        getFeatureLookupMarkup();

    guideContent.scrollIntoView({

        behavior:"smooth",

        block:"start"
    });
}

function updateFeatureCheckButton(){

    const businessIdInput =
        document.getElementById("businessFeatureId");

    const phoneInput =
        document.getElementById("businessMainPhone");

    const button =
        document.getElementById("featureCheckBtn");

    if(!businessIdInput || !phoneInput || !button){

        return;
    }

    button.disabled =
        businessIdInput.value.trim().length === 0 ||
        phoneInput.value.trim().length === 0;
}

function handleFeatureLookupCheck(){

    const businessIdInput =
        document.getElementById("businessFeatureId");

    const phoneInput =
        document.getElementById("businessMainPhone");

    const button =
        document.getElementById("featureCheckBtn");

    if(
        !businessIdInput ||
        !phoneInput ||
        !button ||
        !businessIdInput.value.trim() ||
        !phoneInput.value.trim()
    ){

        return;
    }

    button.disabled = true;
    button.classList.add("loading");
    button.dataset.defaultText =
        button.dataset.defaultText || button.innerHTML.trim();
    button.textContent = "בודק...";

    window.setTimeout(() => {

        button.classList.remove("loading");
        button.innerHTML =
            button.dataset.defaultText || "כניסה לאזור האישי";
        button.disabled =
            businessIdInput.value.trim().length === 0 ||
            phoneInput.value.trim().length === 0;

        showFeatureSupportPopup();

    }, 1400);
}

function closeFeatureSupportPopup(){

    const popup =
        document.getElementById("featureSupportPopup");

    if(popup){

        popup.remove();
    }
}

function showFeatureSupportPopup(){

    closeFeatureSupportPopup();

    const popup =
        document.createElement("div");

    popup.id = "featureSupportPopup";
    popup.className = "support-popup-backdrop";
    popup.setAttribute("role", "dialog");
    popup.setAttribute("aria-modal", "true");
    popup.setAttribute("aria-labelledby", "featureSupportTitle");

    popup.innerHTML = `
        <div class="support-popup">
            <button
                class="support-popup-close"
                type="button"
                aria-label="סגירה"
                onclick="closeFeatureSupportPopup()">
                ×
            </button>
            <div class="support-popup-icon">
                <i class="fa-brands fa-whatsapp" aria-hidden="true"></i>
            </div>
            <h2 id="featureSupportTitle">לא נמצאו פרטי שירות</h2>
            <p>
                לא הצלחנו לזהות את פירטי שירות לפי ח.פ שהקשת נא ליצור קשר מול התמיכה לקבלת שירות
            </p>
            <a
                class="support-popup-whatsapp"
                href="https://wa.me/972778066666"
                target="_blank"
                rel="noopener">
                <i class="fa-brands fa-whatsapp" aria-hidden="true"></i>
                יצירת קשר עם התמיכה
            </a>
        </div>
    `;

    popup.addEventListener("click", event => {

        if(event.target === popup){

            closeFeatureSupportPopup();
        }
    });

    document.body.appendChild(popup);
}

function toggleGuide(type){

    const guideContent =
        document.getElementById("guideContent");

    if(!guideContent || !guides[type]){

        return;
    }

    clearActiveCards();

    if(openedGuide === type){

        guideContent.innerHTML = "";

        openedGuide = null;

        window.scrollTo({

            top:0,

            behavior:"smooth"
        });

        return;
    }

    openedGuide = type;

    guideContent.innerHTML =
        guides[type];

    const activeCard =
        document.querySelector(`[onclick="toggleGuide('${type}')"]`);

    if(activeCard){

        activeCard.classList.add("active");
        activeCard.setAttribute("aria-pressed", "true");

    }

    guideContent.scrollIntoView({

        behavior:"smooth",

        block:"start"
    });
}

function searchGuides(){

    const searchInput =
        document.getElementById("guideSearch");

    if(!searchInput){

        return;
    }

    const value =
        normalizeSearchText(searchInput.value);

    const searchItems =
        getGuideSearchItems();

    if(!value){

        searchItems.forEach(item => {

            item.card.style.display = "";

        });

        renderSearchResults([], value);

        return;
    }

    const matches =
        searchItems.filter(item => item.searchText.includes(value));

    searchItems.forEach(item => {

        item.card.style.display =
            matches.includes(item) ? "" : "none";

    });

    renderSearchResults(matches, value);
}

function openGuidePreview(title){

    const element =
        document.getElementById("pdf-content");

    if(!element){

        return;
    }

    const previewWindow =
        window.open("", "_blank");

    if(!previewWindow){

        alert("יש לאפשר פתיחת חלונות קופצים כדי להציג את המדריך.");
        return;
    }

    const baseHref =
        window.location.href.slice(
            0,
            window.location.href.lastIndexOf("/") + 1
        );

    const doc =
        previewWindow.document;

    doc.open();
    doc.write("<!DOCTYPE html><html><head><meta charset='UTF-8'><meta name='viewport' content='width=device-width, initial-scale=1.0'><title></title></head><body></body></html>");
    doc.close();

    doc.documentElement.lang = "he";
    doc.documentElement.dir = "rtl";
    doc.title = title;

    const base =
        doc.createElement("base");

    base.href = baseHref;
    doc.head.appendChild(base);

    const style =
        doc.createElement("style");

    style.textContent =
        "*{box-sizing:border-box}" +
        "body{margin:0;background:#0f0f0f;color:#fff;font-family:Arial;direction:rtl}" +
        ".action-bar{position:sticky;top:0;z-index:10;background:#151515;border-bottom:1px solid #2a2a2a;display:flex;gap:10px;justify-content:center;align-items:center;padding:12px;flex-wrap:wrap}" +
        ".action-btn{background:#d1006f;color:#fff;border:none;border-radius:8px;padding:10px 16px;font-size:15px;cursor:pointer}" +
        ".guide-wrap{max-width:900px;margin:0 auto;padding:18px}" +
        ".guide-box{background:#181818;border:1px solid #2b2b2b;border-radius:8px;padding:22px;line-height:1.9}" +
        ".guide-box h2,.guide-box h3{color:#ff1493}" +
        ".guide-box a{color:#fff}" +
        ".guide-box img,.guide-box video,.guide-box iframe{max-width:100%;display:block;margin:12px auto;border-radius:8px}" +
        ".guide-note{background:#111;border-right:4px solid #d1006f;border-radius:8px;padding:12px 14px}" +
        ".guide-box video{max-width:540px}" +
        ".download-btn{display:none !important}" +
        "@media (max-width:768px){.guide-wrap{padding:12px}.guide-box{padding:16px}.guide-box video{max-width:100%}}";

    doc.head.appendChild(style);

    const actionBar =
        doc.createElement("div");

    actionBar.className =
        "action-bar";

    const shareBtn =
        doc.createElement("button");

    shareBtn.className = "action-btn";
    shareBtn.textContent = "שיתוף";
    shareBtn.addEventListener("click", () => {

        if(previewWindow.navigator.share){

            previewWindow.navigator
                .share({
                    title: doc.title,
                    text: doc.title,
                    url: previewWindow.location.href
                })
                .catch(() => {});

            return;
        }

        previewWindow.alert(
            "שיתוף ישיר אינו נתמך בדפדפן הזה."
        );
    });

    const printBtn =
        doc.createElement("button");

    printBtn.className = "action-btn";
    printBtn.textContent = "הדפסה / שמירה כ-PDF";
    printBtn.addEventListener("click", () => {

        previewWindow.print();
    });

    actionBar.appendChild(shareBtn);
    actionBar.appendChild(printBtn);

    const wrapper =
        doc.createElement("main");

    wrapper.className =
        "guide-wrap";

    const clonedGuide =
        element.cloneNode(true);

    wrapper.appendChild(clonedGuide);

    doc.body.appendChild(actionBar);
    doc.body.appendChild(wrapper);
}
