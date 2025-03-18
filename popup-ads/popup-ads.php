<?php
/**
 * Plugin Name: Popup Ads
 * Description: A WordPress plugin to create and display popup ads.
 * Version: 1.0
 * Author: Your Name
 * Text Domain: popup-ads
 */

if ( ! defined( 'ABSPATH' ) ) {
    exit; // Exit if accessed directly
}

// Include the main plugin class
require_once plugin_dir_path( __FILE__ ) . 'includes/class-popup-ads.php';

// Register activation and deactivation hooks
register_activation_hook( __FILE__, array( 'Popup_Ads', 'activate' ) );
register_deactivation_hook( __FILE__, array( 'Popup_Ads', 'deactivate' ) );

// Initialize the plugin
$popup_ads = new Popup_Ads();
$popup_ads->register();
