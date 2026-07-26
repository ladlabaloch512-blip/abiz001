<?php
$page_title = "Quality Process";
require_once __DIR__ . '/includes/header.php';
?>

<section class="section section-bg-light" style="padding-top: 150px;">
    <div class="container">
        <div class="section-header reveal">
            <h1 style="font-size: var(--text-h2);">Uncompromising Quality</h1>
            <p>Discover the journey of every drop, from source to bottle.</p>
        </div>

        <div class="reveal delay-100" style="max-width: 900px; margin: 0 auto 4rem auto; border-radius: var(--border-radius-xl); overflow: hidden; box-shadow: var(--shadow-lg);">
            <img src="assets/images/placeholders/quality-hero.svg" alt="Quality Process Certification" style="width: 100%; display: block;">
        </div>

        <div style="max-width: 800px; margin: 0 auto;">

            <div class="reveal" style="display: flex; gap: var(--spacing-md); margin-bottom: var(--spacing-lg); background: var(--bg-main); padding: var(--spacing-md); border-radius: var(--border-radius-lg); box-shadow: var(--shadow-sm);">
                <div style="font-size: 3rem; color: var(--color-secondary); width: 80px; text-align: center;">1</div>
                <div>
                    <h3>Advanced Filtration</h3>
                    <p>Water passes through multi-stage sand and carbon filters to remove all suspended particles, chlorine, and organic impurities.</p>
                </div>
            </div>

            <div class="reveal delay-100" style="display: flex; gap: var(--spacing-md); margin-bottom: var(--spacing-lg); background: var(--bg-main); padding: var(--spacing-md); border-radius: var(--border-radius-lg); box-shadow: var(--shadow-sm);">
                <div style="font-size: 3rem; color: var(--color-secondary); width: 80px; text-align: center;">2</div>
                <div>
                    <h3>Reverse Osmosis</h3>
                    <p>Our state-of-the-art RO membranes extract microscopic contaminants, heavy metals, and dissolved solids, achieving absolute purity.</p>
                </div>
            </div>

            <div class="reveal delay-200" style="display: flex; gap: var(--spacing-md); margin-bottom: var(--spacing-lg); background: var(--bg-main); padding: var(--spacing-md); border-radius: var(--border-radius-lg); box-shadow: var(--shadow-sm);">
                <div style="font-size: 3rem; color: var(--color-secondary); width: 80px; text-align: center;">3</div>
                <div>
                    <h3>Mineral Enrichment</h3>
                    <p>Pure water is tasteless. We carefully re-introduce essential minerals like Calcium and Magnesium for a crisp, refreshing taste and added health benefits.</p>
                </div>
            </div>

            <div class="reveal delay-300" style="display: flex; gap: var(--spacing-md); margin-bottom: var(--spacing-lg); background: var(--bg-main); padding: var(--spacing-md); border-radius: var(--border-radius-lg); box-shadow: var(--shadow-sm);">
                <div style="font-size: 3rem; color: var(--color-secondary); width: 80px; text-align: center;">4</div>
                <div>
                    <h3>Ozonation & UV Sterilization</h3>
                    <p>Before bottling, the water is treated with Ultraviolet light and Ozonation to ensure it is 100% free of bacteria and viruses.</p>
                </div>
            </div>

        </div>
    </div>
</section>

<?php require_once __DIR__ . '/includes/footer.php'; ?>