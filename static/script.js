// ===============================
// Elements
// ===============================

const output = document.getElementById("output");
const status = document.getElementById("status");
const language = document.getElementById("language");

const SpeechRecognition =
window.SpeechRecognition || window.webkitSpeechRecognition;

let recognition;
let isRecording = false;


// ===============================
// Live Speech Recognition
// ===============================

if (SpeechRecognition) {

    recognition = new SpeechRecognition();

    recognition.continuous = true;
    recognition.interimResults = true;

    document.getElementById("start").onclick = function () {

        if (isRecording) return;

        recognition.lang = language.value;

        output.value = "";

        recognition.start();

    };

    document.getElementById("stop").onclick = function () {

        recognition.stop();

    };

    recognition.onstart = function () {

        isRecording = true;

        if(status){
            status.innerHTML = "🟢 Listening...";
            status.style.color = "green";
        }

    };

    recognition.onend = function () {

        isRecording = false;

        if(status){
            status.innerHTML = "🔴 Recording Stopped";
            status.style.color = "red";
        }

    };

    recognition.onresult = function (event) {

        let transcript = "";

        for (let i = 0; i < event.results.length; i++) {

            transcript += event.results[i][0].transcript + " ";

        }

        output.value = transcript;

        updateCounter();

    };

    recognition.onerror = function (event) {

        alert("Speech Recognition Error : " + event.error);

    };

}



/// ===============================
// Upload Audio
// ===============================

function uploadAudio() {

    const file =
        document.getElementById("audioFile").files[0];

    if (!file) {

        alert("Please select an audio file.");

        return;

    }

    output.value =
        "Converting audio... Please wait...";

    const formData =
        new FormData();

    formData.append(
        "audio",
        file
    );

    fetch("/convert", {

        method: "POST",

        body: formData

    })

    .then(response => {

        if (!response.ok) {

            throw new Error(
                "Server Error"
            );

        }

        return response.json();

    })

    .then(data => {

        console.log(data);

        output.value =
            data.text;

        updateCounter();

        // Save to History ONLY ONCE
        saveUploadToHistory(
            data.text
        );

    })

    .catch(error => {

        console.error(error);

        output.value =
            "Conversion Failed.\n\n" +
            error.message;

    });

}


// ===============================
// SAVE UPLOAD AUDIO TO HISTORY
// ===============================

function saveUploadToHistory(text) {

    if (
        !text ||
        text.trim() === ""
    ) {

        return;

    }

    fetch("/save-history", {

        method: "POST",

        headers: {

            "Content-Type":
                "application/json"

        },

        body: JSON.stringify({

            text:
                text.trim(),

            source:
                "Upload Audio"

        })

    })

    .then(response => {

        return response.json();

    })

    .then(data => {

        if (data.success) {

            console.log(
                "Upload Audio saved to History."
            );

        }

        else {

            console.error(
                "History Error:",
                data.message
            );

        }

    })

    .catch(error => {

        console.error(
            "History Save Error:",
            error
        );

    });

}


// ===============================
// Copy
// ===============================
// ===============================
// Copy
// ===============================


// ===============================
// Copy
// ===============================

function copyText() {

    if (output.value.trim() == "") {

        alert("Nothing to copy.");

        return;

    }

    navigator.clipboard.writeText(output.value);

    alert("Copied Successfully.");

}


// ===============================
// Download
// ===============================

function downloadText() {

    if (output.value.trim() == "") {

        alert("Nothing to download.");

        return;

    }

    const blob = new Blob([output.value], {

        type: "text/plain"

    });

    const link = document.createElement("a");

    link.href = URL.createObjectURL(blob);

    link.download = "SpeechText.txt";

    link.click();

}


// ===============================
// Clear
// ===============================

function clearText() {

    output.value = "";

    if(status){

        status.innerHTML = "🔴 Ready";

        status.style.color = "red";

    }

    updateCounter();

}


// ===============================
// Word Counter
// ===============================

function updateCounter(){

    const counter = document.getElementById("counter");

    if(counter){

        const text = output.value.trim();

        const words = text === "" ? 0 : text.split(/\s+/).length;

        const chars = output.value.length;

        counter.innerHTML =
        "Words : " + words + " | Characters : " + chars;

    }

}

if(output){

    output.addEventListener("input", updateCounter);

}