# Popup Ads WordPress Plugin

## Description

The Popup Ads WordPress Plugin allows you to create, customize, and display popups on your WordPress website. It includes features for building popups, managing settings, tracking analytics, and more.

## Folder and File Structure

```
popup-ads/
├── includes/
│   ├── class-popup-ads.php
│   ├── class-popup-builder.php
│   ├── class-popup-display.php
│   ├── class-popup-settings.php
│   └── class-popup-analytics.php
├── admin/
│   ├── class-popup-ads-admin.php
│   ├── assets/
│   │   ├── css/
│   │   │   └── popup-ads-admin.css
│   │   └── js/
│   │       └── popup-ads-admin.js
│   └── views/
│       ├── popup-ads-settings.php
│       └── popup-ads-builder.php
├── public/
│   ├── class-popup-ads-public.php
│   ├── assets/
│   │   ├── css/
│   │   │   └── popup-ads-public.css
│   │   └── js/
│   │       └── popup-ads-public.js
│   └── views/
│       └── popup-ads-display.php
├── vendor/
│   └── (Third-party libraries)
├── languages/
│   └── popup-ads.pot
├── uninstall.php
├── popup-ads.php
└── README.md
```

## Breakdown of Folders and Files

1. **includes/**: This folder contains the core classes that make up the plugin's functionality.
   - `class-popup-ads.php`: The main plugin class that handles the plugin initialization and registration.
   - `class-popup-builder.php`: The class responsible for the popup builder and customization.
   - `class-popup-display.php`: The class that handles the display of popups on the website.
   - `class-popup-settings.php`: The class that manages the plugin's settings and options.
   - `class-popup-analytics.php`: The class that handles the popup analytics and reporting.

2. **admin/**: This folder contains the administrative-related files for the plugin.
   - `class-popup-ads-admin.php`: The class that handles the admin-side functionality, such as the settings page and the popup builder.
   - `assets/`: This folder contains the CSS and JavaScript files used in the admin area.
   - `views/`: This folder contains the admin-side views, such as the settings page and the popup builder interface.

3. **public/**: This folder contains the public-facing files for the plugin.
   - `class-popup-ads-public.php`: The class that handles the public-facing functionality, such as the popup display on the website.
   - `assets/`: This folder contains the CSS and JavaScript files used on the public-facing side.
   - `views/`: This folder contains the public-facing views, such as the popup display template.

4. **vendor/**: This folder is for any third-party libraries or dependencies used by the plugin.

5. **languages/**: This folder contains the translation files for the plugin.

6. **uninstall.php**: This file is used to clean up any data or settings when the plugin is uninstalled.

7. **popup-ads.php**: This is the main plugin file that is loaded by WordPress.

8. **README.md**: This file contains the plugin's documentation and instructions.
