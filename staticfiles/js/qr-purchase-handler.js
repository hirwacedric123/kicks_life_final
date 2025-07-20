/**
 * QR Purchase Handler - Manages QR code scanning and purchase verification flow
 */

// Global variables for the verification flow
let currentQRData = null;
let selectedOrderId = null; 
let selectedPurchase = null;
let otpSessionId = null;
let otpTimer = null;
let resendTimer = null;
let currentPurchaser = null;

/**
 * Parse JWT token from QR code data
 * @param {string} token - JWT token string from QR code
 * @returns {object|null} Decoded payload or null if invalid
 */
function parseJWTFromQRCode(token) {
    try {
        console.log('Attempting to parse JWT token from QR code');
        // Split the JWT into parts
        const parts = token.split('.');
        
        if (parts.length !== 3) {
            console.error('Invalid JWT format: Token should have 3 parts');
            return null;
        }
        
        // Decode the payload (middle part)
        const payload = JSON.parse(atob(parts[1].replace(/-/g, '+').replace(/_/g, '/')));
        console.log('JWT payload decoded successfully', payload);
        
        // Check if the payload has the expected structure
        if (!payload.qr_data) {
            console.error('Invalid JWT payload: Missing qr_data');
            return null;
        }
        
        return payload.qr_data;
    } catch (error) {
        console.error('Error parsing JWT token from QR code:', error);
        // Show an error message in UI
        showError(`Could not parse QR code: ${error.message}`);
        return null;
    }
}

/**
 * Handle QR code scan result
 * @param {string} qrCodeData - Raw data from QR code scan
 */
function handleQRScan(qrCodeData) {
    console.log('QR code scanned:', qrCodeData);
    
    if (!qrCodeData) {
        showError('Empty QR code data received.');
        return;
    }
    
    // Handle the case when we get an object instead of string (from some scanners)
    if (typeof qrCodeData === 'object') {
        console.log('QR code data is an object, attempting to extract text');
        // Try to extract text property if it exists
        if (qrCodeData.text) {
            qrCodeData = qrCodeData.text;
        } else {
            // If we can't extract text, try to stringify the object
            try {
                qrCodeData = JSON.stringify(qrCodeData);
            } catch (e) {
                showError('Invalid QR code data format.');
                return;
            }
        }
    }
    
    // Try to parse as JWT first
    const parsedData = parseJWTFromQRCode(qrCodeData);
    
    if (parsedData) {
        console.log('Successfully parsed QR data as JWT', parsedData);
        // Pass the parsed data to the existing function
        fetchPurchaseDetails(parsedData);
    } else {
        // If not a JWT, try to use as-is
        console.log('Using raw QR data (non-JWT format)');
        fetchPurchaseDetails(qrCodeData);
    }
}

// Function to fetch purchase details using the QR code data
function fetchPurchaseDetails(qrData) {
    console.log(`Fetching purchase details for QR data: ${qrData}`);
    currentQRData = qrData;
    
    // Show loading in the purchase list
    document.getElementById('purchase-loading').style.display = 'block';
    document.getElementById('purchase-empty').style.display = 'none';
    
    // Clear any previous purchase list
    const purchaseListContainer = document.getElementById('purchase-list-container');
    const existingList = purchaseListContainer.querySelector('.purchase-list');
    if (existingList) {
        purchaseListContainer.removeChild(existingList);
    }
    
    // Reset the confirm button
    const confirmBtn = document.getElementById('confirm-purchase-btn');
    confirmBtn.disabled = true;
    
    // Open the popup first
    openPopup('purchase-popup');
    
    // Make API request to get purchase data
    fetchPurchasesFromAPI(qrData)
        .then(data => {
            if (data.error) {
                throw new Error(data.error);
            }
            updatePurchaseList(data);
        })
        .catch(error => {
            document.getElementById('purchase-loading').style.display = 'none';
            document.getElementById('purchase-empty').style.display = 'block';
            document.getElementById('purchase-empty').innerHTML = `
                <p>❌ Error retrieving purchases:</p>
                <p>${error.message || 'Failed to retrieve purchase data'}</p>
            `;
            console.log(`Error fetching purchases: ${error.message}`);
        });
}

// Function to fetch purchases data from the API
function fetchPurchasesFromAPI(qrData) {
    // Format the payload based on whether we received parsed JWT data or raw QR string
    let payload;
    
    if (typeof qrData === 'object' && qrData !== null) {
        // We have pre-parsed JWT data
        console.log('Using pre-parsed JWT data for API request');
        
        // Check which format our backend expects
        if (qrData.purchases) {
            // Backend expects purchases directly
            payload = qrData;
        } else {
            // Backend expects purchases wrapped in qr_data
            payload = { qr_data: qrData };
        }
    } else {
        // We have raw string data
        console.log('Using raw QR string for API request');
        payload = { qr_data: qrData };
    }
    
    console.log('Fetch purchases API payload:', payload);
    
    // Handle JWT tokens that contain purchases directly without needing API call
    if (payload.purchases && Array.isArray(payload.purchases) && payload.purchases.length > 0) {
        const directData = {
            purchases: payload.purchases,
            username: payload.username || 'Customer',
            user_id: payload.user_id || 0
        };
        
        console.log('Using direct purchase data from JWT without API call:', directData);
        return Promise.resolve(directData);
    }
      // Otherwise, make the API call
    return fetch('/auth/api/purchases/by-qr/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value
        },
        body: JSON.stringify(payload)
    })
    .then(response => {
        if (!response.ok) {
            throw new Error(`HTTP error! Status: ${response.status}`);
        }
        return response.json();
    })
    .catch(error => {
        console.error('Error fetching purchase data:', error);
        return { error: error.message || 'Failed to fetch purchase data' };
    });
}

// Function to update the purchase list in the popup
function updatePurchaseList(data) {
    document.getElementById('purchase-loading').style.display = 'none';
    
    console.log('Update purchase list with data:', data);
    
    // If data came directly from JWT, it might have a different structure
    if (!data || data.error) {
        document.getElementById('purchase-empty').style.display = 'block';
        document.getElementById('purchase-empty').innerHTML = `
            <p>❌ Error retrieving purchases:</p>
            <p>${data && data.error ? data.error : 'No purchase data available'}</p>
        `;
        return;
    }
    
    // Check for purchases in different possible data structures
    const purchases = data.purchases || (data.qr_data && data.qr_data.purchases) || [];
    const username = data.username || (data.qr_data && data.qr_data.username) || 'Customer';
    const userId = data.user_id || (data.qr_data && data.qr_data.user_id);
    
    if (!purchases || purchases.length === 0) {
        document.getElementById('purchase-empty').style.display = 'block';
        document.getElementById('purchase-empty').innerHTML = '<p>No purchases found for this QR code.</p>';
        return;
    }
    
    console.log(`Found ${purchases.length} purchases for user ${username}`);
    
    // Update popup title with username
    const popupTitle = document.querySelector('#purchase-popup .popup-title');
    if (popupTitle) {
        popupTitle.textContent = `Purchases for ${username}`;
    }
      // Create purchase list
    const purchaseList = document.createElement('ul');
    purchaseList.className = 'purchase-list';
    
    // Use the extracted purchases array
    purchases.forEach(purchase => {
        const purchaseItem = document.createElement('li');
        purchaseItem.className = 'purchase-item';
        purchaseItem.dataset.orderId = purchase.order_id;
        
        purchaseItem.innerHTML = `
            <div class="purchase-title">${purchase.product_name}</div>
            <div class="purchase-details">
                <div><strong>Order ID:</strong> ${purchase.order_id}</div>
                <div><strong>Quantity:</strong> ${purchase.quantity}</div>
                <div><strong>Vendor:</strong> ${purchase.vendor_name}</div>
            </div>
            <div class="purchase-meta">
                <div class="purchase-price">RWF${purchase.price}</div>
            </div>
        `;
        
        // Add click event to select this purchase
        purchaseItem.addEventListener('click', () => {
            // Remove selected class from all items
            document.querySelectorAll('.purchase-item').forEach(item => {
                item.classList.remove('selected');
            });
            
            // Add selected class to this item
            purchaseItem.classList.add('selected');
            
            // Store the selected purchase order ID and purchase object
            selectedOrderId = purchase.order_id;
            selectedPurchase = purchase;
            
            // Enable the confirm button
            document.getElementById('confirm-purchase-btn').disabled = false;
            
            console.log(`Selected purchase: ${purchase.product_name} (Order ID: ${purchase.order_id})`);
        });
        
        purchaseList.appendChild(purchaseItem);
    });
    
    // Replace the loading indicator with the purchase list
    const purchaseListContainer = document.getElementById('purchase-list-container');
    purchaseListContainer.appendChild(purchaseList);
      // Set up confirm button event handler
    const confirmBtn = document.getElementById('confirm-purchase-btn');
    confirmBtn.onclick = () => {
        if (selectedOrderId) {
            // Instead of AJAX/OTP, submit a POST to Django view
            submitQRCode(currentQRData, selectedOrderId);
            // Optionally close the popup
            closePopup('purchase-popup');
            // Prevent further JS flow
            return;
        }
    };
}

// Function to open the authentication popup
function openAuthPopup() {
    // Reset any previous inputs and errors
    document.getElementById('auth-username').value = '';
    document.getElementById('auth-password').value = '';
    document.getElementById('auth-error').style.display = 'none';
    
    // Set up the verify button
    document.getElementById('verify-credentials-btn').onclick = () => {
        verifyCredentials();
    };
    
    // Open the auth popup
    openPopup('auth-popup');
}

// Function to verify buyer credentials
function verifyCredentials() {
    const username = document.getElementById('auth-username').value.trim();
    const password = document.getElementById('auth-password').value.trim();
    
    if (!username || !password) {
        document.getElementById('auth-error').textContent = 'Please enter both username and password';
        document.getElementById('auth-error').style.display = 'block';
        return;
    }
    
    // Add loading state to button
    const verifyBtn = document.getElementById('verify-credentials-btn');
    const originalText = verifyBtn.textContent;
    verifyBtn.disabled = true;
    verifyBtn.innerHTML = '<div class="loading-spinner"></div> Verifying...';
    
    // Make API call to verify credentials
    fetch('/auth/api/verify-credentials/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value
        },
        body: JSON.stringify({
            username: username,
            password: password,
            user_id: currentPurchaser.id
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.error) {
            document.getElementById('auth-error').textContent = data.error;
            document.getElementById('auth-error').style.display = 'block';
            
            // Reset button
            verifyBtn.disabled = false;
            verifyBtn.textContent = originalText;
        } else if (data.success) {
            closePopup('auth-popup');
            sendOTPToUser();
        }
    })
    .catch(error => {
        document.getElementById('auth-error').textContent = 'Error verifying credentials. Please try again.';
        document.getElementById('auth-error').style.display = 'block';
        
        console.log(`Error verifying credentials: ${error.message}`);
        
        // Reset button
        verifyBtn.disabled = false;
        verifyBtn.textContent = originalText;
    });
}

// Function to send OTP to the buyer's email
function sendOTPToUser() {
    console.log(`Sending OTP to user: ${currentPurchaser.username}`);
    
    // First, set up the OTP popup
    document.getElementById('buyer-email').textContent = currentPurchaser.email || currentPurchaser.username;
    document.getElementById('otp-error').style.display = 'none';
    
    // Clear any previous OTP inputs
    const otpInputs = document.querySelectorAll('.otp-input');
    otpInputs.forEach(input => {
        input.value = '';
    });
    
    // Set up OTP input behavior
    setupOTPInputs();
    
    // Set up the verify OTP button
    document.getElementById('verify-otp-btn').onclick = () => {
        verifyOTP();
    };
    
    // Reset and start timers
    setupOTPTimers();
    
    // Set up resend button
    document.getElementById('resend-otp-btn').onclick = () => {
        resendOTP();
    };
    
    // Open the OTP popup
    openPopup('otp-popup');
    
    // Make API call to send OTP
    fetch('/auth/api/send-otp/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value
        },
        body: JSON.stringify({
            user_id: currentPurchaser.id,
            purchase_id: selectedPurchase.id || selectedOrderId
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            otpSessionId = data.session_id;
            console.log(`OTP sent successfully, session ID: ${otpSessionId}`);
        } else {
            // Handle error
            closePopup('otp-popup');
            showError(data.error || 'Failed to send OTP');
        }
    })
    .catch(error => {
        console.error('Error sending OTP:', error);
        closePopup('otp-popup');
        showError('Failed to send OTP. Please try again.');
    });
}

// Function to verify OTP
function verifyOTP() {
    // Collect OTP from inputs
    const otpInputs = document.querySelectorAll('.otp-input');
    let otp = '';
    
    otpInputs.forEach(input => {
        otp += input.value;
    });
    
    if (otp.length !== 6) {
        document.getElementById('otp-error').textContent = 'Please enter all 6 digits';
        document.getElementById('otp-error').style.display = 'block';
        return;
    }
    
    // Add loading state to button
    const verifyBtn = document.getElementById('verify-otp-btn');
    const originalText = verifyBtn.textContent;
    verifyBtn.disabled = true;
    verifyBtn.innerHTML = '<div class="loading-spinner"></div> Verifying...';
    
    // Make API call to verify OTP
    fetch('/auth/api/verify-otp/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value
        },
        body: JSON.stringify({
            user_id: currentPurchaser.id,
            otp_code: otp,
            purchase_id: selectedPurchase.id || selectedOrderId
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // Store purchase_id from response if available
            if (data.purchase_id) {
                selectedOrderId = data.purchase_id;
            }
            completePurchasePickup();
        } else {
            document.getElementById('otp-error').textContent = data.error || 'Invalid OTP. Please try again.';
            document.getElementById('otp-error').style.display = 'block';
            
            // Reset button
            verifyBtn.disabled = false;
            verifyBtn.textContent = originalText;
        }
    })
    .catch(error => {
        console.error('Error verifying OTP:', error);
        document.getElementById('otp-error').textContent = 'Error verifying OTP. Please try again.';
        document.getElementById('otp-error').style.display = 'block';
        
        // Reset button
        verifyBtn.disabled = false;
        verifyBtn.textContent = originalText;
    });
}

// Function to resend OTP
function resendOTP() {
    const resendButton = document.getElementById('resend-otp-btn');
    resendButton.disabled = true;
    resendButton.innerHTML = '<div class="loading-spinner"></div> Sending...';
    
    // Make API call to resend OTP
    fetch('/auth/api/send-otp/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value
        },
        body: JSON.stringify({
            user_id: currentPurchaser.id,
            purchase_id: selectedPurchase.id || selectedOrderId
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            otpSessionId = data.session_id;
            setupOTPTimers();
            resendButton.textContent = 'Resend OTP (60s)';
            document.getElementById('otp-error').style.display = 'none';
            console.log('OTP resent successfully');
        } else {
            resendButton.disabled = false;
            resendButton.textContent = 'Resend OTP';
            document.getElementById('otp-error').textContent = data.error || 'Failed to resend OTP';
            document.getElementById('otp-error').style.display = 'block';
        }
    })
    .catch(error => {
        console.error('Error resending OTP:', error);
        resendButton.disabled = false;
        resendButton.textContent = 'Resend OTP';
        document.getElementById('otp-error').textContent = 'Failed to resend OTP. Please try again.';
        document.getElementById('otp-error').style.display = 'block';
    });
}

// Function to complete the purchase pickup
function completePurchasePickup() {
    // Clear any timers
    if (otpTimer) clearInterval(otpTimer);
    if (resendTimer) clearInterval(resendTimer);
    
    // Close the OTP popup
    closePopup('otp-popup');
    
    // Display a success message and redirect
    showCameraStatus('Purchase pickup verified successfully! Processing...', 'success');
    
    // Make API call to complete the purchase pickup process
    const purchaseId = selectedPurchase.id || selectedOrderId;
    console.log('Completing purchase with ID:', purchaseId);
    console.log('selectedPurchase:', selectedPurchase);
    console.log('selectedOrderId:', selectedOrderId);
    
    fetch('/auth/api/complete-purchase/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value
        },
        body: JSON.stringify({
            purchase_id: purchaseId
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            console.log('Purchase pickup completed successfully!');
            
            // Show success message with payment details
            const successMessage = `Purchase confirmed! Vendor payment: RWF${data.vendor_payment}, KoraQuest commission: RWF${data.koraquest_commission}`;
            showCameraStatus(successMessage, 'success');
            
            // Show success section
            const resultSection = document.getElementById('result-section');
            if (resultSection) {
                resultSection.style.display = 'block';
                resultSection.innerHTML = `
                    <h3>✅ Purchase Completed Successfully!</h3>
                    <div style="background: white; padding: 20px; border-radius: 8px; margin-top: 15px; box-shadow: 0 2px 10px rgba(0,0,0,0.1);">
                        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 15px;">
                            <h4 style="margin: 0; color: #333;">📦 ${selectedPurchase.product_name}</h4>
                            <span style="background: #e8f5e9; color: #2e7d32; padding: 5px 12px; border-radius: 15px; font-size: 0.9em; font-weight: 500;">
                                Status: Completed
                            </span>
                        </div>
                        
                        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin: 20px 0;">
                            <div style="background: #f8f9fa; padding: 15px; border-radius: 8px;">
                                <h5 style="margin: 0 0 10px 0; color: #495057;">👤 Customer Details</h5>
                                <strong>Username:</strong> ${currentPurchaser.username}<br>
                                <strong>Order ID:</strong> <code>${selectedOrderId}</code>
                            </div>
                            <div style="background: #f8f9fa; padding: 15px; border-radius: 8px;">
                                <h5 style="margin: 0 0 10px 0; color: #495057;">📋 Payment Details</h5>
                                <strong>Total Price:</strong> RWF${selectedPurchase.price}<br>
                                <strong>Vendor Payment:</strong> RWF${data.vendor_payment}<br>
                                <strong>KoraQuest Commission:</strong> RWF${data.koraquest_commission}
                            </div>
                        </div>
                    </div>
                `;
            }
            
            // Redirect to dashboard after a short delay
            setTimeout(() => {
                window.location.href = '/auth/koraquest-dashboard/';
            }, 5000);
        } else {
            showError(data.error || 'Failed to complete purchase pickup');
            // Fall back to traditional form submission
            submitQRCode(currentQRData, selectedOrderId);
        }
    })
    .catch(error => {
        console.error('Error completing purchase pickup:', error);
        showError('Failed to complete purchase pickup. Trying alternative method...');
        // Fall back to traditional form submission
        submitQRCode(currentQRData, selectedOrderId);
    });
}

// Function to set up OTP input fields
function setupOTPInputs() {
    const otpInputs = document.querySelectorAll('.otp-input');
    
    otpInputs.forEach((input, index) => {
        // Clear previous event listeners (if any)
        input.replaceWith(input.cloneNode(true));
    });
    
    // Get fresh references after cloning
    const freshInputs = document.querySelectorAll('.otp-input');
    
    freshInputs.forEach((input, index) => {
        // Handle input
        input.addEventListener('input', function() {
            // Only allow digits
            this.value = this.value.replace(/[^0-9]/g, '');
            
            // Auto-focus next input
            if (this.value && index < freshInputs.length - 1) {
                freshInputs[index + 1].focus();
            }
            
            // Check if all inputs are filled
            checkOTPCompletion();
        });
        
        // Handle backspace
        input.addEventListener('keydown', function(e) {
            if (e.key === 'Backspace' && !this.value && index > 0) {
                freshInputs[index - 1].focus();
            }
        });
        
        // Handle paste
        input.addEventListener('paste', function(e) {
            e.preventDefault();
            
            const pasteData = (e.clipboardData || window.clipboardData).getData('text');
            const digits = pasteData.match(/\d/g);
            
            if (digits) {
                // Fill inputs with pasted digits
                freshInputs.forEach((input, idx) => {
                    if (idx < digits.length) {
                        input.value = digits[idx];
                    }
                });
                
                // Focus the next empty input or the last input
                for (let i = 0; i < freshInputs.length; i++) {
                    if (!freshInputs[i].value) {
                        freshInputs[i].focus();
                        break;
                    }
                    
                    if (i === freshInputs.length - 1) {
                        freshInputs[i].focus();
                    }
                }
                
                // Check if all inputs are filled
                checkOTPCompletion();
            }
        });
    });
    
    // Focus the first input
    if (freshInputs.length > 0) {
        freshInputs[0].focus();
    }
}

// Check if all OTP inputs are filled
function checkOTPCompletion() {
    const otpInputs = document.querySelectorAll('.otp-input');
    let isComplete = true;
    
    otpInputs.forEach(input => {
        if (!input.value) {
            isComplete = false;
        }
    });
    
    document.getElementById('verify-otp-btn').disabled = !isComplete;
}

// Set up OTP timers
function setupOTPTimers() {
    // Clear any existing timers
    if (otpTimer) clearInterval(otpTimer);
    if (resendTimer) clearInterval(resendTimer);
    
    // Set up OTP expiration timer - 5 minutes
    let otpTimeLeft = 5 * 60; // 5 minutes in seconds
    const timerElement = document.getElementById('timer-countdown');
    
    updateTimerDisplay(otpTimeLeft, timerElement);
    
    otpTimer = setInterval(() => {
        otpTimeLeft--;
        updateTimerDisplay(otpTimeLeft, timerElement);
        
        if (otpTimeLeft <= 0) {
            clearInterval(otpTimer);
            document.getElementById('otp-error').textContent = 'OTP expired. Please request a new one.';
            document.getElementById('otp-error').style.display = 'block';
            document.getElementById('verify-otp-btn').disabled = true;
        }
    }, 1000);
    
    // Set up resend timer - 60 seconds
    let resendTimeLeft = 60; // 60 seconds
    const resendButton = document.getElementById('resend-otp-btn');
    const resendCountdown = document.getElementById('resend-countdown');
    
    resendButton.disabled = true;
    resendCountdown.textContent = resendTimeLeft;
    
    resendTimer = setInterval(() => {
        resendTimeLeft--;
        resendCountdown.textContent = resendTimeLeft;
        
        if (resendTimeLeft <= 0) {
            clearInterval(resendTimer);
            resendButton.disabled = false;
            resendButton.textContent = 'Resend OTP';
        }
    }, 1000);
}

// Helper to update timer display
function updateTimerDisplay(seconds, element) {
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = seconds % 60;
    element.textContent = `${minutes.toString().padStart(2, '0')}:${remainingSeconds.toString().padStart(2, '0')}`;
}

/**
 * Display error message to the user
 * @param {string} message - Error message to display
 */
function showError(message) {
    // Close any open popups first
    const popups = document.querySelectorAll('.popup-container');
    popups.forEach(popup => {
        popup.style.display = 'none';
    });
    
    // Show camera status with error
    if (typeof showCameraStatus === 'function') {
        showCameraStatus(message, 'error');
    } else {
        console.error(message);
        // Fallback if showCameraStatus isn't available
        alert('Error: ' + message);
    }
}
