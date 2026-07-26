<?php
$page_title = "Terms and Conditions";
require_once __DIR__ . '/includes/header.php';
?>

<section class="section section-bg-light" style="padding-top: 150px;">
    <div class="container">
        <div class="card reveal" style="max-width: 900px; margin: 0 auto; padding: var(--spacing-lg);">
            <h1 style="font-size: var(--text-h2); margin-bottom: 2rem;">Terms & Conditions</h1>
            <p>Last updated: <?php echo date('F Y'); ?></p>

            <h3 style="margin-top: 2rem;">1. Acceptance of Terms</h3>
            <p>By accessing and using the <?php echo htmlspecialchars($brand['name']); ?> website, you accept and agree to be bound by the terms and provision of this agreement. If you do not agree to abide by these terms, please do not use this service.</p>

            <h3 style="margin-top: 2rem;">2. Orders and Deliveries</h3>
            <p>All orders placed through our website or via phone are subject to availability and confirmation of the order price. Delivery times may vary according to availability and any guarantees or representations made as to delivery times are subject to any delays resulting from postal delays or force majeure for which we will not be responsible.</p>

            <h3 style="margin-top: 2rem;">3. Empty Bottle Returns (19L)</h3>
            <p>For 19-liter gallon deliveries, customers are required to return empty bottles in good condition. Damaged or lost bottles may incur replacement fees as outlined in your delivery agreement.</p>

            <h3 style="margin-top: 2rem;">4. Intellectual Property</h3>
            <p>The website and its original content, features, and functionality are owned by <?php echo htmlspecialchars($brand['name']); ?> and are protected by international copyright, trademark, patent, trade secret, and other intellectual property or proprietary rights laws.</p>

            <h3 style="margin-top: 2rem;">5. Changes to Terms</h3>
            <p>We reserve the right to modify these terms at any time. We do so by posting and drawing attention to the updated terms on the Site. Your decision to continue to visit and make use of the Site after such changes have been made constitutes your formal acceptance of the new Terms.</p>
        </div>
    </div>
</section>

<?php require_once __DIR__ . '/includes/footer.php'; ?>