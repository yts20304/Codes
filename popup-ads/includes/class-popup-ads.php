<?php

class Popup_Ads {

    public function __construct() {
        // Plugin initialization code here
    }

    public static function activate() {
        // Code to run during plugin activation
    }

    public static function deactivate() {
        // Code to run during plugin deactivation
    }

    public function register() {
        // Code to register the plugin with WordPress
    }
}

register_activation_hook(__FILE__, array('Popup_Ads', 'activate'));
register_deactivation_hook(__FILE__, array('Popup_Ads', 'deactivate'));

$popup_ads = new Popup_Ads();
$popup_ads->register();
