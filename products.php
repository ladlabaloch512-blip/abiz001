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

                <div style="margin-top: auto; display: flex; flex-direction: column; gap: 0.5rem;">
                    <a href="contact.php?subject=Inquiry about <?php echo urlencode($product['name']); ?>" class="btn btn-outline" style="width: 100%;">Email Inquiry</a>

                    <?php if(!empty($brand['whatsapp'])): ?>
                        <?php
                        $wa_msg = "Hello, I'm interested in the " . $product['name'] . ". Please provide more information.";
                        $wa_link = "https://wa.me/" . $brand['whatsapp'] . "?text=" . urlencode($wa_msg);
                        ?>
                        <a href="<?php echo htmlspecialchars($wa_link); ?>" target="_blank" class="btn" style="width: 100%; background-color: #25D366; color: white; border: none; box-shadow: var(--shadow-sm);">Inquire on WhatsApp</a>
                    <?php endif; ?>
                </div>
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