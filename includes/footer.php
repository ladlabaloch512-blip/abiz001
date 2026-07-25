    </main>

    <footer class="site-footer">
        <div class="container">
            <div class="footer-grid">

                <!-- Brand Col -->
                <div class="footer-col reveal">
                    <img src="<?php echo $brand['logo_path']; ?>" alt="<?php echo htmlspecialchars($brand['name']); ?> Logo" style="width: 150px; margin-bottom: 1.5rem; filter: brightness(0) invert(1);">
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

    <!-- JavaScript -->
    <script src="assets/js/main.js" defer></script>
</body>
</html>