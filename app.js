let openedGuide = null;

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
onclick="generatePDF('מדריך-פקס')">

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
onclick="generatePDF('מדריך-SMS')">

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
onclick="generatePDF('הקלטות-שיחות')">

הצגת מדריך PDF

</button>

</div>

`,

yealink: `

<div class="guide-box">

<h2>
מדריך כללי למשתמשי Yealink
</h2>

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

/* PDF */

function generatePDF(fileName){

    const element =
        document.getElementById("pdf-content");

    if(!element){

        return;
    }

    const options = {

        margin:0.5,

        filename:fileName + '.pdf',

        image:{
            type:'jpeg',
            quality:1
        },

        html2canvas:{
            scale:2
        },

        jsPDF:{
            unit:'in',
            format:'a4',
            orientation:'portrait'
        }
    };

    html2pdf()
        .set(options)
        .from(element)
        .save();
}