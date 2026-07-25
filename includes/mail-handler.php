<?php
session_start();
require_once __DIR__ . '/config.php';
require_once __DIR__ . '/PHPMailer/Exception.php';
require_once __DIR__ . '/PHPMailer/PHPMailer.php';
require_once __DIR__ . '/PHPMailer/SMTP.php';

use PHPMailer\PHPMailer\PHPMailer;
use PHPMailer\PHPMailer\Exception;

// Initialize response array
$response = [
    'status' => 'error',
    'message' => 'An unexpected error occurred.'
];

// Check if it's a POST request
if ($_SERVER["REQUEST_METHOD"] == "POST") {

    // 1. CSRF Protection Check
    if (!isset($_POST['csrf_token']) || $_POST['csrf_token'] !== $_SESSION['csrf_token']) {
        $response['message'] = 'Security verification failed. Please refresh the page and try again.';
        echo json_encode($response);
        exit;
    }

    // 2. Rate Limiting (1 request per 60 seconds)
    if (isset($_SESSION['last_submit_time']) && (time() - $_SESSION['last_submit_time'] < 60)) {
        $response['message'] = 'Please wait a moment before sending another message.';
        echo json_encode($response);
        exit;
    }

    // 3. Basic Spam Prevention (Honeypot)
    if (!empty($_POST['website_url_hp'])) {
        // Honeypot field was filled out, likely a bot
        $response['status'] = 'success';
        $response['message'] = 'Thank you for your message.'; // Fake success
        echo json_encode($response);
        exit;
    }

    // 4. Sanitize and Validate Inputs
    // Using strip_tags and trim as FILTER_SANITIZE_STRING is deprecated in PHP 8.1+
    $name = isset($_POST['name']) ? strip_tags(trim($_POST['name'])) : '';
    $email = filter_input(INPUT_POST, 'email', FILTER_SANITIZE_EMAIL);
    $phone = isset($_POST['phone']) ? strip_tags(trim($_POST['phone'])) : '';
    $subject_input = isset($_POST['subject']) ? strip_tags(trim($_POST['subject'])) : '';
    $message = isset($_POST['message']) ? strip_tags(trim($_POST['message'])) : '';

    if (empty($name) || empty($email) || empty($message)) {
        $response['message'] = 'Please fill out all required fields.';
        echo json_encode($response);
        exit;
    }

    if (!filter_var($email, FILTER_VALIDATE_EMAIL)) {
        $response['message'] = 'Please provide a valid email address.';
        echo json_encode($response);
        exit;
    }

    $subject_line = empty($subject_input) ? 'New Contact Form Submission' : 'Website Inquiry: ' . $subject_input;

    // 5. Send Email via PHPMailer
    $mail = new PHPMailer(true);

    try {
        // Server settings
        $mail->isSMTP();
        $mail->Host       = SMTP_HOST;
        $mail->SMTPAuth   = true;
        $mail->Username   = SMTP_USERNAME;
        $mail->Password   = SMTP_PASSWORD;
        $mail->SMTPSecure = SMTP_ENCRYPTION;
        $mail->Port       = SMTP_PORT;

        // Recipients
        $mail->setFrom(SMTP_USERNAME, 'Website Contact Form');
        $mail->addAddress(RECEIVER_EMAIL, RECEIVER_NAME);
        $mail->addReplyTo($email, $name);

        // Content
        $mail->isHTML(true);
        $mail->Subject = $subject_line;

        // Email Body
        $email_body = "
            <h2>New Inquiry from Website</h2>
            <p><strong>Name:</strong> {$name}</p>
            <p><strong>Email:</strong> {$email}</p>
            <p><strong>Phone:</strong> {$phone}</p>
            <p><strong>Subject:</strong> {$subject_input}</p>
            <br>
            <p><strong>Message:</strong></p>
            <p>" . nl2br(htmlspecialchars($message)) . "</p>
        ";

        $mail->Body    = $email_body;
        $mail->AltBody = strip_tags(str_replace('<br>', "\n", $email_body));

        $mail->send();

        // Update session time for rate limiting
        $_SESSION['last_submit_time'] = time();

        $response['status'] = 'success';
        $response['message'] = 'Thank you! Your message has been sent successfully. We will contact you soon.';

    } catch (Exception $e) {
        // Log the actual error securely without exposing it to the frontend
        error_log("Mailer Error: {$mail->ErrorInfo}");
        $response['message'] = 'Sorry, your message could not be sent at this time due to a server error. Please try again later.';
    }

    echo json_encode($response);
    exit;
} else {
    // Direct access not allowed
    header("Location: ../index.php");
    exit;
}
?>