<?php
$page_title = "Why Choose Us";
require_once __DIR__ . '/includes/header.php';
?>

<section class="section section-bg-light" style="padding-top: 150px;">
    <div class="container">
        <div class="section-header reveal">
            <h1 style="font-size: var(--text-h2);">The Premium Choice</h1>
            <p>Why thousands of households and businesses trust <?php echo htmlspecialchars($brand['name']); ?>.</p>
        </div>

        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: var(--spacing-lg); margin-top: var(--spacing-lg);">

            <div class="card reveal delay-100">
                <div style="width: 70px; height: 70px; background: rgba(0,180,216,0.1); border-radius: var(--border-radius-md); display: flex; align-items: center; justify-content: center; margin-bottom: 1.5rem; color: var(--color-secondary); font-size: 2rem;">🛡️</div>
                <h3>100% Safe Drinking Water</h3>
                <p>Our comprehensive 7-step purification process ensures that every bottle exceeds local and international health standards. We guarantee pure, safe hydration in every drop.</p>
            </div>

            <div class="card reveal delay-200">
                <div style="width: 70px; height: 70px; background: rgba(0,180,216,0.1); border-radius: var(--border-radius-md); display: flex; align-items: center; justify-content: center; margin-bottom: 1.5rem; color: var(--color-secondary); font-size: 2rem;">🚚</div>
                <h3>Reliable & Fast Delivery</h3>
                <p>We value your time. Our dedicated logistics team and fleet of delivery vehicles ensure that your orders arrive exactly when you need them, without delays.</p>
            </div>

            <div class="card reveal delay-300">
                <div style="width: 70px; height: 70px; background: rgba(0,180,216,0.1); border-radius: var(--border-radius-md); display: flex; align-items: center; justify-content: center; margin-bottom: 1.5rem; color: var(--color-secondary); font-size: 2rem;">💰</div>
                <h3>Premium yet Affordable</h3>
                <p>We believe that high-quality water shouldn't be a luxury. We offer competitive pricing across all our bottle sizes, providing exceptional value for money.</p>
            </div>

            <div class="card reveal delay-100">
                <div style="width: 70px; height: 70px; background: rgba(0,180,216,0.1); border-radius: var(--border-radius-md); display: flex; align-items: center; justify-content: center; margin-bottom: 1.5rem; color: var(--color-secondary); font-size: 2rem;">🌱</div>
                <h3>Eco-Conscious Practices</h3>
                <p>We are committed to sustainability. Our bottles are 100% recyclable, and our 19L gallons are thoroughly sterilized and reused to minimize environmental impact.</p>
            </div>

            <div class="card reveal delay-200">
                <div style="width: 70px; height: 70px; background: rgba(0,180,216,0.1); border-radius: var(--border-radius-md); display: flex; align-items: center; justify-content: center; margin-bottom: 1.5rem; color: var(--color-secondary); font-size: 2rem;">👔</div>
                <h3>Corporate Solutions</h3>
                <p>From modern dispensers to scheduled bulk deliveries, we provide end-to-end hydration solutions tailored specifically for offices and commercial spaces.</p>
            </div>

            <div class="card reveal delay-300">
                <div style="width: 70px; height: 70px; background: rgba(0,180,216,0.1); border-radius: var(--border-radius-md); display: flex; align-items: center; justify-content: center; margin-bottom: 1.5rem; color: var(--color-secondary); font-size: 2rem;">🤝</div>
                <h3>Excellent Support</h3>
                <p>Our customer service team is always ready to assist you with order adjustments, delivery queries, or maintenance requests with a smile.</p>
            </div>

        </div>
    </div>
</section>

<?php require_once __DIR__ . '/includes/footer.php'; ?>