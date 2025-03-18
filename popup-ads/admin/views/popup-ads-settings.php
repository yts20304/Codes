<?php
if (!defined('ABSPATH')) {
    exit; // Exit if accessed directly
}
?>

<div class="wrap">
    <h1><?php esc_html_e('Popup Ads Settings', 'popup-ads'); ?></h1>
    <form method="post" action="options.php" class="popup-ads-admin-form">
        <?php
        settings_fields('popup_ads_settings_group');
        do_settings_sections('popup_ads_settings_page');
        submit_button();
        ?>
    </form>
</div>
