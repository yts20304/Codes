<?php
if (!defined('ABSPATH')) {
    exit; // Exit if accessed directly
}
?>

<div class="wrap">
    <h1><?php esc_html_e('Popup Ads Builder', 'popup-ads'); ?></h1>
    <form method="post" action="admin-post.php" class="popup-ads-builder">
        <?php
        // Add nonce for security
        wp_nonce_field('popup_ads_builder_nonce', 'popup_ads_builder_nonce_field');
        ?>
        <div class="popup-ads-builder-container">
            <label for="popup-title"><?php esc_html_e('Popup Title', 'popup-ads'); ?></label>
            <input type="text" id="popup-title" name="popup_title" required>

            <label for="popup-content"><?php esc_html_e('Popup Content', 'popup-ads'); ?></label>
            <textarea id="popup-content" name="popup_content" rows="5" required></textarea>

            <label for="popup-display-rules"><?php esc_html_e('Display Rules', 'popup-ads'); ?></label>
            <textarea id="popup-display-rules" name="popup_display_rules" rows="3" required></textarea>

            <button type="submit" class="button button-primary"><?php esc_html_e('Save Popup', 'popup-ads'); ?></button>
        </div>
    </form>
</div>
