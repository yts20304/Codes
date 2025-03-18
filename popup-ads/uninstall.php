<?php

if (!defined('WP_UNINSTALL_PLUGIN')) {
    die;
}

// Clear database stored data
$popups = get_posts(array('post_type' => 'popup_ads', 'numberposts' => -1));

foreach ($popups as $popup) {
    wp_delete_post($popup->ID, true);
}

// Optionally, delete options or other data
delete_option('popup_ads_settings');
