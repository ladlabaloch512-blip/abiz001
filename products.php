<?php
$page_title = "Our Products";
require_once __DIR__ . '/includes/header.php';
?>

<section class="section section-bg-light" style="padding-top: 150px;">
    <div class="container">
        <div class="section-header reveal">
            <h1 style="font-size: var(--text-h2);">Premium Hydration Options</h1>
            <p>Explore our full range of carefully purified water bottles, designed to suit every lifestyle and requirement.</p>
        </div>

        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: var(--spacing-lg); margin-top: var(--spacing-lg);">
            <?php
            $count = 0;
            foreach($products as $product):
                $delay = ($count % 3) * 100;
            ?>
            <div class="card product-card reveal delay-<?php echo $delay; ?>" style="background: var(--bg-main);">
                <div class="product-image-wrapper">
                    <img src="<?php echo htmlspecialchars($product['image_path']); ?>" alt="<?php echo htmlspecialchars($product['name']); ?>" class="product-image animate-float" loading="lazy">
                </div>
                <span class="product-size"><?php echo htmlspecialchars($product['size']); ?></span>
                <h3 class="product-title"><?php echo htmlspecialchars($product['name']); ?></h3>
                <p style="font-size: 0.95rem; margin-bottom: 1.5rem; color: var(--text-muted);"><?php echo htmlspecialchars($product['description']); ?></p>
                <a href="contact.php?subject=Inquiry about <?php echo urlencode($product['name']); ?>" class="btn btn-outline" style="width: 100%; margin-top: auto;">Inquire Now</a>
            </div>
            <?php
            $count++;
            endforeach;
            ?>
        </div>
    </div>
</section>

<!-- CTA -->
<section class="section" style="background: var(--color-primary); text-align: center;">
    <div class="container reveal">
        <h2 style="color: var(--text-light);">Need Bulk Orders for Your Business?</h2>
        <p style="color: rgba(255,255,255,0.8); max-width: 600px; margin: 0 auto var(--spacing-lg);">We offer special pricing and dedicated delivery schedules for corporate and wholesale partners.</p>
        <a href="contact.php?subject=Corporate Partnership" class="btn btn-secondary">Contact Wholesale Team</a>
    </div>
</section>

<?php require_once __DIR__ . '/includes/footer.php'; ?>