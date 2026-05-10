let openedGuide = null;

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

function goHome(){

    const guideContent =
        document.getElementById("guideContent");

    if(guideContent){

        guideContent.innerHTML = "";
    }

    openedGuide = null;

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

    topBanner.addEventListener(
        "click",
        goHome
    );
}

window.addEventListener(
    "load",
    bindTopBannerHome
);

/* GUIDES */

const guides = {

fax: `

<div class="guide-box" id="pdf-content">

<h2>
מדריך שליחת פקס מהמייל
</h2>

<p style="margin-bottom:25px;">
אנו שמחים לעדכן כי צורפת לשירות מייל 2 פקס.
</p>

<ol class="guide-steps">

<li>

פתח את תיבת המייל שלך.

</li>

<li>

בשדה TO יש להזין את כתובת הפקס בצורה הבאה:

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

יש להזין את מספר הפקס אליו תרצה לשלוח.

</li>

<li>

לדוגמה:

<br><br>

<b>
031234567@fax.tc
</b>

<br><br>

שימו לב:
המספר חייב להופיע בצד שמאל של הסימן @

</li>

<li>

בשדה SUBJECT ניתן לרשום מידע לתיעוד עצמי בלבד.

<br>

הטקסט לא יישלח בפקס.

</li>

<li>

בגוף המייל ניתן:

<ul>

<li>
לכתוב טקסט חופשי
</li>

<li>
או לצרף קובץ
</li>

</ul>

רק אחד מהם יישלח.

</li>

<li>

מומלץ לצרף קובץ PDF,
אך ניתן גם לשלוח פורמטים נוספים.

</li>

<li>

לאחר מספר דקות יתקבל מייל חוזר
עם אישור האם הפקס נשלח בהצלחה.

</li>

</ol>

<button class="download-btn"
onclick="openGuidePreview('Guide Preview')">

הצגת מדריך PDF

</button>

</div>

`,

sms: `

<div class="guide-box" id="pdf-content">

<h2>
שירות SMS
</h2>

<p>
ניתן לשנות את תוכן ההודעה בכל שלב.
</p>

<p>
הודעת שירות עד 160 תווים.
</p>

<p>
ניתן להגדיר שם עסק באנגלית בלבד עד 11 תווים.
</p>

<button class="download-btn"
onclick="openGuidePreview('Guide Preview')">

הצגת מדריך PDF

</button>

</div>

`,

recordings: `

<div class="guide-box" id="pdf-content">

<h2>
הקלטות שיחות ודוחות
</h2>

<img src="assets/Rec.png"
class="recording-image">

<p>
לקבלת גישה לממשק יש ליצור קשר ב-WhatsApp:
</p>

<a class="whatsapp-access"
href="https://wa.me/972778066666"
target="_blank">

<i class="fa-brands fa-whatsapp"></i>

מעבר לתמיכה WhatsApp

</a>

<h3 style="margin-top:35px;">
לינק למערכת:
</h3>

<p>

<a href="https://hot.nimbusip.com/"
target="_blank">

https://hot.nimbusip.com/

</a>

</p>

<button class="download-btn"
onclick="openGuidePreview('Guide Preview')">

הצגת מדריך PDF

</button>

</div>

`,

yealink: `

<div class="guide-box">

<h2>
מדריך כללי למשתמשי Yealink
</h2>

<!-- PDF -->

<div class="sub-guide">

<h3>
מדריך מלא למשתמש
</h3>

<iframe
class="pdf-viewer"
src="guides/manual-centrix.pdf">
</iframe>

</div>

<!-- A -->

<div class="sub-guide">

<h3>
A) טיפול ברעשים בשמע
<p>
W70B
</p>
</h3>

<p>
אם קיימים רעשים בשמע יש לבצע הפעלה מחדש דרך השפופרת לקו:
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
יש להמתין 2-4 דקות עד שהבסיס יעלה מחדש
ויירשם למרכזייה.
</p>

<p>
לאחר מכן יש לבצע בדיקה חוזרת.
</p>

</div>

<!-- B -->

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

<!-- C -->

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

/* TOGGLE GUIDE */

function toggleGuide(type){

    const guideContent =
        document.getElementById("guideContent");

    if(openedGuide === type){

        guideContent.innerHTML = "";

        openedGuide = null;

        window.scrollTo({

            top:0,

            behavior:'smooth'
        });

        return;
    }

    openedGuide = type;

    guideContent.innerHTML =
        guides[type];

    window.scrollTo({

        top:450,

        behavior:'smooth'
    });
}

/* SEARCH */

function searchGuides(){

    const value =
        document.getElementById("guideSearch")
        .value
        .toLowerCase();

    const cards =
        document.querySelectorAll(".card");

    cards.forEach(card => {

        const text =
            card.innerText.toLowerCase();

        if(text.includes(value)){

            card.style.display = "block";

        }else{

            card.style.display = "none";
        }

    });

}

/* GUIDE PREVIEW */

function openGuidePreview(title){

    const element =
        document.getElementById("pdf-content");

    if(!element){

        return;
    }

    const previewWindow =
        window.open("", "_blank");

    if(!previewWindow){

        alert("Please allow popups to open the guide preview.");
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
        "body{margin:0;background:#0f0f0f;color:#fff;font-family:Arial}" +
        ".action-bar{position:sticky;top:0;z-index:10;background:#151515;border-bottom:1px solid #2a2a2a;display:flex;gap:10px;justify-content:center;align-items:center;padding:12px;flex-wrap:wrap}" +
        ".action-btn{background:#d1006f;color:#fff;border:none;border-radius:10px;padding:10px 16px;font-size:15px;cursor:pointer}" +
        ".guide-wrap{max-width:900px;margin:0 auto;padding:18px}" +
        ".guide-box{background:#181818;border:1px solid #2b2b2b;border-radius:16px;padding:22px;line-height:1.9}" +
        ".guide-box h2,.guide-box h3{color:#ff1493}" +
        ".guide-box a{color:#fff}" +
        ".guide-box img,.guide-box video,.guide-box iframe{max-width:100%;display:block;margin:12px auto;border-radius:12px}" +
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
    shareBtn.textContent = "Share";
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
            "Direct share is not supported in this browser."
        );
    });

    const printBtn =
        doc.createElement("button");

    printBtn.className = "action-btn";
    printBtn.textContent = "Print / Save PDF";
    printBtn.addEventListener("click", () => {

        previewWindow.print();
    });

    actionBar.appendChild(shareBtn);
    actionBar.appendChild(printBtn);

    const wrapper =
        doc.createElement("main");

    wrapper.className = "guide-wrap";

    const clonedGuide =
        element.cloneNode(true);

    wrapper.appendChild(clonedGuide);

    doc.body.appendChild(actionBar);
    doc.body.appendChild(wrapper);
}


