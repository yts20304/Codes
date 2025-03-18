document.addEventListener('DOMContentLoaded', function() {
    // Function to display the popup
    function displayPopup(popupId) {
        var popup = document.getElementById(popupId);
        if (popup) {
            popup.style.display = 'block';
        }
    }

    // Function to close the popup
    function closePopup(popupId) {
        var popup = document.getElementById(popupId);
        if (popup) {
            popup.style.display = 'none';
        }
    }

    // Add event listener to close button
    var closeButtons = document.querySelectorAll('.popup-ads-close');
    closeButtons.forEach(function(button) {
        button.addEventListener('click', function() {
            var popupId = this.closest('.popup-ads-container').id;
            closePopup(popupId);
        });
    });

    // Example: Display the popup with ID 'popup-ads-1' after 5 seconds
    setTimeout(function() {
        displayPopup('popup-ads-1');
    }, 5000);
});
