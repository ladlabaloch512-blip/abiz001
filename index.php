<?php
$page_title = "Home";
require_once __DIR__ . '/includes/header.php';
?>

<!-- HERO SECTION -->
<section class="hero-section">
    <!-- Canvas for Water Ripple -->
    <div class="hero-canvas-container ripple-bg" id="hero-canvas-wrapper">
        <canvas id="water-ripple-canvas"></canvas>
    </div>

    <div class="container" style="position: relative; z-index: 10;">
        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: var(--spacing-lg); align-items: center;">
            <div class="hero-content reveal">
                <h1 class="hero-title">Experience the <br><span style="color: var(--color-secondary);">Purest</span> Drinking Water.</h1>
                <p style="font-size: 1.25rem; margin-bottom: 2rem; max-width: 500px; color: var(--text-main);">
                    Hydrate your life with our premium, carefully purified water. Delivered fresh to your home or office.
                </p>
                <div style="display: flex; gap: 1rem; flex-wrap: wrap;">
                    <a href="products.php" class="btn btn-primary">View Products</a>
                    <a href="contact.php" class="btn btn-outline">Order Now</a>
                </div>
            </div>

            <div class="hero-image-wrapper reveal delay-200" style="text-align: center; display: none;">
                <!-- Fallback to display block on desktop via CSS -->
                <img src="assets/images/banners/hero-bottles.svg" alt="Premium Bottles" class="animate-float" style="max-width: 100%; height: auto; display: block; margin: 0 auto; filter: drop-shadow(0 20px 30px rgba(0,0,0,0.1));">
            </div>
        </div>
    </div>
</section>

<!-- ABOUT PREVIEW SECTION -->
<section class="section section-bg-light">
    <div class="container">
        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: var(--spacing-xl); align-items: center;">
            <div class="reveal">
                <span class="section-subtitle">Who We Are</span>
                <h2>Commitment to Health & Purity</h2>
                <p>At <?php echo htmlspecialchars($brand['name']); ?>, we believe that access to clean, mineral-rich drinking water is a fundamental right. We source our water from the most pristine environments and use state-of-the-art purification technology.</p>
                <p>Our meticulous process guarantees every drop meets the highest international safety standards, ensuring you and your family enjoy crisp, refreshing hydration every single day.</p>
                <a href="about.php" class="btn btn-outline" style="margin-top: 1rem;">Learn More About Us</a>
            </div>
            <div class="reveal delay-200" style="position: relative;">
                <div style="background: var(--gradient-primary); border-radius: var(--border-radius-xl); padding: 2rem; aspect-ratio: 4/3; display: flex; align-items: center; justify-content: center; overflow: hidden; box-shadow: var(--shadow-lg);">
                    <h3 style="color: white; opacity: 0.5;">AGENCY PLACEHOLDER IMAGE</h3>
                </div>
            </div>
        </div>
    </div>
</section>

<!-- PRODUCTS PREVIEW SECTION -->
<section class="section">
    <div class="container">
        <div class="section-header reveal">
            <span class="section-subtitle">Our Range</span>
            <h2>Perfect Sizes for Every Need</h2>
            <p>From large family gallons to convenient pocket sizes, we have the perfect bottle for your hydration needs.</p>
        </div>

        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: var(--spacing-md);">
            <?php
            // Display top 4 products
            $count = 0;
            foreach($products as $product):
                if($count >= 4) break;
                $delay = $count * 100;
            ?>
            <div class="card product-card reveal delay-<?php echo $delay; ?>">
                <div class="product-image-wrapper">
                    <img src="<?php echo htmlspecialchars($product['image_path']); ?>" alt="<?php echo htmlspecialchars($product['name']); ?>" class="product-image animate-float" loading="lazy">
                </div>
                <span class="product-size"><?php echo htmlspecialchars($product['size']); ?></span>
                <h3 class="product-title"><?php echo htmlspecialchars($product['name']); ?></h3>
                <p style="font-size: 0.9rem; margin-bottom: 1.5rem;"><?php echo htmlspecialchars($product['description']); ?></p>

                <?php if(!empty($brand['whatsapp'])): ?>
                    <div style="margin-top: auto;">
                        <?php
                        $wa_msg = "Hello, I'm interested in the " . $product['name'] . ". Please provide more information.";
                        $wa_link = "https://wa.me/" . $brand['whatsapp'] . "?text=" . urlencode($wa_msg);
                        ?>
                        <a href="<?php echo htmlspecialchars($wa_link); ?>" target="_blank" class="btn" style="width: 100%; background-color: #25D366; color: white; border: none; font-size: 0.9rem; padding: 0.75rem 1rem;">Inquire on WhatsApp</a>
                    </div>
                <?php endif; ?>
            </div>
            <?php
            $count++;
            endforeach;
            ?>
        </div>

        <div class="text-center reveal delay-400" style="margin-top: var(--spacing-lg);">
            <a href="products.php" class="btn btn-secondary">View All Products</a>
        </div>
    </div>
</section>

<!-- QUALITY PROCESS PREVIEW -->
<section class="section section-bg-dark text-center">
    <div class="container">
        <div class="section-header reveal">
            <span class="section-subtitle" style="color: var(--color-accent);">Uncompromising Standards</span>
            <h2>7-Step Purification Process</h2>
            <p style="color: rgba(255,255,255,0.8);">Every drop goes through rigorous filtration, reverse osmosis, and UV sterilization to ensure 100% purity before it reaches you.</p>
        </div>

        <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: var(--spacing-md); max-width: 900px; margin: 0 auto var(--spacing-lg);">
            <div class="reveal delay-100" style="background: rgba(255,255,255,0.1); padding: 2rem; border-radius: var(--border-radius-lg); border: 1px solid rgba(255,255,255,0.2); box-shadow: var(--shadow-sm);">
                <div style="font-size: 3rem; margin-bottom: 1rem;">💧</div>
                <h4 style="color: #ffffff;">Filtration</h4>
            </div>
            <div class="reveal delay-200" style="background: rgba(255,255,255,0.1); padding: 2rem; border-radius: var(--border-radius-lg); border: 1px solid rgba(255,255,255,0.2); box-shadow: var(--shadow-sm);">
                <div style="font-size: 3rem; margin-bottom: 1rem;">⚡</div>
                <h4 style="color: #ffffff;">Ozonation</h4>
            </div>
            <div class="reveal delay-300" style="background: rgba(255,255,255,0.1); padding: 2rem; border-radius: var(--border-radius-lg); border: 1px solid rgba(255,255,255,0.2); box-shadow: var(--shadow-sm);">
                <div style="font-size: 3rem; margin-bottom: 1rem;">🔬</div>
                <h4 style="color: #ffffff;">Testing</h4>
            </div>
        </div>
        <a href="quality.php" class="btn btn-outline reveal delay-400" style="color: white; border-color: white;">Discover Our Process</a>
    </div>
</section>

<!-- WHY CHOOSE US -->
<section class="section">
    <div class="container">
        <div class="section-header reveal">
            <span class="section-subtitle">Why Us</span>
            <h2>The Premium Choice</h2>
        </div>
        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: var(--spacing-md);">
            <div class="card reveal delay-100">
                <div style="width: 60px; height: 60px; background: var(--bg-secondary); border-radius: 50%; display: flex; align-items: center; justify-content: center; margin-bottom: 1rem; color: var(--color-secondary); font-size: 1.5rem;">🚚</div>
                <h3>Fast Delivery</h3>
                <p>We ensure your water reaches you promptly with our dedicated fleet of delivery vehicles, maintaining the perfect schedule for your needs.</p>
            </div>
            <div class="card reveal delay-200">
                <div style="width: 60px; height: 60px; background: var(--bg-secondary); border-radius: 50%; display: flex; align-items: center; justify-content: center; margin-bottom: 1rem; color: var(--color-secondary); font-size: 1.5rem;">🛡️</div>
                <h3>Trusted Brand</h3>
                <p>Thousands of homes and businesses rely on our consistent quality and exceptional customer service every single day.</p>
            </div>
            <div class="card reveal delay-300">
                <div style="width: 60px; height: 60px; background: var(--bg-secondary); border-radius: 50%; display: flex; align-items: center; justify-content: center; margin-bottom: 1rem; color: var(--color-secondary); font-size: 1.5rem;">💎</div>
                <h3>Premium Quality</h3>
                <p>Never compromising on safety, our water is enriched with essential minerals for a crisp, smooth taste.</p>
            </div>
        </div>
    </div>
</section>

<!-- TESTIMONIALS & FAQ -->
<section class="section section-bg-light">
    <div class="container">
        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: var(--spacing-xl);">

            <!-- Testimonials Slider -->
            <div class="reveal">
                <span class="section-subtitle">Testimonials</span>
                <h2>What Our Clients Say</h2>
                <div class="testimonial-slider-container" style="margin-top: 2rem; position: relative; overflow: hidden;">
                    <div class="testimonial-track" id="testimonial-track" style="display: flex; transition: transform var(--transition-medium);">

                        <!-- Slide 1 -->
                        <div class="testimonial-slide" style="min-width: 100%; padding-right: 1rem; box-sizing: border-box;">
                            <div class="card" style="background: var(--bg-main);">
                                <p style="font-size: 1.1rem; font-style: italic; color: var(--text-main);">"Since switching to <?php echo htmlspecialchars($brand['name']); ?>, our office has never been happier. The water tastes incredible, and the 19L delivery is always exactly on time. Highly recommended premium service."</p>
                                <div style="margin-top: 1.5rem; display: flex; align-items: center; gap: 1rem;">
                                    <div style="width: 50px; height: 50px; background: var(--color-highlight); border-radius: 50%;"></div>
                                    <div>
                                        <h4 style="margin: 0; font-size: 1rem;">Sarah Jenkins</h4>
                                        <span style="font-size: 0.85rem; color: var(--text-muted);">Office Manager</span>
                                    </div>
                                </div>
                            </div>
                        </div>

                        <!-- Slide 2 -->
                        <div class="testimonial-slide" style="min-width: 100%; padding-right: 1rem; box-sizing: border-box;">
                            <div class="card" style="background: var(--bg-main);">
                                <p style="font-size: 1.1rem; font-style: italic; color: var(--text-main);">"The convenience of having premium water delivered directly to our door cannot be overstated. The customer service is responsive, and the purity is unmatched."</p>
                                <div style="margin-top: 1.5rem; display: flex; align-items: center; gap: 1rem;">
                                    <div style="width: 50px; height: 50px; background: var(--color-highlight); border-radius: 50%;"></div>
                                    <div>
                                        <h4 style="margin: 0; font-size: 1rem;">Michael Rodriguez</h4>
                                        <span style="font-size: 0.85rem; color: var(--text-muted);">Homeowner</span>
                                    </div>
                                </div>
                            </div>
                        </div>

                    </div>

                    <!-- Slider Controls -->
                    <div style="display: flex; gap: 0.5rem; margin-top: 1rem; justify-content: center;">
                        <button class="slider-dot active" data-slide="0" aria-label="Go to slide 1" style="width: 12px; height: 12px; border-radius: 50%; background: var(--color-secondary); opacity: 1; transition: opacity var(--transition-fast);"></button>
                        <button class="slider-dot" data-slide="1" aria-label="Go to slide 2" style="width: 12px; height: 12px; border-radius: 50%; background: var(--color-secondary); opacity: 0.3; transition: opacity var(--transition-fast);"></button>
                    </div>
                </div>
            </div>

            <!-- FAQ -->
            <div class="reveal delay-200">
                <span class="section-subtitle">FAQ</span>
                <h2>Common Questions</h2>
                <div class="accordion" style="margin-top: 2rem;">

                    <div class="accordion-item">
                        <button class="accordion-header" aria-expanded="false">
                            How often do you deliver?
                            <span class="accordion-icon">▼</span>
                        </button>
                        <div class="accordion-body">
                            <div class="accordion-content">
                                We offer flexible delivery schedules including daily, weekly, and bi-weekly options depending on your consumption needs and location.
                            </div>
                        </div>
                    </div>

                    <div class="accordion-item">
                        <button class="accordion-header" aria-expanded="false">
                            Are your bottles BPA-free?
                            <span class="accordion-icon">▼</span>
                        </button>
                        <div class="accordion-body">
                            <div class="accordion-content">
                                Absolutely. All our 19L, 1.5L, and smaller PET bottles are strictly BPA-free and manufactured using food-grade materials to ensure maximum safety.
                            </div>
                        </div>
                    </div>

                    <div class="accordion-item">
                        <button class="accordion-header" aria-expanded="false">
                            Do you serve commercial offices?
                            <span class="accordion-icon">▼</span>
                        </button>
                        <div class="accordion-body">
                            <div class="accordion-content">
                                Yes, we have specialized corporate plans that include water dispenser maintenance and automated bulk deliveries tailored for offices.
                            </div>
                        </div>
                    </div>

                </div>
            </div>

        </div>
    </div>
</section>

<!-- CTA SECTION -->
<section class="section" style="background: var(--gradient-accent); text-align: center; color: var(--bg-dark);">
    <div class="container reveal">
        <h2 style="color: var(--bg-dark);">Ready to taste the difference?</h2>
        <p style="color: var(--bg-dark); max-width: 600px; margin: 0 auto var(--spacing-lg);">Contact our team today to setup your first delivery or inquire about our corporate hydration solutions.</p>
        <a href="contact.php" class="btn" style="background: var(--bg-dark); color: white;">Contact Us Now</a>
    </div>
</section>

<?php require_once __DIR__ . '/includes/footer.php'; ?>