const guides = JSON.parse(localStorage.getItem("guides")) || {

    fax: "תוכן מדריך פקס",
    sms: "תוכן מדריך SMS",
    recordings: "תוכן מדריך הקלטות"
    
    };
    
    const select = document.getElementById("guideSelect");
    const editor = document.getElementById("editor");
    
    loadGuide();
    
    select.addEventListener("change", loadGuide);
    
    function loadGuide(){
    
        editor.value =
            guides[select.value];
    
    }
    
    function saveGuide(){
    
        guides[select.value] =
            editor.value;
    
        localStorage.setItem(
            "guides",
            JSON.stringify(guides)
        );
    
        alert("נשמר בהצלחה");
    
    }