const video = document.getElementById('video');
const canvas = document.getElementById('canvas');
const capturedPhoto = document.getElementById('captured-photo');
const startCameraBtn = document.getElementById('start-camera');
const captureBtn = document.getElementById('capture-btn');
const retakeBtn = document.getElementById('retake-btn');
const sendBtn = document.getElementById('send-btn');
const liveAnalysisBtn = document.getElementById('live-analysis-btn');
const loading = document.getElementById('loading');
const results = document.getElementById('results');
const resultsContent = document.getElementById('results-content');
const error = document.getElementById('error');

let stream = null;
let photoBlob = null;
let liveAnalysisInterval = null;
let isLiveAnalysisActive = false;

// Start camera
startCameraBtn.addEventListener('click', async () => {
    try {
        hideError();

        // Check if getUserMedia is available
        if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
            showError('Camera access is not supported in this browser. Please use a modern browser like Chrome, Firefox, or Safari.');
            return;
        }

        stream = await navigator.mediaDevices.getUserMedia({
            video: {
                facingMode: 'user',
                width: { ideal: 1280 },
                height: { ideal: 720 }
            }
        });

        video.srcObject = stream;
        video.style.display = 'block';
        capturedPhoto.style.display = 'none';

        startCameraBtn.disabled = true;
        captureBtn.disabled = false;
        liveAnalysisBtn.disabled = false;
        retakeBtn.style.display = 'none';
        sendBtn.style.display = 'none';
        results.style.display = 'none';
    } catch (err) {
        let errorMessage = 'Error accessing camera: ';

        if (err.name === 'NotAllowedError' || err.name === 'PermissionDeniedError') {
            errorMessage = 'Camera permission denied. Please:\n' +
                '1. Click "Allow" when your browser asks for camera permission\n' +
                '2. Check your browser settings to ensure camera access is allowed\n' +
                '3. Make sure no other application is using your camera\n' +
                '4. Try refreshing the page and clicking "Start Camera" again';
        } else if (err.name === 'NotFoundError' || err.name === 'DevicesNotFoundError') {
            errorMessage = 'No camera found. Please connect a camera and try again.';
        } else if (err.name === 'NotReadableError' || err.name === 'TrackStartError') {
            errorMessage = 'Camera is already in use by another application. Please close other apps using the camera and try again.';
        } else {
            errorMessage += err.message;
        }

        showError(errorMessage);
        console.error('Error accessing camera:', err);
    }
});

// Capture photo
captureBtn.addEventListener('click', () => {
    // Stop live analysis if active
    stopLiveAnalysis();

    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;

    const ctx = canvas.getContext('2d');
    // Flip the canvas horizontally to match the mirrored video display
    ctx.translate(canvas.width, 0);
    ctx.scale(-1, 1);
    ctx.drawImage(video, 0, 0);

    canvas.toBlob((blob) => {
        photoBlob = blob;
        const photoUrl = URL.createObjectURL(blob);
        capturedPhoto.src = photoUrl;

        video.style.display = 'none';
        capturedPhoto.style.display = 'block';

        captureBtn.style.display = 'none';
        retakeBtn.style.display = 'inline-block';
        sendBtn.style.display = 'inline-block';
    }, 'image/jpeg', 0.95);
});

// Retake photo
retakeBtn.addEventListener('click', () => {
    capturedPhoto.style.display = 'none';
    video.style.display = 'block';

    captureBtn.style.display = 'inline-block';
    retakeBtn.style.display = 'none';
    sendBtn.style.display = 'none';
    results.style.display = 'none';

    if (photoBlob) {
        URL.revokeObjectURL(capturedPhoto.src);
        photoBlob = null;
    }
});

// Send photo to API
sendBtn.addEventListener('click', async () => {
    if (!photoBlob) {
        showError('No photo captured');
        return;
    }

    // Stop live analysis if active
    stopLiveAnalysis();

    try {
        hideError();
        loading.style.display = 'block';
        results.style.display = 'none';
        sendBtn.disabled = true;

        const formData = new FormData();
        formData.append('file', photoBlob, 'photo.jpg');

        const response = await fetch('https://192.168.0.237:8000/api/classify', {
            method: 'POST',
            mode: 'cors', // Explicitly request CORS
            headers: {
                'accept': 'application/json'
                // Don't set Content-Type for FormData - browser will set it with boundary
            },
            body: formData
        });

        if (!response.ok) {
            const errorText = await response.text();
            throw new Error(`HTTP error! status: ${response.status}, message: ${errorText}`);
        }

        const data = await response.json();
        console.log('API Response:', data);
        displayResults(data);

    } catch (err) {
        let errorMsg = 'Error sending photo: ' + err.message;

        // Check for CORS errors
        if (err.message.includes('Failed to fetch') || err.message.includes('CORS') || err.name === 'TypeError') {
            errorMsg = 'CORS Error: The API server needs to include CORS headers.\n\n' +
                'Please add these headers to your API response:\n' +
                'Access-Control-Allow-Origin: *\n' +
                'Access-Control-Allow-Methods: POST\n' +
                'Access-Control-Allow-Headers: accept, Content-Type\n\n' +
                'Or if using FastAPI, add CORS middleware.';
        }

        showError(errorMsg);
        console.error('Error sending photo:', err);
        console.error('Full error:', err);
    } finally {
        loading.style.display = 'none';
        sendBtn.disabled = false;
    }
});

// Live Analysis - Send frame to API at 2 requests per second
let isProcessingRequest = false;

async function sendFrameToAPI() {
    if (isProcessingRequest || !stream || video.readyState !== video.HAVE_ENOUGH_DATA) {
        return;
    }

    try {
        isProcessingRequest = true;

        // Capture current frame from video
        canvas.width = video.videoWidth;
        canvas.height = video.videoHeight;

        const ctx = canvas.getContext('2d');
        ctx.translate(canvas.width, 0);
        ctx.scale(-1, 1);
        ctx.drawImage(video, 0, 0);

        // Convert to blob
        const blob = await new Promise((resolve) => {
            canvas.toBlob(resolve, 'image/jpeg', 0.85);
        });

        if (!blob) {
            isProcessingRequest = false;
            return;
        }

        // Send to API
        const formData = new FormData();
        formData.append('file', blob, 'frame.jpg');

        const response = await fetch('https://192.168.0.237:8000/api/classify', {
            method: 'POST',
            mode: 'cors',
            headers: {
                'accept': 'application/json'
            },
            body: formData
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const data = await response.json();
        displayResults(data);
        results.style.display = 'block';

    } catch (err) {
        // Silently handle errors in live mode to avoid spam
        console.error('Live analysis error:', err);
    } finally {
        isProcessingRequest = false;
    }
}

// Stop live analysis helper function
function stopLiveAnalysis() {
    if (isLiveAnalysisActive) {
        if (liveAnalysisInterval) {
            clearInterval(liveAnalysisInterval);
            liveAnalysisInterval = null;
        }
        isLiveAnalysisActive = false;
        liveAnalysisBtn.textContent = 'Start Live Analysis';
        liveAnalysisBtn.classList.remove('btn-stop');
        liveAnalysisBtn.classList.add('btn-live');
    }
}

// Toggle live analysis
liveAnalysisBtn.addEventListener('click', () => {
    if (isLiveAnalysisActive) {
        // Stop live analysis
        stopLiveAnalysis();
    } else {
        // Start live analysis - 1 request per second = every 1000ms
        if (!stream) {
            showError('Please start the camera first');
            return;
        }

        isLiveAnalysisActive = true;
        liveAnalysisBtn.textContent = 'Stop Live Analysis';
        liveAnalysisBtn.classList.remove('btn-live');
        liveAnalysisBtn.classList.add('btn-stop');

        // Show results section
        results.style.display = 'block';

        // Start sending frames at 1 request per second (every 1000ms)
        liveAnalysisInterval = setInterval(() => {
            sendFrameToAPI();
        }, 500);

        // Send first frame immediately
        sendFrameToAPI();
    }
});

// Display results
function displayResults(data) {
    results.style.display = 'block';

    const issues = [];
    const resultItems = [];

    // Map possible field names from API to display labels
    // Handle both snake_case and different field name variations
    const fieldMappings = [
        /*{
            keys: ['is_valid_photo'],
            label: 'Is Valid Photo',
            invert: false // For 'not_rotated', if true then it's good (not rotated = good)
        }*/
        {
            keys: ['no_glasses', 'is_valid', 'valid', 'has_glasses'],
            label: 'Nothing on the face(no glasses, no mask)',
            invert: false // true means glasses are bad, false means no glasses is good
        },
        {
            keys: ['is_centered', 'centered', 'center'],
            label: 'Face Is Centered',
            invert: false
        },
        {
            keys: ['open_eye_status', 'eyes_open', 'open_eyes', 'eye_status'],
            label: 'Open Eye Status',
            invert: false
        },
        {
            keys: ['eyes_centered'],
            label: 'Eyes Are Centered',
            invert: false
        },
        {
            keys: ['is_vertical_straight', 'not_rotated', 'is_rotated', 'vertical_straight', 'rotated'],
            label: 'Is Vertical Straight',
            invert: false // For 'not_rotated', if true then it's good (not rotated = good)
        },
        {
            keys: ['is_bg_uniform'],
            label: 'Is Background Color Uniform',
            invert: false // For 'not_rotated', if true then it's good (not rotated = good)
        },
        {
            keys: ['is_bg_bright'],
            label: 'Is Background Color Bright',
            invert: false // For 'not_rotated', if true then it's good (not rotated = good)
        },


    ];

    fieldMappings.forEach(mapping => {
        let value = null;
        let foundKey = null;

        // Try to find the value using any of the possible keys
        for (const key of mapping.keys) {
            if (data.hasOwnProperty(key)) {
                value = data[key];
                foundKey = key;
                break;
            }
        }

        // If not found, try case-insensitive search
        if (value === null) {
            const dataKeys = Object.keys(data);
            for (const key of mapping.keys) {
                const found = dataKeys.find(k => k.toLowerCase() === key.toLowerCase());
                if (found !== undefined) {
                    value = data[found];
                    foundKey = found;
                    break;
                }
            }
        }

        // Handle special case: if key is 'not_rotated', invert the logic
        if (foundKey === 'not_rotated') {
            value = value === true; // not_rotated=true means it's straight (good)
        } else if (foundKey === 'is_rotated' || foundKey === 'rotated') {
            value = value === false; // is_rotated=false means it's straight (good)
        }

        // If still not found, show unknown
        if (value === null) {
            value = 'unknown';
        }

        const pass = value === true;
        if (!pass && value !== 'unknown') {
            issues.push(mapping.label);
        }

        const statusIcon = value === 'unknown' ? '?' : (pass ? '✓' : '✗');
        const statusText = value === 'unknown' ? 'Unknown' : (pass ? 'Pass' : 'Fail');
        const statusClass = value === 'unknown' ? 'fail' : (pass ? 'pass' : 'fail');

        // Check if screen is small (phone) or large (tablet/laptop)
        const isSmallScreen = window.innerWidth <= 768;
        const textSpan = isSmallScreen ? '' : `<span class="result-text">${statusText}</span>`;

        resultItems.push(`
            <div class="result-item ${statusClass}">
                <span class="result-label">${mapping.label}:</span>
                <span class="result-value ${statusClass}">
                    <span class="result-icon">${statusIcon}</span>${textSpan}
                </span>
            </div>
        `);
    });

    resultsContent.innerHTML = resultItems.join('');

    // Add report_info if available
    if (data.report_info) {
        let reportInfoHtml = '<div class="report-info" style="margin-top: 20px; padding: 15px; background: #e7f3ff; border-radius: 8px; border-left: 4px solid #2196F3;">';
        reportInfoHtml += '<h3 style="color: #1976D2; margin-bottom: 15px; font-size: 1.2em;">Recommendations</h3>';

        const adviceItems = [];

        if (data.report_info['face center displacement']) {
            const displacement = data.report_info['face center displacement'];
            const xDisplacement = Math.abs(displacement[0]);
            const yDisplacement = Math.abs(displacement[1]);

            // Add advice for face centering
            if (xDisplacement > 20 || yDisplacement > 20) {
                let advice = '💡 <strong>Advice:</strong> ';
                if (xDisplacement > 20) {
                    if (displacement[0] > 0) {
                        advice += 'Move your face slightly to the left. ';
                    } else {
                        advice += 'Move your face slightly to the right. ';
                    }
                }
                if (yDisplacement > 20) {
                    if (displacement[1] > 0) {
                        advice += 'Move your face slightly up. ';
                    } else {
                        advice += 'Move your face slightly down. ';
                    }
                }
                advice += 'Try to center your face in the frame.';
                adviceItems.push(advice);
            } else {
                adviceItems.push('✓ Face is well-centered in the frame.');
            }
        }

        if (data.report_info['head tilt'] !== undefined) {
            const headTilt = data.report_info['head tilt'];
            const tiltDegrees = Math.abs(headTilt - 180); // Calculate deviation from straight (180°)

            // Add advice for head tilt
            if (tiltDegrees > 5) {
                let advice = '💡 <strong>Advice:</strong> ';
                if (headTilt < 175) {
                    advice += 'Tilt your head slightly to the right to straighten it. ';
                } else if (headTilt > 185) {
                    advice += 'Tilt your head slightly to the left to straighten it. ';
                }
                advice += 'Keep your head straight and level for the best photo.';
                adviceItems.push(advice);
            } else {
                adviceItems.push('✓ Head is straight and properly aligned.');
            }
        }

        // Add advice section if there are any advice items
        if (adviceItems.length > 0) {
            reportInfoHtml += '<ul style="list-style: none; padding-left: 0; margin: 0;">';
            adviceItems.forEach(advice => {
                reportInfoHtml += `<li style="margin-bottom: 8px; padding-left: 0;">${advice}</li>`;
            });
            reportInfoHtml += '</ul>';
        }

        reportInfoHtml += '</div>';
        resultsContent.innerHTML += reportInfoHtml;
    }

    // Add success message if all checks pass
    if (issues.length === 0) {
        const successHtml = `
            <div class="issues-list" style="background: #d4edda; border-left-color: #28a745;">
                <h3 style="color: #155724;">✓ All checks passed!</h3>
                <p style="color: #155724; margin-top: 10px;">Your photo meets all the requirements.</p>
            </div>
        `;
        resultsContent.innerHTML += successHtml;
    }
}

// Error handling
function showError(message) {
    // Preserve line breaks in error messages
    error.innerHTML = message.split('\n').map(line => line.trim()).filter(line => line).join('<br>');
    error.style.display = 'block';
    // Scroll to error
    error.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
}

function hideError() {
    error.style.display = 'none';
}

// Cleanup on page unload
window.addEventListener('beforeunload', () => {
    if (liveAnalysisInterval) {
        clearInterval(liveAnalysisInterval);
    }
    if (stream) {
        stream.getTracks().forEach(track => track.stop());
    }
    if (photoBlob) {
        URL.revokeObjectURL(capturedPhoto.src);
    }
});

