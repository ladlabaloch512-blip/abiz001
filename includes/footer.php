    </main>

    <footer class="site-footer">
        <div class="container">
            <div class="footer-grid">

                <!-- Brand Col -->
                <div class="footer-col reveal">
                    <img src="<?php echo $brand['logo_path']; ?>" alt="<?php echo htmlspecialchars($brand['name']); ?> Logo" style="width: 150px; margin-bottom: 1.5rem; filter: brightness(0) invert(1);" loading="eager">
                    <p><?php echo htmlspecialchars($brand['slogan']); ?></p>
                    <div class="footer-social">
                        <?php if(!empty($brand['facebook'])): ?>
                            <a href="<?php echo $brand['facebook']; ?>" class="social-icon" aria-label="Facebook">F</a>
                        <?php endif; ?>
                        <?php if(!empty($brand['instagram'])): ?>
                            <a href="<?php echo $brand['instagram']; ?>" class="social-icon" aria-label="Instagram">I</a>
                        <?php endif; ?>
                        <?php if(!empty($brand['twitter'])): ?>
                            <a href="<?php echo $brand['twitter']; ?>" class="social-icon" aria-label="Twitter">T</a>
                        <?php endif; ?>
                        <?php if(!empty($brand['linkedin'])): ?>
                            <a href="<?php echo $brand['linkedin']; ?>" class="social-icon" aria-label="LinkedIn">L</a>
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
                    <p><strong>📍 Address:</strong><br>
                        <?php echo htmlspecialchars($brand['address_line_1']); ?><br>
                        <?php echo htmlspecialchars($brand['address_line_2']); ?>
                    </p>
                    <p style="margin-top: 1rem;">
                        <strong>📞 Phone:</strong><br>
                        <a href="tel:<?php echo htmlspecialchars($brand['phone']); ?>" style="color: inherit;"><?php echo htmlspecialchars($brand['phone']); ?></a>
                    </p>
                    <p style="margin-top: 1rem;">
                        <strong>✉️ Email:</strong><br>
                        <a href="mailto:<?php echo htmlspecialchars($brand['email']); ?>" style="color: inherit;"><?php echo htmlspecialchars($brand['email']); ?></a>
                    </p>
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