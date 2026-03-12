async function loadProgress(){

    const res = await fetch("/dashboard-stats")
    const data = await res.json()

    // SMS
    document.getElementById("sms-percent").innerText = data.sms_percent + "%"
    document.getElementById("sms-progress").style.width = data.sms_percent + "%"

    // BOT
    document.getElementById("bot-percent").innerText = data.bot_percent + "%"
    document.getElementById("bot-progress").style.width = data.bot_percent + "%"

}

loadProgress()