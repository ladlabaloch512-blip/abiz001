<?php
// SMTP Configuration for PHPMailer
// Keep this file secure and out of public access via .htaccess

define('SMTP_HOST', 'smtp.hostinger.com'); // e.g. smtp.gmail.com or smtp.hostinger.com
define('SMTP_USERNAME', 'contact@yourdomain.com');
define('SMTP_PASSWORD', 'your_secure_password');
define('SMTP_PORT', 465); // Typically 465 for SSL, 587 for TLS
define('SMTP_ENCRYPTION', 'ssl'); // 'tls' or 'ssl'

// Receiver Configuration
define('RECEIVER_EMAIL', 'info@yourdomain.com'); // Where the contact emails will be sent
define('RECEIVER_NAME', 'Pure & Fresh Support');
?>