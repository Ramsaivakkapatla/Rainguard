// ======================================================
// RAINGUARD VOICE MODULE
// ======================================================

let recognition = null;

let recognitionSupported = false;

let recognitionAttempts = 0;

let successfulRecognitions = 0;

let voiceBusy = false;


// ======================================================
// INITIALIZE SPEECH RECOGNITION
// ======================================================

function initializeVoiceRecognition() {

    const SpeechRecognition =
        window.SpeechRecognition ||
        window.webkitSpeechRecognition;


    if (!SpeechRecognition) {

        recognitionSupported = false;

        updateVoiceStatus(
            "⚠️ Voice recognition is not supported by this browser."
        );

        return false;

    }


    recognitionSupported = true;


    recognition =
        new SpeechRecognition();


    // Telugu

    recognition.lang =
        "te-IN";


    recognition.continuous =
        false;


    recognition.interimResults =
        false;


    recognition.maxAlternatives =
        1;



    // ==================================================
    // LISTENING STARTED
    // ==================================================

    recognition.onstart =
        function () {

            voiceBusy =
                true;


            updateVoiceStatus(
                "🎤 Listening... Please say \"అవును\" when you understand."
            );


            const button =
                document.getElementById(
                    "voice-button"
                );


            if (button) {

                button.disabled =
                    true;

                button.textContent =
                    "🎤 Listening...";

            }

        };



    // ==================================================
    // RESULT
    // ==================================================

    recognition.onresult =
        function (event) {


            recognitionAttempts++;


            const transcript =
                event
                    .results[0][0]
                    .transcript
                    .trim();


            successfulRecognitions++;


            displayRecognizedSpeech(
                transcript
            );


            updateVoiceStatus(
                "✅ Speech recognized"
            );


            checkComprehension(
                transcript
            );

        };



    // ==================================================
    // ERROR
    // ==================================================

    recognition.onerror =
        function (event) {


            recognitionAttempts++;


            console.log(
                "Voice recognition error:",
                event.error
            );


            voiceBusy =
                false;


            let message =
                "⚠️ Voice recognition failed.";


            if (
                event.error ===
                "not-allowed"
            ) {

                message =
                    "🎤 Microphone permission was denied.";

            }


            else if (
                event.error ===
                "no-speech"
            ) {

                message =
                    "🎤 No speech detected. Please try again.";

            }


            else if (
                event.error ===
                "audio-capture"
            ) {

                message =
                    "🎤 Microphone could not be accessed.";

            }


            updateVoiceStatus(
                message
            );


            showVoiceFallback();


            resetVoiceButton();

        };



    // ==================================================
    // RECOGNITION END
    // ==================================================

    recognition.onend =
        function () {

            voiceBusy =
                false;

            resetVoiceButton();

            console.log(
                "Voice recognition ended."
            );

        };


    return true;

}



// ======================================================
// START VOICE REGISTRATION
// ======================================================

function startVoiceRegistration() {


    hideVoiceFallback();


    const comprehension =
        document.getElementById(
            "comprehensionResult"
        );


    const recognized =
        document.getElementById(
            "recognizedSpeech"
        );


    if (comprehension) {

        comprehension.style.display =
            "none";

    }


    if (recognized) {

        recognized.style.display =
            "none";

    }



    // Browser doesn't support recognition

    if (!recognitionSupported) {

        showVoiceFallback();

        speakPolicyDisclosure();

        return;

    }



    // Already listening

    if (voiceBusy) {

        return;

    }



    // Speak policy first

    speakPolicyDisclosure();



    /*
     * Wait for the Telugu policy to finish.
     * 4 seconds is suitable for the current
     * prototype policy message.
     */

    setTimeout(
        function () {

            startListening();

        },
        4000
    );

}



// ======================================================
// SPEAK POLICY DISCLOSURE
// ======================================================

function speakPolicyDisclosure() {


    if (
        !("speechSynthesis" in window)
    ) {

        showVoiceFallback();

        return;

    }


    window.speechSynthesis.cancel();


    const message =

        "రెయిన్ గార్డ్ రైతు పంట బీమా. " +

        "మీ ప్రాంతంలో వర్షపాతం నిర్ణయించిన స్థాయి కంటే తక్కువగా ఉంటే, " +

        "బీమా చెల్లింపు ఆటోమేటిక్‌గా మీ ఆఫ్‌లైన్ వాలెట్‌లో జమ అవుతుంది. " +

        "బీమా పాలసీని అర్థం చేసుకున్న తర్వాత మాత్రమే అది అమలులోకి వస్తుంది. " +

        "పాలసీ అర్థమైతే అవును అని చెప్పండి.";



    const speech =
        new SpeechSynthesisUtterance(
            message
        );


    speech.lang =
        "te-IN";


    speech.rate =
        0.85;


    speech.pitch =
        1;



    speech.onstart =
        function () {

            updateVoiceStatus(
                "🔊 Playing policy explanation in Telugu..."
            );

        };


    speech.onend =
        function () {

            updateVoiceStatus(
                "🎤 Get ready to answer..."
            );

        };


    speech.onerror =
        function () {

            console.log(
                "Speech synthesis error."
            );

            updateVoiceStatus(
                "⚠️ Could not play the voice policy."
            );

        };


    window.speechSynthesis.speak(
        speech
    );

}



// ======================================================
// START LISTENING
// ======================================================

function startListening() {


    if (!recognition) {

        showVoiceFallback();

        return;

    }


    if (voiceBusy) {

        return;

    }


    updateVoiceStatus(
        "🎤 Please answer \"అవును\"..."
    );


    try {

        recognition.start();

    }

    catch (error) {

        console.log(
            "Recognition could not start:",
            error
        );


        voiceBusy =
            false;


        showVoiceFallback();

        resetVoiceButton();

    }

}



// ======================================================
// COMPREHENSION CHECK
// ======================================================

function checkComprehension(
    transcript
) {


    const text =
        transcript
            .toLowerCase()
            .trim();



    const positiveWords = [

        "అవును",

        "అర్థమైంది",

        "అర్థమయ్యింది",

        "yes",

        "understood",

        "ok",

        "okay"

    ];



    let understood =
        false;



    for (
        const word of positiveWords
    ) {

        if (
            text.includes(word)
        ) {

            understood =
                true;

            break;

        }

    }



    if (understood) {

        showComprehensionSuccess();

    }

    else {

        showComprehensionRetry();

    }

}



// ======================================================
// SUCCESS
// ======================================================

function showComprehensionSuccess() {


    const box =
        document.getElementById(
            "comprehensionResult"
        );


    if (!box) {

        return;

    }


    box.style.display =
        "block";


    box.className =
        "success-box";


    box.innerHTML = `

        <h3>
            ✅ Policy Understanding Confirmed
        </h3>

        <p>
            Your response indicates that you
            understood the insurance policy.
        </p>

        <p>
            Voice registration completed successfully.
        </p>

    `;


    updateVoiceStatus(
        "✅ Voice registration completed"
    );


    resetVoiceButton();

}



// ======================================================
// RETRY
// ======================================================

function showComprehensionRetry() {


    const box =
        document.getElementById(
            "comprehensionResult"
        );


    if (!box) {

        return;

    }


    box.style.display =
        "block";


    box.className =
        "warning-box";


    box.innerHTML = `

        <h3>
            ⚠️ Please try again
        </h3>

        <p>
            We could not confirm your understanding.
        </p>

        <p>
            Please listen again and say
            <strong>\"అవును\"</strong>
            when you understand.
        </p>

        <button
            type="button"
            class="secondary-button"
            onclick="startVoiceRegistration()"
        >

            🔊 Listen Again

        </button>

    `;


    updateVoiceStatus(
        "⚠️ Understanding not confirmed"
    );


    resetVoiceButton();

}



// ======================================================
// FALLBACK
// ======================================================

function showVoiceFallback() {


    const fallback =
        document.getElementById(
            "voiceFallback"
        );


    if (!fallback) {

        return;

    }


    fallback.style.display =
        "block";


    fallback.innerHTML = `

        <div class="warning-box">

            <h3>
                ⚠️ Voice Recognition Unavailable
            </h3>

            <p>
                Your browser or device could not
                recognize speech.
            </p>

            <button
                type="button"
                class="secondary-button"
                onclick="manualComprehension()"
            >

                ✓ I Understand

            </button>

        </div>

    `;

}



// ======================================================
// HIDE FALLBACK
// ======================================================

function hideVoiceFallback() {


    const fallback =
        document.getElementById(
            "voiceFallback"
        );


    if (fallback) {

        fallback.style.display =
            "none";

    }

}



// ======================================================
// MANUAL FALLBACK
// ======================================================

function manualComprehension() {


    showComprehensionSuccess();

}



// ======================================================
// DISPLAY TRANSCRIPT
// ======================================================

function displayRecognizedSpeech(
    transcript
) {


    const output =
        document.getElementById(
            "recognizedSpeech"
        );


    if (!output) {

        return;

    }


    output.style.display =
        "block";


    /*
     * textContent is used instead of
     * innerHTML for user speech.
     */

    output.innerHTML = `

        <strong>
            🎤 You said:
        </strong>

        <p></p>

    `;


    output
        .querySelector("p")
        .textContent =
        transcript;

}



// ======================================================
// STATUS
// ======================================================

function updateVoiceStatus(
    message
) {


    const status =
        document.getElementById(
            "voiceStatus"
        );


    if (status) {

        status.textContent =
            message;

    }

}



// ======================================================
// RESET BUTTON
// ======================================================

function resetVoiceButton() {


    const button =
        document.getElementById(
            "voice-button"
        );


    if (!button) {

        return;

    }


    button.disabled =
        false;


    button.textContent =
        "🔊 Start Voice Registration";

}



// ======================================================
// ACCURACY
// ======================================================

function getVoiceAccuracy() {


    if (
        recognitionAttempts === 0
    ) {

        return 0;

    }


    return (
        successfulRecognitions /
        recognitionAttempts
    ) * 100;

}



// ======================================================
// EXPOSE FUNCTIONS
// ======================================================

window.startVoiceRegistration =
    startVoiceRegistration;


window.startListening =
    startListening;


window.manualComprehension =
    manualComprehension;


window.getVoiceAccuracy =
    getVoiceAccuracy;



// ======================================================
// INITIALIZE
// ======================================================

document.addEventListener(
    "DOMContentLoaded",
    function () {

        initializeVoiceRecognition();

    }
);