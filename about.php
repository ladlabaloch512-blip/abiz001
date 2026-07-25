<?php
$page_title = "About Us";
require_once __DIR__ . '/includes/header.php';
?>

<section class="section section-bg-light" style="padding-top: 150px;">
    <div class="container">
        <div class="section-header reveal">
            <h1 style="font-size: var(--text-h2);">About <?php echo htmlspecialchars($brand['name']); ?></h1>
            <p>Dedicated to providing the purest hydration experience.</p>
        </div>

        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: var(--spacing-xl); align-items: center; margin-top: var(--spacing-lg);">
            <div class="reveal">
                <h2>Our Mission</h2>
                <p>Our mission is simple: to deliver the highest quality drinking water to homes and businesses while maintaining sustainable and eco-friendly practices. We believe that access to clean, safe, and refreshing water is essential for a healthy community.</p>
                <p>Through continuous innovation in our purification processes and strict adherence to international quality standards, we ensure every bottle that leaves our facility is a testament to purity.</p>
            </div>
            <div class="reveal delay-200">
                <div style="background: var(--color-highlight); border-radius: var(--border-radius-lg); aspect-ratio: 16/9; display: flex; align-items: center; justify-content: center; box-shadow: var(--shadow-md);">
                    <span style="color: var(--text-muted);">MISSION IMAGE PLACEHOLDER</span>
                </div>
            </div>
        </div>

        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: var(--spacing-xl); align-items: center; margin-top: var(--spacing-xxl);">
            <div class="reveal delay-100" style="order: 2;">
                <h2>Our Vision</h2>
                <p>We envision a future where premium hydration is accessible to everyone. By expanding our reach and investing in cutting-edge water treatment technologies, we aim to be the most trusted name in the bottled water industry nationwide.</p>
                <p>We are not just bottling water; we are bottling health, vitality, and trust.</p>
            </div>
            <div class="reveal" style="order: 1;">
                <div style="background: var(--color-primary); border-radius: var(--border-radius-lg); aspect-ratio: 16/9; display: flex; align-items: center; justify-content: center; box-shadow: var(--shadow-md);">
                    <span style="color: var(--text-light); opacity: 0.5;">VISION IMAGE PLACEHOLDER</span>
                </div>
            </div>
        </div>
    </div>
</section>

<?php require_once __DIR__ . '/includes/footer.php'; ?>