// QR Scan Handler - Manages QR code scanning and purchase verification flow

// Global variables for the verification flow
let currentQRData = null;
let selectedPurchaseId = null;
let selectedPurchase = null;  // Store the selected purchase object
let otpSessionId = null;
let otpTimer = null;
let resendTimer = null;
let currentPurchaser = null;  // Store purchaser information

// Function to fetch purchase details using the QR code data
function fetchPurchaseDetails(qrData) {
    debugLog(`Fetching purchase details for QR data: ${qrData}`);
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
            debugLog(`Error fetching purchases: ${error.message}`);
        });
}

// Function to fetch purchases data from the API
function fetchPurchasesFromAPI(qrData) {
    return fetch('/auth/api/purchases/by-qr/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value
        },
        body: JSON.stringify({ qr_data: qrData })
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
    
    if (!data || data.error || !data.purchases || data.purchases.length === 0) {
        document.getElementById('purchase-empty').style.display = 'block';
        return;
    }
    
    // Update popup title with username
    const popupTitle = document.querySelector('#purchase-popup .popup-title');
    if (popupTitle) {
        popupTitle.textContent = `Purchases for ${data.username}`;
    }
    
    // Create purchase list
    const purchaseList = document.createElement('ul');
    purchaseList.className = 'purchase-list';
    
    data.purchases.forEach(purchase => {
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
            selectedPurchaseId = purchase.order_id;
            selectedPurchase = purchase;
            
            // Enable the confirm button
            document.getElementById('confirm-purchase-btn').disabled = false;
            
            debugLog(`Selected purchase: ${purchase.product_name} (Order ID: ${purchase.order_id})`);
        });
        
        purchaseList.appendChild(purchaseItem);
    });
    
    // Replace the loading indicator with the purchase list
    const purchaseListContainer = document.getElementById('purchase-list-container');
    purchaseListContainer.appendChild(purchaseList);
    
    // Set up confirm button event handler
    const confirmBtn = document.getElementById('confirm-purchase-btn');
    confirmBtn.onclick = () => {
        if (selectedPurchaseId) {
            // Store the user info for later steps
            currentPurchaser = {
                id: data.user_id,
                username: data.username
            };
            
            closePopup('purchase-popup');
            openAuthPopup();
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
        
        debugLog(`Error verifying credentials: ${error.message}`);
        
        // Reset button
        verifyBtn.disabled = false;
        verifyBtn.textContent = originalText;
    });
}

// Function to send OTP to the buyer's email
function sendOTPToUser() {
    debugLog(`Sending OTP to user: ${currentPurchaser.username}`);
    
    // First, set up the OTP popup
    document.getElementById('buyer-email').textContent = currentPurchaser.username;
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
            purchase_id: selectedPurchaseId
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            otpSessionId = data.session_id;
            debugLog(`OTP sent successfully, session ID: ${otpSessionId}`);
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
            purchase_id: selectedPurchaseId
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
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
            purchase_id: selectedPurchaseId
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            otpSessionId = data.session_id;
            setupOTPTimers();
            resendButton.textContent = 'Resend OTP (60s)';
            document.getElementById('otp-error').style.display = 'none';
            debugLog('OTP resent successfully');
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
    showCameraStatus('Purchase pickup verified successfully! Redirecting...', 'success');
    
    // Make API call to complete the purchase pickup process
    fetch('/auth/api/complete-purchase/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value
        },
        body: JSON.stringify({
            purchase_id: selectedPurchaseId
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            debugLog('Purchase pickup completed successfully!');
            
            // Show success message with payment details
            const successMessage = `Purchase confirmed! Vendor payment: RWF${data.vendor_payment}, KoraQuest commission: RWF${data.koraquest_commission}`;
            showCameraStatus(successMessage, 'success');
            
            // Redirect to dashboard after a short delay
            setTimeout(() => {
                window.location.href = '/auth/koraquest-dashboard/';
            }, 3000);
        } else {
            showError(data.error || 'Failed to complete purchase pickup');
            // Fall back to traditional form submission
            submitQRCode(currentQRData, selectedPurchaseId);
        }
    })
    .catch(error => {
        console.error('Error completing purchase pickup:', error);
        showError('Failed to complete purchase pickup. Trying alternative method...');
        // Fall back to traditional form submission
        submitQRCode(currentQRData, selectedPurchaseId);
    });
}
