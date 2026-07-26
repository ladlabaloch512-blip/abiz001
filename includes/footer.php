    </main>

    <footer class="site-footer">
        <div class="container">
            <div class="footer-grid">

                <!-- Brand Col -->
                <div class="footer-col reveal">
                    <?php if (file_exists(__DIR__ . '/../' . $brand['logo_path'])): ?>
                        <img src="<?php echo $brand['logo_path']; ?>" alt="<?php echo htmlspecialchars($brand['name']); ?> Logo" style="width: 150px; margin-bottom: 1.5rem; filter: brightness(0) invert(1);" loading="eager" onerror="this.outerHTML='<h2 style=\'color: white; margin-bottom: 1.5rem; font-size: 1.5rem;\'><?php echo htmlspecialchars($brand['name']); ?></h2>'">
                    <?php else: ?>
                        <h2 style="color: white; margin-bottom: 1.5rem; font-size: 1.5rem;"><?php echo htmlspecialchars($brand['name']); ?></h2>
                    <?php endif; ?>
                    <p><?php echo htmlspecialchars($brand['slogan']); ?></p>
                    <div class="footer-social">
                        <?php if(!empty($brand['facebook'])): ?>
                            <a href="<?php echo $brand['facebook']; ?>" class="social-icon" aria-label="Facebook">
                                <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M18 2h-3a5 5 0 0 0-5 5v3H7v4h3v8h4v-8h3l1-4h-4V7a1 1 0 0 1 1-1h3z"></path></svg>
                            </a>
                        <?php endif; ?>
                        <?php if(!empty($brand['instagram'])): ?>
                            <a href="<?php echo $brand['instagram']; ?>" class="social-icon" aria-label="Instagram">
                                <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="2" y="2" width="20" height="20" rx="5" ry="5"></rect><path d="M16 11.37A4 4 0 1 1 12.63 8 4 4 0 0 1 16 11.37z"></path><line x1="17.5" y1="6.5" x2="17.51" y2="6.5"></line></svg>
                            </a>
                        <?php endif; ?>
                        <?php if(!empty($brand['linkedin'])): ?>
                            <a href="<?php echo $brand['linkedin']; ?>" class="social-icon" aria-label="LinkedIn">
                                <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M16 8a6 6 0 0 1 6 6v7h-4v-7a2 2 0 0 0-2-2 2 2 0 0 0-2 2v7h-4v-7a6 6 0 0 1 6-6z"></path><rect x="2" y="9" width="4" height="12"></rect><circle cx="4" cy="4" r="2"></circle></svg>
                            </a>
                        <?php endif; ?>
                        <?php if(!empty($brand['twitter'])): ?>
                            <a href="<?php echo $brand['twitter']; ?>" class="social-icon" aria-label="Twitter">
                                <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M23 3a10.9 10.9 0 0 1-3.14 1.53 4.48 4.48 0 0 0-7.86 3v1A10.66 10.66 0 0 1 3 4s-4 9 5 13a11.64 11.64 0 0 1-7 2c9 5 20 0 20-11.5a4.5 4.5 0 0 0-.08-.83A7.72 7.72 0 0 0 23 3z"></path></svg>
                            </a>
                        <?php endif; ?>
                    </div>
                </div>

                <!-- Quick Links -->
                <div class="footer-col reveal delay-100">
                    <h4>Quick Links</h4>
                    <a href="about.php" class="footer-link">About Us</a>
                    <a href="products.php" class="footer-link">Our Products</a>
                    <a href="quality.php" class="footer-link">Quality Process</a>
                    <a href="why-us.php" class="footer-link">Why Choose Us</a>
                </div>

                <!-- Support -->
                <div class="footer-col reveal delay-200">
                    <h4>Support</h4>
                    <a href="contact.php" class="footer-link">Contact Us</a>
                    <a href="privacy.php" class="footer-link">Privacy Policy</a>
                    <a href="terms.php" class="footer-link">Terms & Conditions</a>
                </div>

                <!-- Contact Info -->
                <div class="footer-col reveal delay-300">
                    <h4>Contact Us</h4>
                    <div class="footer-icon-text">
                        <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="color: var(--color-secondary);"><path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"></path><circle cx="12" cy="10" r="3"></circle></svg>
                        <span>
                            <?php echo htmlspecialchars($brand['address_line_1']); ?>,
                            <?php echo htmlspecialchars($brand['address_line_2']); ?>
                        </span>
                    </div>
                    <div class="footer-icon-text" style="margin-top: 0.5rem;">
                        <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="color: var(--color-secondary);"><path d="M22 16.92v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07 19.5 19.5 0 0 1-6-6 19.79 19.79 0 0 1-3.07-8.67A2 2 0 0 1 4.11 2h3a2 2 0 0 1 2 1.72 12.84 12.84 0 0 0 .7 2.81 2 2 0 0 1-.45 2.11L8.09 9.91a16 16 0 0 0 6 6l1.27-1.27a2 2 0 0 1 2.11-.45 12.84 12.84 0 0 0 2.81.7A2 2 0 0 1 22 16.92z"></path></svg>
                        <a href="tel:<?php echo htmlspecialchars($brand['phone']); ?>" style="color: inherit;"><?php echo htmlspecialchars($brand['phone']); ?></a>
                    </div>
                    <?php if(!empty($brand['whatsapp'])): ?>
                    <div class="footer-icon-text" style="margin-top: 0.5rem;">
                        <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="currentColor" style="color: var(--color-secondary);"><path d="M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.298-.347.446-.52.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207-.242-.579-.487-.5-.669-.51-.173-.008-.371-.01-.57-.01-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 1.871.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347m-5.421 7.403h-.004a9.87 9.87 0 01-5.031-1.378l-.361-.214-3.741.982.998-3.648-.235-.374a9.86 9.86 0 01-1.51-5.26c.001-5.45 4.436-9.884 9.888-9.884 2.64 0 5.122 1.03 6.988 2.898a9.825 9.825 0 012.893 6.994c-.003 5.45-4.437 9.884-9.885 9.884m8.413-18.297A11.815 11.815 0 0012.05 0C5.495 0 .16 5.335.157 11.892c0 2.096.547 4.142 1.588 5.945L.057 24l6.305-1.654a11.882 11.882 0 005.683 1.448h.005c6.554 0 11.89-5.335 11.893-11.893a11.821 11.821 0 00-3.48-8.413Z"/></svg>
                        <a href="https://wa.me/<?php echo htmlspecialchars($brand['whatsapp']); ?>" style="color: inherit;" target="_blank"><?php echo htmlspecialchars($brand['whatsapp']); ?></a>
                    </div>
                    <?php endif; ?>
                    <div class="footer-icon-text" style="margin-top: 0.5rem;">
                        <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="color: var(--color-secondary);"><path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z"></path><polyline points="22,6 12,13 2,6"></polyline></svg>
                        <a href="mailto:<?php echo htmlspecialchars($brand['email']); ?>" style="color: inherit;"><?php echo htmlspecialchars($brand['email']); ?></a>
                    </div>
                </div>

            </div>

            <div class="footer-bottom reveal delay-400">
                <p>&copy; <?php echo $brand['copyright_year']; ?> <?php echo htmlspecialchars($brand['name']); ?>. <?php echo htmlspecialchars($brand['copyright_text']); ?></p>
            </div>
        </div>
    </footer>

    <!-- Sticky WhatsApp Button -->
    <?php if(!empty($brand['whatsapp'])): ?>
    <a href="https://wa.me/<?php echo htmlspecialchars($brand['whatsapp']); ?>" class="sticky-whatsapp" target="_blank" aria-label="Chat with us on WhatsApp">
        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="30" height="30" fill="currentColor">
            <path d="M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.298-.347.446-.52.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207-.242-.579-.487-.5-.669-.51-.173-.008-.371-.01-.57-.01-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 1.871.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347m-5.421 7.403h-.004a9.87 9.87 0 01-5.031-1.378l-.361-.214-3.741.982.998-3.648-.235-.374a9.86 9.86 0 01-1.51-5.26c.001-5.45 4.436-9.884 9.888-9.884 2.64 0 5.122 1.03 6.988 2.898a9.825 9.825 0 012.893 6.994c-.003 5.45-4.437 9.884-9.885 9.884m8.413-18.297A11.815 11.815 0 0012.05 0C5.495 0 .16 5.335.157 11.892c0 2.096.547 4.142 1.588 5.945L.057 24l6.305-1.654a11.882 11.882 0 005.683 1.448h.005c6.554 0 11.89-5.335 11.893-11.893a11.821 11.821 0 00-3.48-8.413Z"/>
        </svg>
    </a>
    <?php endif; ?>

    <!-- JavaScript -->
    <script src="assets/js/main.js" defer></script>
</body>
</html>