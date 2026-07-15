// chatbot.js - Price Negotiation AJAX handler

// Enable pressing Enter key to send the offer
document.getElementById('user-offer')?.addEventListener('keypress', function(event) {
    if (event.key === 'Enter') {
        sendOffer();
    }
});

function appendMessage(sender, text) {
    const chatMessages = document.getElementById('chat-messages');
    if (!chatMessages) return;

    const messageDiv = document.createElement('div');
    messageDiv.classList.add('message', sender);
    messageDiv.innerHTML = text;
    chatMessages.appendChild(messageDiv);
    
    // Auto scroll to the bottom of chat
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

function sendOffer() {
    const offerInput = document.getElementById('user-offer');
    if (!offerInput) return;

    const offerValue = offerInput.value.trim();
    if (!offerValue || isNaN(offerValue) || parseFloat(offerValue) <= 0) {
        alert("Please enter a valid price offer greater than 0.");
        return;
    }

    const offerPrice = parseFloat(offerValue).toFixed(2);

    // 1. Append user's proposed offer message to chat bubble log
    appendMessage('user', `My offer is: <strong>$${offerPrice}</strong>`);
    
    // Clear input field
    offerInput.value = '';

    // Disable button during thinking
    const sendBtn = document.getElementById('send-btn');
    if (sendBtn) {
        sendBtn.disabled = true;
        sendBtn.innerText = "Thinking...";
    }

    // 2. Propose AJAX request to Django views
    fetch(negotiateUrl, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrfToken
        },
        body: JSON.stringify({ offer: offerPrice })
    })
    .then(response => {
        if (!response.ok) {
            throw new Error('Network response was not ok');
        }
        return response.json();
    })
    .then(data => {
        // Re-enable send button
        if (sendBtn) {
            sendBtn.disabled = false;
            sendBtn.innerText = "Offer Price";
        }

        // 3. Append bot reply message
        appendMessage('bot', data.message);

        // 4. If offer is accepted, update UI elements dynamically
        if (data.status === 'success' && data.negotiated_price) {
            const price = parseFloat(data.negotiated_price).toFixed(2);
            
            // Show discount price container
            const negotiatedInfo = document.getElementById('negotiated-price-info');
            const negotiatedDisplay = document.getElementById('negotiated-price-display');
            if (negotiatedInfo && negotiatedDisplay) {
                negotiatedInfo.classList.remove('d-none');
                negotiatedDisplay.innerText = `$${price}`;
            }

            // Update add-to-cart & buy-now button titles
            const addToCartBtn = document.getElementById('add-to-cart-btn');
            const buyNowBtn = document.getElementById('buy-now-btn');
            
            if (addToCartBtn) {
                addToCartBtn.innerHTML = `<i class="fa-solid fa-cart-plus me-2"></i>Add to Cart ($${price})`;
                addToCartBtn.classList.remove('btn-info');
                addToCartBtn.classList.add('btn-success');
            }
            
            if (buyNowBtn) {
                buyNowBtn.innerHTML = `<i class="fa-solid fa-bolt me-2"></i>Buy Now ($${price})`;
            }
        }
    })
    .catch(error => {
        console.error('Error during negotiation AJAX:', error);
        // Re-enable send button
        if (sendBtn) {
            sendBtn.disabled = false;
            sendBtn.innerText = "Offer Price";
        }
        appendMessage('bot', "Oops! It seems I encountered an error. Please try offering again in a moment.");
    });
}
