<?php
$page_title = "Privacy Policy";
require_once __DIR__ . '/includes/header.php';
?>

<section class="section section-bg-light" style="padding-top: 150px;">
    <div class="container">
        <div class="card reveal" style="max-width: 900px; margin: 0 auto; padding: var(--spacing-lg);">
            <h1 style="font-size: var(--text-h2); margin-bottom: 2rem;">Privacy Policy</h1>
            <p>Last updated: <?php echo date('F Y'); ?></p>

            <h3 style="margin-top: 2rem;">1. Information We Collect</h3>
            <p>When you use the <?php echo htmlspecialchars($brand['name']); ?> website or services, we may collect personal information such as your name, email address, phone number, and delivery address. This information is primarily collected when you fill out our contact or order forms.</p>

            <h3 style="margin-top: 2rem;">2. How We Use Your Information</h3>
            <p>We use the information we collect to:</p>
            <ul style="list-style-type: disc; padding-left: 2rem; color: var(--text-muted); margin-bottom: 1rem;">
                <li>Process and deliver your orders.</li>
                <li>Communicate with you regarding delivery schedules or inquiries.</li>
                <li>Improve our website and customer service.</li>
            </ul>

            <h3 style="margin-top: 2rem;">3. Data Security</h3>
            <p>We implement strict security measures to maintain the safety of your personal information. We do not sell, trade, or otherwise transfer your personally identifiable information to outside parties, except trusted third parties who assist us in operating our website or conducting our business, so long as those parties agree to keep this information confidential.</p>

            <h3 style="margin-top: 2rem;">4. Cookies</h3>
            <p>Our website may use "cookies" to enhance user experience. You may choose to set your web browser to refuse cookies or to alert you when cookies are being sent.</p>

            <h3 style="margin-top: 2rem;">5. Contact Us</h3>
            <p>If there are any questions regarding this privacy policy, you may contact us using the information on our <a href="contact.php">Contact Us</a> page.</p>
        </div>
    </div>
</section>

<?php require_once __DIR__ . '/includes/footer.php'; ?>